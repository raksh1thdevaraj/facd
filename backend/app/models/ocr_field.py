"""SQLAlchemy ORM model for individual academic fields extracted via OCR."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String

from app.database import Base


class OCRFieldModel(Base):
    """Extracted text field record from OCR stage (name, roll no, degree, grade, etc.)."""

    __tablename__ = "ocr_fields"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(
        String(36), ForeignKey("certificates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name = Column(String(64), nullable=False)  # student_name, roll_number, etc.
    field_value = Column(String(512), nullable=True)
    confidence_score = Column(Float, nullable=False, default=0.0)
    bounding_box = Column(JSON, nullable=True)  # xmin, ymin, xmax, ymax
    is_flagged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
