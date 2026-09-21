"""Integration tests for JWT tokens, expiry, profiles, and rate limits (TC-USR-02, TC-USR-05)."""

from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import reset_rate_limits
from app.config import settings
from app.core.security import create_access_token
from app.models.user import AppUserModel


def _create_test_user(db: Session, email: str, role: str = "PUBLIC_USER") -> AppUserModel:
    from app.core.security import get_password_hash

    user = AppUserModel(
        email=email,
        full_name="Token Test User",
        password_hash=get_password_hash("CorrectPass123!"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_valid_login_returns_jwt_tokens(client: TestClient, db_session: Session):
    """Verify POST /api/v1/auth/login issues valid access and refresh tokens (TC-USR-02)."""
    user = _create_test_user(db_session, "login_test@example.com", "PUBLIC_USER")

    res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "CorrectPass123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert data["user"]["email"] == user.email


def test_invalid_login_credentials(client: TestClient, db_session: Session):
    """Verify wrong password returns HTTP 401 Unauthorized."""
    user = _create_test_user(db_session, "wrong_pass_user@example.com")

    res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_token_decoding_and_expiration(client: TestClient, db_session: Session):
    """Verify expired token returns HTTP 401 on protected endpoints (TC-USR-05)."""
    user = _create_test_user(db_session, "expired_user@example.com")

    # Generate token already expired 5 minutes ago
    expired_token = create_access_token(
        subject=user.id, role=user.role, expires_delta=timedelta(minutes=-5)
    )

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_user_profile_and_password_change(client: TestClient, db_session: Session):
    """Verify GET /api/v1/auth/me and POST /api/v1/auth/change-password lifecycle (FR-USR-03)."""
    user = _create_test_user(db_session, "profile_test@example.com")

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "CorrectPass123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch profile
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == user.email

    # 2. Change password
    chg_res = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "CorrectPass123!", "new_password": "NewSecretPass456!"},
        headers=headers,
    )
    assert chg_res.status_code == 200

    # 3. Old password should fail
    fail_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "CorrectPass123!"},
    )
    assert fail_res.status_code == 401

    # 4. New password should succeed
    succ_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "NewSecretPass456!"},
    )
    assert succ_res.status_code == 200


def test_login_rate_limiting(client: TestClient, db_session: Session):
    """Verify 5 failed login attempts trigger HTTP 429 Too Many Requests (CHIP USR-10)."""
    reset_rate_limits()
    try:
        # 5 failed login requests
        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                json={"email": "nonexistent@test.com", "password": "BadPassword123!"},
            )

        # 6th attempt must return 429
        blocked_res = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "BadPassword123!"},
        )
        assert blocked_res.status_code == 429
        assert "too many failed login attempts" in blocked_res.json()["detail"].lower()
    finally:
        reset_rate_limits()
