"""Pydantic V2 schemas for Verification History and Audit Logging."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class VerificationHistorySummary(BaseModel):
    """Clean summary representation of a past verification record for tabular/card views."""

    id: str = Field(..., description="Unique record identifier (UUID)")
    timestamp: str = Field(..., description="ISO 8601 formatted verification timestamp")
    original_filename: str = Field(
        ..., description="Original name of the uploaded certificate file"
    )
    document_type: str = Field(
        ..., description="Document category (e.g. VTU_MARKSCARD or ONLINE_COURSE_CERTIFICATE)"
    )
    student_name: str = Field(..., description="Candidate student or learner name")
    identifier: str = Field(..., description="Registration number, USN, or certificate identifier")
    issuer: str = Field(..., description="Issuing educational institution or platform")
    verdict: str = Field(
        ..., description="Holistic assessment: AUTHENTIC, SUSPICIOUS, or FRAUDULENT"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0"
    )
    qr_status: bool = Field(
        ..., description="Whether cryptographic/payload QR was detected and validated"
    )
    tampering_flags: List[str] = Field(
        default_factory=list, description="Array of detected anomalies, tampering or advisory flags"
    )
    remarks: str = Field("", description="Executive summary notes or primary rationale")


class VerificationHistoryDetail(VerificationHistorySummary):
    """Comprehensive forensic dossier snapshot for a historical verification."""

    full_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Comprehensive audit dossier including extracted fields, RAG validation, and QR payload",
    )


class VerificationHistoryPaginatedList(BaseModel):
    """Paginated collection of verification history summaries."""

    items: List[VerificationHistorySummary] = Field(default_factory=list)
    total: int = Field(..., description="Total number of matching verification records")
    page: int = Field(..., description="Current page number (1-indexed)")
    limit: int = Field(..., description="Number of records per page")
    total_pages: int = Field(..., description="Total number of pages available")


class VerificationHistoryClearResponse(BaseModel):
    """Response payload after clearing history records."""

    success: bool = True
    message: str
    deleted_count: int = 0
