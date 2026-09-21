"""Cryptographic security utilities: bcrypt password hashing and JWT issuance."""

from __future__ import annotations

import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set, Tuple

import bcrypt
from jose import jwt

from app.config import settings

# Thread-safe in-memory revocation blocklist for refresh token JTIs
_REVOCATION_LOCK = threading.Lock()
_REVOKED_JTIS: Set[str] = set()


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt with 12 work factor rounds."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash in constant time."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """Enforce password complexity requirements (NFR-02).

    Rules:
      - Minimum 8 characters.
      - At least 1 uppercase letter.
      - At least 1 lowercase letter.
      - At least 1 digit.
      - At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        return False, "Password must contain at least one special character."
    return True, None


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed, stateless JWT access token (default expiry: 15 minutes)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": str(role).upper(),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token with unique JTI (default expiry: 7 days)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate signature and expiry of a JWT token.

    Raises:
        JWTError: If signature verification or claims validation fails.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def revoke_token(jti_or_token: str) -> None:
    """Add a token or its JTI to the revocation blocklist."""
    jti = jti_or_token
    try:
        claims = decode_token(jti_or_token)
        jti = claims.get("jti", jti_or_token)
    except Exception:
        pass

    with _REVOCATION_LOCK:
        _REVOKED_JTIS.add(jti)


def is_token_revoked(jti_or_token: str) -> bool:
    """Check whether a token or its JTI has been revoked."""
    jti = jti_or_token
    try:
        claims = decode_token(jti_or_token)
        jti = claims.get("jti", jti_or_token)
    except Exception:
        pass

    with _REVOCATION_LOCK:
        return jti in _REVOKED_JTIS
