"""Role-Based Access Control (RBAC) hierarchy and permissions."""

from __future__ import annotations

from enum import Enum
from typing import Set


class UserRole(str, Enum):
    """Platform authorization roles: strictly user and admin."""

    ADMIN = "admin"
    USER = "user"


_ROLE_ALIASES = {
    "admin": UserRole.ADMIN,
    "administrator": UserRole.ADMIN,
    "user": UserRole.USER,
    "public_user": UserRole.USER,
    "public": UserRole.USER,
    "guest": UserRole.USER,
    "student": UserRole.USER,
    "auditor": UserRole.USER,
    "institution_verifier": UserRole.USER,
    "verifier": UserRole.USER,
    "registrar": UserRole.USER,
}


def normalize_role(role: str | UserRole) -> UserRole:
    """Normalize arbitrary string or enum to canonical UserRole (admin vs user)."""
    if isinstance(role, UserRole):
        return role
    cleaned = role.strip().lower()
    return _ROLE_ALIASES.get(cleaned, UserRole.USER)


def is_role_authorized(current_role: str | UserRole, allowed_roles: Set[UserRole]) -> bool:
    """Check if current role is within allowed roles (Admin always inherits full access)."""
    norm = normalize_role(current_role)
    if norm == UserRole.ADMIN:
        return True
    return norm in allowed_roles

