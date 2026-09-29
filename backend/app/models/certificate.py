"""SQLAlchemy ORM model for submitted academic certificates and verification jobs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CertificateModel(Base):
    """Core certificate entity tracking document ingestion, lifecycle, and verification progress."""

    __tablename__ = "certificates"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False, default="image/png")

    job_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING", index=True
    )  # PENDING, PROCESSING, COMPLETED, FAILED
    job_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    preprocessed_image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("AppUserModel", backref="certificates", lazy="joined")
    institution = relationship("InstitutionModel", backref="certificates", lazy="joined")
