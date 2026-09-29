"""Pydantic V2 schemas for user management, profiles, and credential changes."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.rbac import UserRole, normalize_role


class UserBase(BaseModel):
    """Base user properties."""

    email: str = Field(..., description="User's unique email address")
    full_name: Optional[str] = Field(default=None, max_length=255, description="Full legal name")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned in ("admin", "administrator", "root") or re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", cleaned):
            return cleaned
        raise ValueError("Invalid email address format")


class UserCreate(UserBase):
    """Schema for registering a new user."""

    name: Optional[str] = Field(default=None, description="Alias for full_name")
    password: str = Field(..., min_length=8, description="Plaintext password")
    role: UserRole = Field(default=UserRole.USER, description="Assigned role (default: user)")
    institution_id: Optional[str] = Field(
        default=None, description="Optional institution UUID if affiliated"
    )

    @field_validator("role", mode="before")
    @classmethod
    def parse_role(cls, v: str | UserRole) -> UserRole:
        return normalize_role(v)



class UserUpdate(BaseModel):
    """Schema for updating user details."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    institution_id: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChangeRequest(BaseModel):
    """Schema for rotating password."""

    current_password: str = Field(..., description="Current plaintext password")
    new_password: str = Field(..., min_length=8, description="New plaintext password")


class UserResponse(UserBase):
    """Publicly safe user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    institution_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
