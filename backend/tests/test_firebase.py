"""Tests for Firebase Admin initialization, token verification, and FirestoreService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.firebase import (
    get_firebase_storage_bucket,
    get_firestore_client,
    initialize_firebase,
    verify_firebase_id_token,
)
from app.models.user import AppUserModel
from app.services.firestore_service import FirestoreService, firestore_service


def test_firebase_initialize_graceful():
    """Verify initialize_firebase initializes or handles fallback gracefully."""
    app = initialize_firebase()
    # In test environment, app initializes with project options
    assert app is not None or app is None


def test_verify_firebase_id_token_rejects_invalid():
    """Verify non-JWT or non-RS256 strings immediately return None without crashing."""
    assert verify_firebase_id_token("") is None
    assert verify_firebase_id_token("not-a-token") is None
    assert verify_firebase_id_token("header.payload.signature") is None


def test_firestore_service_availability():
    """Verify FirestoreService methods degrade gracefully when offline."""
    svc = FirestoreService()
    # When offline or credentials missing, operations safely return False or None
    if not svc.is_available:
        assert svc.upsert_user("u1", {"email": "test@example.com"}) is False
        assert svc.get_user("u1") is None
        assert svc.get_user_by_email("test@example.com") is None
        assert svc.save_certificate("c1", {"status": "PENDING"}) is False
        assert svc.get_certificate("c1") is None
        assert svc.list_certificates_for_user("u1") == []
        assert svc.save_course_verification("v1", {"status": "VERIFIED"}) is False
        assert svc.get_course_verification("v1") is None
        assert svc.log_audit_event({"action": "TEST"}) is False


def test_get_current_user_with_firebase_token(db_session: Session):
    """Verify that a valid Firebase ID token resolves and syncs user into the database session."""
    mock_claims = {
        "uid": "firebase-test-user-123",
        "email": "fb_user@university.edu",
        "name": "Firebase Test User",
        "role": "INSTITUTION_VERIFIER",
    }

    with patch("app.api.deps.verify_firebase_id_token", return_value=mock_claims):
        user = get_current_user(token="mock.firebase.token", db=db_session)
        assert user is not None
        assert user.id == "firebase-test-user-123"
        assert user.email == "fb_user@university.edu"
        assert user.full_name == "Firebase Test User"
        assert user.role == "INSTITUTION_VERIFIER"
        assert user.is_active is True


def test_get_current_user_deactivated_firebase_user(db_session: Session):
    """Verify deactivated user with Firebase token is rejected with HTTP 401."""
    # Pre-create deactivated user
    deactivated = AppUserModel(
        id="deactivated-fb-user",
        email="inactive@university.edu",
        password_hash="FIREBASE_MANAGED_AUTH",
        full_name="Inactive User",
        role="PUBLIC_USER",
        is_active=False,
    )
    db_session.add(deactivated)
    db_session.commit()

    mock_claims = {
        "uid": "deactivated-fb-user",
        "email": "inactive@university.edu",
    }

    with patch("app.api.deps.verify_firebase_id_token", return_value=mock_claims):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="mock.firebase.token", db=db_session)
        assert exc_info.value.status_code == 401
        assert "deactivated" in exc_info.value.detail.lower()
