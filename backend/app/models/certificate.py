"""SQLAlchemy ORM model for submitted academic certificates and verification jobs."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class CertificateModel(Base):
    """Core certificate entity tracking document ingestion, lifecycle, and verification progress."""

    __tablename__ = "certificates"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    institution_id = Column(
        String(36), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    original_filename = Column(String(256), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(64), nullable=False, default="image/png")

    job_status = Column(
        String(32), nullable=False, default="PENDING", index=True
    )  # PENDING, PROCESSING, COMPLETED, FAILED
    job_error = Column(Text, nullable=True)
    job_progress = Column(Integer, nullable=False, default=0)

    preprocessed_image_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("AppUserModel", backref="certificates", lazy="joined")
    institution = relationship("InstitutionModel", backref="certificates", lazy="joined")
