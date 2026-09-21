"""Integration tests for RBAC enforcement and token revocation (TC-USR-03, TC-USR-04, TC-USR-05)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.user import AppUserModel


def _create_user(db: Session, email: str, role: str) -> AppUserModel:
    user = AppUserModel(
        email=email,
        full_name=f"User {role}",
        password_hash=get_password_hash("Pass12345!"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_admin_endpoint_rejects_public_user(client: TestClient, db_session: Session):
    """Verify Public user accessing /api/v1/audit-logs returns HTTP 403 Forbidden (TC-USR-03)."""
    public_user = _create_user(db_session, "public_rbac@test.com", "PUBLIC_USER")
    token = create_access_token(subject=public_user.id, role=public_user.role)

    res = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "insufficient permissions" in res.json()["detail"].lower()


def test_admin_endpoint_permits_admin(client: TestClient, db_session: Session):
    """Verify Admin user accessing /api/v1/audit-logs returns HTTP 200 OK (TC-USR-03)."""
    admin_user = _create_user(db_session, "admin_rbac@test.com", "ADMIN")
    token = create_access_token(subject=admin_user.id, role=admin_user.role)

    res = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "items" in res.json()


def test_protected_endpoint_rejects_unauthenticated(client: TestClient):
    """Verify request without Bearer token returns HTTP 401 Unauthorized (TC-USR-05)."""
    res = client.get("/api/v1/audit-logs")
    assert res.status_code == 401
    assert "missing" in res.json()["detail"].lower()


def test_token_refresh_flow(client: TestClient, db_session: Session):
    """Verify refresh token exchanges for fresh token pair and enforces rotation (TC-USR-04)."""
    user = _create_user(db_session, "refresh_flow@test.com", "INSTITUTION_VERIFIER")

    # 1. Login to get token pair
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Pass12345!"},
    )
    assert login_res.status_code == 200
    initial_refresh = login_res.json()["refresh_token"]

    # 2. Exchange refresh token
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert ref_res.status_code == 200
    new_data = ref_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["refresh_token"] != initial_refresh

    # 3. Old refresh token should now be rejected (strict rotation)
    stale_res = client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
    assert stale_res.status_code == 401


def test_token_logout_revocation(client: TestClient, db_session: Session):
    """Verify logout revokes the active access token (FR-USR-04)."""
    user = _create_user(db_session, "logout_user@test.com", "PUBLIC_USER")

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "Pass12345!"},
    )
    access_tok = login_res.json()["access_token"]
    refresh_tok = login_res.json()["refresh_token"]
    headers = {"Authorization": f"Bearer {access_tok}"}

    # Verify token works before logout
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_tok},
        headers=headers,
    )
    assert logout_res.status_code == 200

    # Token must now be rejected
    post_logout_res = client.get("/api/v1/auth/me", headers=headers)
    assert post_logout_res.status_code == 401
