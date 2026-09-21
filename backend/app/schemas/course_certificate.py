"""Pydantic V2 schemas for Course Certificate Authenticity Verification."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class NormalizedCertificateData(BaseModel):
    """Normalized structured data extracted from course certificate text and tokens."""

    candidate_name: Optional[str] = None
    course_name: Optional[str] = None
    certificate_id: Optional[str] = None
    credential_id: Optional[str] = None
    registration_id: Optional[str] = None
    issuer: Optional[str] = None
    institution: Optional[str] = None
    organization: Optional[str] = None
    issue_date: Optional[str] = None
    completion_date: Optional[str] = None
    expiry_date: Optional[str] = None
    grade: Optional[str] = None
    score: Optional[str] = None
    duration: Optional[str] = None
    instructor: Optional[str] = None
    signatory: Optional[str] = None
    verification_url: Optional[str] = None
    qr_content: Optional[str] = None
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class QRCodeData(BaseModel):
    """Extracted and decoded QR code payload."""

    qr_detected: bool = False
    qr_decoded: bool = False
    qr_content: Optional[str] = None
    payload: Optional[str] = None
    qr_url: Optional[str] = None
    bounding_box: Optional[List[int]] = None
    points: Optional[List[List[float]]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    error_message: Optional[str] = None


class URLVerificationData(BaseModel):
    """Results from URL syntax validation and issuer domain verification."""

    url: Optional[str] = None
    is_valid_url: bool = False
    is_valid_syntax: bool = False
    is_https: bool = False
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    issuer_name: Optional[str] = None
    resolved_issuer: Optional[str] = None
    trust_level: str = "UNKNOWN"  # TRUSTED, UNKNOWN, SUSPICIOUS, MALICIOUS
    risk_level: str = "SAFE"
    trust_score: float = 0.0
    domain_match: bool = False
    is_known_issuer: bool = False
    page_accessible: bool = False
    http_status: Optional[int] = None
    redirect_count: int = 0
    final_destination_url: Optional[str] = None
    remarks: Optional[str] = None
    error_message: Optional[str] = None


class OnlineVerificationRecord(BaseModel):
    """Scraped or queried online verification record from issuer website."""

    candidate_name: Optional[str] = None
    course_name: Optional[str] = None
    certificate_id: Optional[str] = None
    issue_date: Optional[str] = None
    issuer: Optional[str] = None
    badge_title: Optional[str] = None
    raw_metadata: Optional[dict[str, Any]] = None


class FieldComparisonResult(BaseModel):
    """Cross-modal field-by-field comparison between certificate and online record."""

    name_match_score: float = 0.0
    course_match_score: float = 0.0
    id_match_score: float = 0.0
    date_match_score: float = 0.0
    issuer_match_score: float = 0.0

    name_match: bool = False
    course_match: bool = False
    id_match: bool = False
    date_match: bool = False
    issuer_match: bool = False

    copied_qr_detected: bool = False
    overall_match_ratio: float = 0.0
    details: List[str] = Field(default_factory=list)


class TamperingAnalysisResult(BaseModel):
    """Document tampering and pixel-level forensic detection results."""

    tampering_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    tampering_regions: List[List[int]] = Field(default_factory=list)
    tampering_type: str = "none"  # none, text_splicing, copy_move, font_anomaly, noise_variance
    model_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    ela_anomaly_score: float = 0.0
    copy_move_score: float = 0.0
    noise_anomaly_score: float = 0.0
    heatmap_relative_path: Optional[str] = None


class SealSignatureResult(BaseModel):
    """Presence and integrity analysis for signatures and institutional seals."""

    signature_detected: bool = False
    signature_score: float = Field(default=0.0, ge=0.0, le=1.0)
    seal_detected: bool = False
    seal_score: float = Field(default=0.0, ge=0.0, le=1.0)
    details: List[str] = Field(default_factory=list)


class ScoreComponentBreakdown(BaseModel):
    """Explainable weighted sub-scores contributing to final authenticity score."""

    online_issuer_score: float = Field(default=0.0, ge=0.0, le=100.0)  # 25%
    field_matching_score: float = Field(default=0.0, ge=0.0, le=100.0)  # 25%
    document_integrity_score: float = Field(default=0.0, ge=0.0, le=100.0)  # 20%
    qr_verification_score: float = Field(default=0.0, ge=0.0, le=100.0)  # 15%
    issuer_domain_trust_score: float = Field(default=0.0, ge=0.0, le=100.0)  # 10%
    signature_seal_score: float = Field(default=0.0, ge=0.0, le=100.0)  # 5%


class CourseCertificateReport(BaseModel):
    """Complete verification report and decision payload."""

    verification_id: str
    uploaded_filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Core Decisions
    final_status: str  # VERIFIED, SUSPICIOUS, FRAUDULENT, UNVERIFIED, VERIFICATION_UNAVAILABLE
    authenticity_score: float = Field(default=0.0, ge=0.0, le=100.0)
    fraud_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    verdict_badge_color: str  # GREEN, YELLOW, RED, GRAY

    # Evidence & Explanations
    evidence_points: List[str] = Field(default_factory=list)
    component_breakdown: ScoreComponentBreakdown = Field(default_factory=ScoreComponentBreakdown)

    # Detailed Subsystems
    extracted_certificate_data: NormalizedCertificateData = Field(
        default_factory=NormalizedCertificateData
    )
    qr_data: QRCodeData = Field(default_factory=QRCodeData)
    url_verification: URLVerificationData = Field(default_factory=URLVerificationData)
    online_record: Optional[OnlineVerificationRecord] = None
    field_comparison: FieldComparisonResult = Field(default_factory=FieldComparisonResult)
    tampering_analysis: TamperingAnalysisResult = Field(default_factory=TamperingAnalysisResult)
    seal_signature: SealSignatureResult = Field(default_factory=SealSignatureResult)

    pdf_report_url: Optional[str] = None


class IssuerCreateRequest(BaseModel):
    """Request payload to register a new recognized credential issuer."""

    issuer_name: str
    official_domain: str
    verification_domain: str
    verification_pattern: Optional[str] = None
    certificate_id_pattern: Optional[str] = None
    trusted_status: str = "TRUSTED"


class IssuerResponse(IssuerCreateRequest):
    """Response payload for a registered credential issuer."""

    id: str
    created_at: datetime
    updated_at: datetime


# --- Pipeline Domain Models ---

from enum import Enum


class CourseVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    SUSPICIOUS = "SUSPICIOUS"
    FRAUDULENT = "FRAUDULENT"
    UNVERIFIED = "UNVERIFIED"


class CourseExtractedFields(BaseModel):
    candidate_name: Optional[str] = None
    course_name: Optional[str] = None
    certificate_id: Optional[str] = None
    issue_date: Optional[str] = None
    issuer: Optional[str] = None
    ocr_confidence: float = 0.0
    grade: Optional[str] = None
    signatory: Optional[str] = None
    raw_text: Optional[str] = None


class CourseQRResult(BaseModel):
    qr_detected: bool = False
    qr_decoded: bool = False
    payload: Optional[str] = None
    points: Optional[List[List[float]]] = None
    details: dict[str, Any] = Field(default_factory=dict)


class CourseURLVerificationResult(BaseModel):
    is_valid_url: bool = False
    resolved_issuer: Optional[str] = None
    domain: Optional[str] = None
    risk_level: str = "SAFE"
    trust_score: float = 0.0
    domain_match: bool = False
    is_known_issuer: bool = False
    remarks: Optional[str] = None


class CourseOnlineRecord(BaseModel):
    is_available: bool = False
    candidate_name: Optional[str] = None
    course_name: Optional[str] = None
    certificate_id: Optional[str] = None
    issue_date: Optional[str] = None
    issuer: Optional[str] = None
    raw_details: dict[str, Any] = Field(default_factory=dict)


class CourseComparisonResult(BaseModel):
    name_match_score: float = 0.0
    course_match_score: float = 0.0
    cert_id_match_score: float = 0.0
    date_match_score: float = 0.0
    overall_match_score: float = 0.0
    online_record: Optional[CourseOnlineRecord] = None
    discrepancies: List[str] = Field(default_factory=list)
    copied_qr_detected: bool = False


class CourseForensicResult(BaseModel):
    tampering_detected: bool = False
    tampering_probability: float = 0.0
    copy_move_detected: bool = False
    noise_inconsistency_score: float = 0.0
    suspicious_bounding_boxes: List[List[int]] = Field(default_factory=list)


class CourseSealSignatureResult(BaseModel):
    signature_detected: bool = False
    seal_detected: bool = False
    signature_score: float = 0.0
    seal_score: float = 0.0
    details: Union[dict[str, Any], List[Any]] = Field(default_factory=dict)


class CourseVerificationDecision(BaseModel):
    status: CourseVerificationStatus
    overall_authenticity_score: float
    fraud_risk_score: float
    decision_reasons: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    signal_scores: dict[str, float] = Field(default_factory=dict)


class CourseVerificationResponse(BaseModel):
    verification_id: Any
    certificate_id: Optional[str] = None
    filename: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision: CourseVerificationDecision
    extracted_fields: CourseExtractedFields
    qr_result: CourseQRResult
    url_result: CourseURLVerificationResult
    comparison_result: CourseComparisonResult
    forensic_result: CourseForensicResult
    seal_signature_result: Optional[CourseSealSignatureResult] = None
