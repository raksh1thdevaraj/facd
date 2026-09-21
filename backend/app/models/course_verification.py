"""SQLAlchemy ORM model for Course Certificate Authenticity Verifications."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CourseCertificateVerificationModel(Base):
    """Database model persisting course certificate verifications, QR findings, and forensics."""

    __tablename__ = "course_certificate_verifications"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Ingested file properties
    uploaded_file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    original_filename = Column(String(256), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(64), nullable=False, default="application/pdf")
    job_status = Column(
        String(32), nullable=False, default="PENDING", index=True
    )  # PENDING, PROCESSING, COMPLETED, FAILED

    # Extracted metadata & QR data
    extracted_fields_json = Column(JSON, nullable=True)
    qr_data_json = Column(JSON, nullable=True)
    verification_url = Column(String(512), nullable=True)
    issuer = Column(String(256), nullable=True)

    # Online record & comparison
    online_verification_data_json = Column(JSON, nullable=True)
    field_comparison_json = Column(JSON, nullable=True)

    # Forensic & visual manipulation signals
    tampering_analysis_json = Column(JSON, nullable=True)
    seal_signature_json = Column(JSON, nullable=True)
    ml_prediction_json = Column(JSON, nullable=True)

    # Final verdict & scores
    authenticity_score = Column(Float, nullable=False, default=0.0)
    fraud_risk_score = Column(Float, nullable=False, default=0.0)
    final_status = Column(
        String(32), nullable=False, default="UNVERIFIED", index=True
    )  # VERIFIED, SUSPICIOUS, FRAUDULENT, UNVERIFIED, VERIFICATION_UNAVAILABLE
    evidence_summary_json = Column(JSON, nullable=True)

    # Generated report paths
    report_pdf_path = Column(String(512), nullable=True)
    report_json_path = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationship to user
    user = relationship("AppUserModel", backref="course_verifications", lazy="joined")


# Convenient alias
CourseCertificateVerification = CourseCertificateVerificationModel
