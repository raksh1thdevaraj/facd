"""Pydantic V2 schemas for authentication requests, tokens, and payloads."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """JSON credentials payload for user login."""

    email: str = Field(..., description="Registered user email")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    """Payload to exchange refresh token for a fresh token pair."""

    refresh_token: str = Field(..., description="Valid JWT refresh token")


class TokenResponse(BaseModel):
    """Standard authentication session response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration window in seconds")
    user: UserResponse


class TokenData(BaseModel):
    """Extracted claims from validated JWT payload."""

    user_id: Optional[str] = None
    role: Optional[str] = None
    token_type: Optional[str] = None
