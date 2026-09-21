"""Pydantic V2 schemas for certificate upload, status polling, and verification management."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.decision import VerificationVerdict


class CertificateUploadResponse(BaseModel):
    """Initial response returned upon certificate document upload."""

    certificate_id: str = Field(..., description="Unique UUID assigned to uploaded certificate")
    status: str = Field(..., description="Pipeline job status: PENDING, PROCESSING, etc.")
    poll_url: str = Field(..., description="URL to poll execution progress and job state")
    filename: str = Field(..., description="Original filename uploaded")
    file_hash: str = Field(..., description="SHA-256 fingerprint")
    created_at: datetime = Field(..., description="Upload timestamp")


class CertificateStatusResponse(BaseModel):
    """Lightweight polling response reflecting real-time pipeline execution progress."""

    id: str = Field(..., description="Certificate UUID")
    status: str = Field(..., description="PENDING, PROCESSING, COMPLETED, or FAILED")
    progress: int = Field(..., ge=0, le=100, description="Percentage of pipeline completed (0-100)")
    error: Optional[str] = Field(default=None, description="Detailed error message if failed")
    report_id: Optional[str] = Field(default=None, description="Report ID if completed")


class CertificateListItem(BaseModel):
    """Summary item in paginated certificate history listings."""

    id: str
    filename: str
    file_hash: str
    file_size: int
    status: str
    progress: int
    created_at: datetime
    verdict: Optional[VerificationVerdict] = None
    authenticity_score: Optional[float] = None


class CertificatePaginatedList(BaseModel):
    """Paginated collection of certificates for verifier dashboards."""

    items: List[CertificateListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class CertificateDetailResponse(BaseModel):
    """Full detail view of an individual assessed certificate."""

    id: str
    filename: str
    file_hash: str
    file_size: int
    mime_type: str
    status: str
    progress: int
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    preprocessed_image_path: Optional[str] = None
    ocr_fields: List[Dict[str, Any]] = Field(default_factory=list)
    forensic_findings: List[Dict[str, Any]] = Field(default_factory=list)
    report_id: Optional[str] = None
    verdict: Optional[VerificationVerdict] = None
    authenticity_score: Optional[float] = None
