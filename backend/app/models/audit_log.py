"""SQLAlchemy ORM model for immutable compliance audit logging."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLogModel(Base):
    """Immutable audit trail recording all security, verification, and administrative actions."""

    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    certificate_id = Column(
        String(36), ForeignKey("certificates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # Supports IPv4 and IPv6
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
