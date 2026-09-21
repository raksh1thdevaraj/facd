"""Firebase Admin SDK initialization and verification helpers."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials, firestore, storage

from app.config import settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None
_firestore_db = None


def initialize_firebase() -> Optional[firebase_admin.App]:
    """Initialize Firebase Admin SDK singleton with project credentials or ADC."""
    global _firebase_app, _firestore_db
    if _firebase_app is not None:
        return _firebase_app

    options = {
        "projectId": settings.FIREBASE_PROJECT_ID,
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
    }

    try:
        # Check if already initialized by default
        if firebase_admin._apps and "[DEFAULT]" in firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
            return _firebase_app

        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, options)
            logger.info(
                "Firebase Admin initialized with service account certificate from %s", cred_path
            )
        else:
            # Try Application Default Credentials (ADC) or project options
            try:
                cred = credentials.ApplicationDefault()
                _firebase_app = firebase_admin.initialize_app(cred, options)
                logger.info("Firebase Admin initialized with Application Default Credentials.")
            except Exception:
                # Local dev / test fallback without GCP credentials file
                _firebase_app = firebase_admin.initialize_app(options=options)
                logger.info("Firebase Admin initialized with project options: %s", options)

        return _firebase_app
    except Exception as exc:
        logger.warning("Firebase Admin initialization deferred/failed: %s", exc)
        return None


def get_firestore_client():
    """Retrieve Firestore client singleton if available."""
    global _firestore_db
    if _firestore_db is not None:
        return _firestore_db

    initialize_firebase()
    try:
        _firestore_db = firestore.client()
        return _firestore_db
    except Exception as exc:
        logger.warning("Firestore client could not be created: %s", exc)
        return None


def get_firebase_storage_bucket():
    """Retrieve default Firebase Cloud Storage bucket."""
    initialize_firebase()
    try:
        return storage.bucket(settings.FIREBASE_STORAGE_BUCKET)
    except Exception as exc:
        logger.warning("Firebase Storage bucket could not be resolved: %s", exc)
        return None


def verify_firebase_id_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a Firebase ID Token using Firebase Admin SDK.

    Returns the decoded token claims dictionary if valid, or None if invalid.
    """
    if not token or token.count(".") != 2:
        return None

    # Pre-check header algorithm without network overhead:
    # Firebase ID tokens are always RS256 signed.
    try:
        from jose import jwt as jose_jwt

        header = jose_jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            return None
    except Exception:
        return None

    app_instance = initialize_firebase()
    if not app_instance:
        return None

    try:
        decoded = auth.verify_id_token(token, check_revoked=False, clock_skew_seconds=10)
        return decoded
    except Exception as exc:
        logger.debug("Firebase token verification failed: %s", exc)
        return None
