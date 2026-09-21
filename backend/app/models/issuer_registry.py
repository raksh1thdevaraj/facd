"""SQLAlchemy ORM model for recognized credential issuers and domain verification registries."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IssuerRegistryModel(Base):
    """Registry of recognized educational and training credential issuers."""

    __tablename__ = "issuer_registry"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issuer_name = Column(String(256), nullable=False, unique=True, index=True)
    official_domain = Column(String(256), nullable=False)
    verification_domain = Column(String(256), nullable=False, index=True)
    verification_pattern = Column(String(512), nullable=True)
    certificate_id_pattern = Column(String(256), nullable=True)
    trusted_status = Column(
        String(32), default="TRUSTED", nullable=False, index=True
    )  # TRUSTED, UNKNOWN, SUSPICIOUS, MALICIOUS
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


# Convenient alias
IssuerRegistry = IssuerRegistryModel
