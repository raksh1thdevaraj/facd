from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.pipeline import TemplateMatchOutput


class TierStatus(str, Enum):
    """Three-Tier Match Status as defined by FR-TMP-03."""

    TIER_1_VERIFIED = "TIER_1_VERIFIED"  # Confirmed against official university database records
    TIER_2_CONSISTENT = (
        "TIER_2_CONSISTENT"  # Layout & typography consistent with master template; record missing
    )
    TIER_3_INCONSISTENT = (
        "TIER_3_INCONSISTENT"  # Blatant contradiction in records or counterfeit layout
    )
    TIER_3_UNVERIFIED = (
        "TIER_3_UNVERIFIED"  # Fallback: No template/record available or inconclusive evidence
    )


class SealROI(BaseModel):
    """Bounding box coordinates for seal/logo/emblem in pixel dimensions."""

    x: int = Field(..., ge=0, description="Top-left X in pixels")
    y: int = Field(..., ge=0, description="Top-left Y in pixels")
    width: int = Field(..., gt=0, description="Width in pixels")
    height: int = Field(..., gt=0, description="Height in pixels")


class TemplateMatchMetrics(BaseModel):
    """Detailed visual comparison metrics against master template."""

    ssim_score: float = Field(..., ge=0.0, le=1.0, description="Structural Similarity Index")
    feature_similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="ORB/homography inlier ratio"
    )
    seal_match_score: float = Field(
        ..., ge=0.0, le=1.0, description="Emblem correlation & color score"
    )
    overall_template_score: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted composite template similarity"
    )
    alignment_success: bool = Field(
        ..., description="Whether RANSAC homography alignment succeeded"
    )
    inlier_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class RecordVerificationResult(BaseModel):
    """Result of cross-referencing extracted certificate text against database records."""

    record_found: bool = Field(default=False)
    matched_record_id: Optional[str] = None
    name_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    roll_no_match: bool = Field(default=False)
    degree_match: bool = Field(default=False)
    passing_year_match: bool = Field(default=False)
    cgpa_match: bool = Field(default=False)
    discrepancies: List[str] = Field(default_factory=list)


class TierClassification(BaseModel):
    """Final three-tier determination and confidence justification."""

    tier: TierStatus
    confidence: float = Field(..., ge=0.0, le=1.0)
    primary_reason: str
    discrepancies: List[str] = Field(default_factory=list)


class TemplateVerificationResult(BaseModel):
    """Composite verification DTO containing visual, database, and tier assessment."""

    document_id: str
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    template_metrics: Optional[TemplateMatchMetrics] = None
    record_result: RecordVerificationResult = Field(default_factory=RecordVerificationResult)
    tier_classification: TierClassification
    visual_diff_path: Optional[str] = None
    execution_time_ms: float = 0.0

    @property
    def template_risk_score(self) -> float:
        """Calculate a risk score on [0.0, 100.0] scale."""
        if self.tier_classification.tier == TierStatus.TIER_1_VERIFIED:
            return 0.0
        elif self.tier_classification.tier == TierStatus.TIER_3_INCONSISTENT:
            return 95.0
        elif self.tier_classification.tier == TierStatus.TIER_2_CONSISTENT:
            if self.template_metrics:
                return round(
                    float(
                        max(
                            0.0,
                            min(
                                100.0, (1.0 - self.template_metrics.overall_template_score) * 100.0
                            ),
                        )
                    ),
                    2,
                )
            return 20.0
        else:  # TIER_3_UNVERIFIED
            return 50.0

    def to_pipeline_output(self) -> TemplateMatchOutput:
        """Convert to canonical SPEC-02 TemplateMatchOutput contract."""
        record_matches = {
            "name": self.record_result.name_match_score >= 0.85,
            "roll_number": self.record_result.roll_no_match,
            "degree": self.record_result.degree_match,
            "passing_year": self.record_result.passing_year_match,
            "cgpa": self.record_result.cgpa_match,
        }
        return TemplateMatchOutput(
            matched_template_id=self.template_id,
            matched_template_name=self.template_name,
            layout_similarity_score=(
                round(self.template_metrics.ssim_score, 4) if self.template_metrics else None
            ),
            logo_signature_similarity=(
                round(self.template_metrics.seal_match_score, 4) if self.template_metrics else None
            ),
            template_risk_score=self.template_risk_score,
            record_found=self.record_result.record_found,
            record_field_matches=record_matches,
        )


# ==============================================================================
# API Request & Response Models
# ==============================================================================
class TemplateSummary(BaseModel):
    """Summary of registered institutional template for listing and OpenAPI spec."""

    template_id: str
    institution_id: str
    institution_name: str
    template_name: str
    degree_program: Optional[str] = None
    uploaded_at: datetime


class TemplateDetailResponse(TemplateSummary):
    """Detailed view of registered institutional template."""

    image_path: str
    seal_roi: Optional[Dict[str, Any]] = None
    variable_regions: Optional[List[Dict[str, Any]]] = None


class RecordCreateRequest(BaseModel):
    """Single student record payload."""

    institution_id: str
    student_name: str
    roll_number: str
    degree_name: str
    passing_year: int
    cgpa: Optional[float] = None
    issue_date: Optional[str] = None


class RecordBulkImportResponse(BaseModel):
    """Summary of bulk student record CSV ingestion."""

    total_records_processed: int
    records_inserted: int
    duplicates_skipped: int
    errors: List[str] = Field(default_factory=list)
