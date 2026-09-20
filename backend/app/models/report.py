"""SQLAlchemy ORM model for final verification decisions and reports."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String

from app.database import Base


class VerificationReportModel(Base):
    """SQLAlchemy model persisting final multimodal verification decisions."""

    __tablename__ = "verification_reports"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(String(36), index=True, nullable=False)
    overall_score = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    verdict = Column(String(32), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)
    sub_scores_json = Column(JSON, nullable=True)
    veto_applied = Column(Boolean, default=False, nullable=False)
    veto_reason = Column(String(512), nullable=True)
    contributing_factors_json = Column(JSON, nullable=True)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    pdf_path = Column(String(512), nullable=True)
    json_path = Column(String(512), nullable=True)
    qr_path = Column(String(512), nullable=True)
    hmac_signature = Column(String(128), nullable=True)
    report_data_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
