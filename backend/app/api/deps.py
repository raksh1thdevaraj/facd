"""FastAPI authentication and role-based authorization dependencies."""

from __future__ import annotations

from typing import Optional, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.firebase import verify_firebase_id_token
from app.core.rbac import UserRole, is_role_authorized, normalize_role
from app.core.security import decode_token, is_token_revoked
from app.database import get_db
from app.models.user import AppUserModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AppUserModel:
    """Validate Bearer access token and resolve active user from database."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Try Firebase Authentication ID token if enabled
    if settings.USE_FIREBASE_AUTH:
        fb_claims = verify_firebase_id_token(token)
        if fb_claims:
            uid = fb_claims.get("uid") or fb_claims.get("sub")
            email = fb_claims.get("email") or f"{uid}@example.com"
            user = (
                db.query(AppUserModel)
                .filter((AppUserModel.id == uid) | (AppUserModel.email == email))
                .first()
            )
            if not user and uid:
                # Synchronize Firebase user identity into local DB session
                role = fb_claims.get("role", "public_user")
                full_name = fb_claims.get("name") or email.split("@")[0]
                user = AppUserModel(
                    id=uid,
                    email=email,
                    password_hash="FIREBASE_MANAGED_AUTH",
                    full_name=full_name,
                    role=str(role),
                    is_active=True,
                )
                db.add(user)
                try:
                    db.commit()
                    db.refresh(user)
                except Exception:
                    db.rollback()
                    user = (
                        db.query(AppUserModel)
                        .filter((AppUserModel.id == uid) | (AppUserModel.email == email))
                        .first()
                    )

            if user:
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is deactivated.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return user

    # 2. Fallback to local signed JWT token
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type for endpoint authentication.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(AppUserModel).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[AppUserModel]:
    """Resolve user if a valid token is provided; otherwise returns None without raising."""
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except Exception:
        return None


def require_role(*roles: UserRole | str):
    """Enforce that the authenticated user possesses one of the specified roles."""
    allowed_set: Set[UserRole] = {normalize_role(r) for r in roles}

    def role_dependency(current_user: AppUserModel = Depends(get_current_user)) -> AppUserModel:
        if not is_role_authorized(str(current_user.role), allowed_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation.",
            )
        return current_user

    return role_dependency


# Convenience RBAC dependency shortcuts
require_admin = require_role(UserRole.ADMIN)
require_verifier = require_role(UserRole.ADMIN, UserRole.USER)
require_user = require_role(UserRole.ADMIN, UserRole.USER)
