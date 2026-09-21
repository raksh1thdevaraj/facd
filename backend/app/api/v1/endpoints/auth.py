"""FastAPI router for user authentication, registration, token refresh, and profile management."""

from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    decode_token,
    is_token_revoked,
    revoke_token,
)
from app.database import get_db
from app.models.user import AppUserModel
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.schemas.user import PasswordChangeRequest, UserCreate, UserResponse
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])

# In-memory IP-based brute-force tracker: tracks timestamps of failed attempts
_RATE_LIMIT_LOCK = threading.Lock()
_FAILED_ATTEMPTS: Dict[str, List[float]] = collections.defaultdict(list)
_MAX_FAILED_ATTEMPTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 60.0


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    with _RATE_LIMIT_LOCK:
        recent = [t for t in _FAILED_ATTEMPTS[ip] if now - t < _RATE_LIMIT_WINDOW_SECONDS]
        _FAILED_ATTEMPTS[ip] = recent
        if len(recent) >= _MAX_FAILED_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again after 60 seconds.",
            )


def _record_failed_attempt(ip: str) -> None:
    with _RATE_LIMIT_LOCK:
        _FAILED_ATTEMPTS[ip].append(time.time())


def _clear_failed_attempts(ip: str) -> None:
    with _RATE_LIMIT_LOCK:
        _FAILED_ATTEMPTS.pop(ip, None)


def reset_rate_limits() -> None:
    """Clear all recorded failed attempts (primarily for testing and administrative resets)."""
    with _RATE_LIMIT_LOCK:
        _FAILED_ATTEMPTS.clear()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new platform user",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new user account with bcrypt password hashing (FR-USR-01)."""
    user = AuthService.register_user(db=db, user_in=user_in)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate credentials and issue JWT access and refresh tokens",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate via JSON payload or form credentials with rate-limiting protection (NFR-02)."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    _check_rate_limit(client_ip)

    # Parse JSON or form body
    email: Optional[str] = None
    password: Optional[str] = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email") or body.get("username")
        password = body.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both email/username and password are required.",
        )

    user = AuthService.authenticate_user(db=db, email=str(email), password=str(password))
    if not user:
        _record_failed_attempt(client_ip)
        AuditService.log_action(
            db=db,
            action="USER_LOGIN_FAILED",
            ip_address=client_ip,
            details={"email": str(email)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _clear_failed_attempts(client_ip)
    AuditService.log_action(
        db=db,
        action="USER_LOGIN_SUCCESS",
        user_id=user.id,
        ip_address=client_ip,
        details={"email": user.email, "role": user.role},
    )

    return AuthService.create_user_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange valid refresh token for rotated token pair",
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Validate refresh token, check revocation, and issue fresh access/refresh pair (FR-USR-04)."""
    token_str = payload.refresh_token
    try:
        claims = decode_token(token_str)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if claims.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = claims.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims.get("sub")
    user = db.query(AppUserModel).filter_by(id=user_id).first() if user_id else None
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Revoke used refresh token for strict rotation
    if jti:
        revoke_token(jti)

    # Issue new rotated pair
    return AuthService.create_user_tokens(user)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke active tokens and terminate session",
)
def logout(
    request: Request,
    payload: Optional[RefreshTokenRequest] = None,
    current_user: AppUserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Revoke provided refresh token and active Bearer access token."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        access_tok = auth_header.replace("Bearer ", "").strip()
        revoke_token(access_tok)

    if payload and payload.refresh_token:
        revoke_token(payload.refresh_token)

    AuditService.log_action(
        db=db,
        action="USER_LOGOUT",
        user_id=current_user.id,
    )
    return {"message": "Successfully logged out and revoked session tokens."}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get profile details of the authenticated user",
)
def get_current_user_profile(
    current_user: AppUserModel = Depends(get_current_user),
) -> UserResponse:
    """Return identity and roles for the active session (FR-USR-03)."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Update credentials for authenticated user",
)
def change_password(
    payload: PasswordChangeRequest,
    current_user: AppUserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Verify current password and update salted bcrypt hash."""
    AuthService.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return {"message": "Password changed successfully."}
