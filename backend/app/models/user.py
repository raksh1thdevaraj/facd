"""SQLAlchemy ORM model for application users and access management."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


class AppUserModel(Base):
    """User account entity representing registrars, admissions officers, and auditors."""

    __tablename__ = "app_users"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(
        String(36), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(32), default="auditor", nullable=False)  # admin, registrar, auditor
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    institution = relationship("InstitutionModel", backref="users", lazy="joined")
