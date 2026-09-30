"""SQLAlchemy ORM model for Verification History and Audit Logging."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationHistoryModel(Base):
    """Database model persisting verification audit log records across all certificate types."""

    __tablename__ = "verification_history"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False, index=True)
    timestamp_iso: Mapped[str] = mapped_column(String(64), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="VTU_MARKSCARD", index=True
    )  # VTU_MARKSCARD | ONLINE_COURSE_CERTIFICATE
    student_name: Mapped[str] = mapped_column(String(256), nullable=False, default="Not Detected", index=True)
    identifier: Mapped[str] = mapped_column(String(128), nullable=False, default="Not Detected", index=True)
    issuer: Mapped[str] = mapped_column(String(256), nullable=False, default="Not Detected", index=True)
    verdict: Mapped[str] = mapped_column(
        String(32), nullable=False, default="SUSPICIOUS", index=True
    )  # AUTHENTIC | SUSPICIOUS | FRAUDULENT
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    qr_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tampering_flags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # List[str]
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Detailed forensic snapshot

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return summary dictionary for tabular history views."""
        ts = self.timestamp_iso or (self.timestamp.isoformat() if self.timestamp is not None else "")
        score = float(getattr(self, "confidence_score", 0.0) or 0.0)
        return {
            "id": self.id,
            "timestamp": ts,
            "original_filename": self.original_filename,
            "document_type": self.document_type,
            "student_name": self.student_name,
            "identifier": self.identifier,
            "issuer": self.issuer,
            "verdict": self.verdict,
            "confidence_score": round(score, 4),
            "qr_status": bool(self.qr_status),
            "tampering_flags": self.tampering_flags or [],
            "remarks": self.remarks or "",
        }

    def to_detail_dict(self) -> Dict[str, Any]:
        """Return comprehensive breakdown dictionary including forensics and RAG audit."""
        summary = self.to_summary_dict()
        summary["full_details"] = self.full_details or {}
        return summary
