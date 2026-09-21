"""Integration tests for user registration, bcrypt hashing, and duplicate checks (TC-USR-01)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, validate_password_strength, verify_password
from app.models.user import AppUserModel


def test_password_hashing_and_verification():
    """Verify salted bcrypt cost factor, verification, and complexity rules (TC-USR-01)."""
    raw_password = "SecurePassword123!"
    h1 = get_password_hash(raw_password)
    h2 = get_password_hash(raw_password)

    # Salted hashes must differ
    assert h1 != h2
    assert h1.startswith("$2b$12$")

    # Constant time verification
    assert verify_password(raw_password, h1) is True
    assert verify_password(raw_password, h2) is True
    assert verify_password("WrongPassword123!", h1) is False

    # Password complexity checks
    valid, _ = validate_password_strength("ValidPass123!")
    assert valid is True
    short_valid, _ = validate_password_strength("Short1!")
    assert short_valid is False
    no_num, _ = validate_password_strength("NoNumberPass!")
    assert no_num is False
    no_special, _ = validate_password_strength("NoSpecialPass123")
    assert no_special is False


def test_user_registration_and_duplicate_rejection(client: TestClient, db_session: Session):
    """Verify POST /register creates user and rejects duplicate email with 409 (TC-USR-01)."""
    user_data = {
        "email": "new_student@university.edu",
        "password": "Password123!",
        "full_name": "New Student",
        "role": "PUBLIC_USER",
    }

    # 1. Register successfully
    res = client.post("/api/v1/auth/register", json=user_data)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "new_student@university.edu"
    assert data["full_name"] == "New Student"
    assert data["role"] == "PUBLIC_USER"
    assert "id" in data
    assert "password" not in data

    # Verify user in database has hashed password
    db_user = db_session.query(AppUserModel).filter_by(email="new_student@university.edu").first()
    assert db_user is not None
    assert db_user.password_hash != "Password123!"
    assert verify_password("Password123!", db_user.password_hash)

    # 2. Duplicate registration attempt should return 409 Conflict
    dup_res = client.post("/api/v1/auth/register", json=user_data)
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"].lower()


def test_registration_with_nonexistent_institution(client: TestClient):
    """Verify registering with an invalid institution ID fails with 404."""
    user_data = {
        "email": "invalid_inst_user@example.com",
        "password": "Password123!",
        "full_name": "Invalid Inst User",
        "role": "INSTITUTION_VERIFIER",
        "institution_id": "nonexistent-institution-uuid-000",
    }

    res = client.post("/api/v1/auth/register", json=user_data)
    assert res.status_code == 404
    assert "institution was not found" in res.json()["detail"].lower()
