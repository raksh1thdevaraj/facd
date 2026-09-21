"""Role-Based Access Control (RBAC) hierarchy and permissions."""

from __future__ import annotations

from enum import Enum
from typing import Set


class UserRole(str, Enum):
    """Platform authorization roles."""

    ADMIN = "ADMIN"
    INSTITUTION_VERIFIER = "INSTITUTION_VERIFIER"
    PUBLIC_USER = "PUBLIC_USER"


_ROLE_ALIASES = {
    "admin": UserRole.ADMIN,
    "administrator": UserRole.ADMIN,
    "institution_verifier": UserRole.INSTITUTION_VERIFIER,
    "verifier": UserRole.INSTITUTION_VERIFIER,
    "registrar": UserRole.INSTITUTION_VERIFIER,
    "auditor": UserRole.INSTITUTION_VERIFIER,
    "public_user": UserRole.PUBLIC_USER,
    "public": UserRole.PUBLIC_USER,
    "guest": UserRole.PUBLIC_USER,
}


def normalize_role(role: str | UserRole) -> UserRole:
    """Normalize arbitrary string or enum to canonical UserRole."""
    if isinstance(role, UserRole):
        return role
    cleaned = str(role).strip().lower()
    return _ROLE_ALIASES.get(cleaned, UserRole.PUBLIC_USER)


def is_role_authorized(current_role: str | UserRole, allowed_roles: Set[UserRole]) -> bool:
    """Check if current role is within allowed roles (Admin always inherits full access)."""
    norm = normalize_role(current_role)
    if norm == UserRole.ADMIN:
        return True
    return norm in allowed_roles
