"""Authentication service managing user onboarding, credentials verification, and token issuance."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.rbac import normalize_role
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from app.models.template import InstitutionModel
from app.models.user import AppUserModel
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class AuthService:
    """Business logic for authentication, password verification, and credential lifecycle."""

    @classmethod
    def register_user(cls, db: Session, user_in: UserCreate) -> AppUserModel:
        """Register a new user account with bcrypt salted hash (FR-USR-01).

        Raises:
            HTTPException: 400 if password does not meet complexity rules.
            HTTPException: 409 if email is already registered.
            HTTPException: 404 if referenced institution does not exist.
        """
        # 1. Enforce password complexity
        valid, msg = validate_password_strength(user_in.password)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg,
            )

        # 2. Check for duplicate email
        normalized_email = user_in.email.strip().lower()
        existing = db.query(AppUserModel).filter_by(email=normalized_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        # 3. Check institution reference if supplied
        if user_in.institution_id:
            inst = db.query(InstitutionModel).filter_by(id=user_in.institution_id).first()
            if not inst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Referenced institution was not found.",
                )

        # 4. Hash password and persist user
        pwd_hash = get_password_hash(user_in.password)
        user_role = normalize_role(user_in.role).value
        resolved_name = (user_in.name or user_in.full_name or normalized_email.split("@")[0]).strip()

        user = AppUserModel(
            email=normalized_email,
            full_name=resolved_name,
            password_hash=pwd_hash,
            role=user_role,
            institution_id=user_in.institution_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 5. Record compliance audit entry
        AuditService.log_action(
            db=db,
            action="USER_REGISTERED",
            user_id=str(user.id),
            details={"email": str(user.email), "role": str(user.role)},
        )
        logger.info("Successfully registered user %s with role %s", user.email, user.role)
        return user

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> Optional[AppUserModel]:
        """Authenticate user credentials using constant-time hash comparison."""
        normalized_email = email.strip().lower()
        is_admin_alias = normalized_email in ("admin", "admin@certishield.ai", "administrator")
        query_filter = (
            (AppUserModel.email == normalized_email)
            | (AppUserModel.full_name == email.strip())
        )
        if is_admin_alias:
            query_filter = query_filter | (AppUserModel.role == "admin")

        user = db.query(AppUserModel).filter(query_filter).first()
        if not user or not user.is_active:
            return None

        if not verify_password(password, str(user.password_hash)):
            return None

        return user

    @classmethod
    def create_user_tokens(cls, user: AppUserModel) -> TokenResponse:
        """Generate JWT access and refresh token pair for authenticated user."""
        access_token = create_access_token(subject=str(user.id), role=str(user.role))
        refresh_token = create_refresh_token(subject=str(user.id))
        user_resp = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_resp,
        )

    @classmethod
    def change_password(
        cls, db: Session, user: AppUserModel, current_password: str, new_password: str
    ) -> bool:
        """Validate current credentials and update to new salted hash."""
        if not verify_password(current_password, str(user.password_hash)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        valid, msg = validate_password_strength(new_password)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg,
            )

        setattr(user, "password_hash", get_password_hash(new_password))
        db.commit()
        db.refresh(user)

        AuditService.log_action(
            db=db,
            action="USER_PASSWORD_CHANGED",
            user_id=str(user.id),
        )
        return True
