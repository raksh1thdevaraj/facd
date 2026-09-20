"""Pydantic V2 schemas for explainability, feature attributions, and spatial overlays."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.primitives import PixelBoundingBox


class FindingSeverity(str, Enum):
    """Severity of a detected anomaly finding."""

    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    WARNING = "WARNING"
    INFO = "INFO"


class FindingCategory(str, Enum):
    """Categorical domain for explainability findings."""

    DATABASE_RECORD = "DATABASE_RECORD"
    IMAGE_FORENSICS = "IMAGE_FORENSICS"
    TYPOGRAPHY = "TYPOGRAPHY"
    COMPRESSION = "COMPRESSION"
    CHRONOLOGY = "CHRONOLOGY"
    TEMPLATE_MATCH = "TEMPLATE_MATCH"
    DEEP_LEARNING = "DEEP_LEARNING"


class FindingBullet(BaseModel):
    """Structured human-readable finding bullet point."""

    id: str = Field(..., description="Unique finding ID")
    severity: FindingSeverity = Field(..., description="Anomaly severity")
    category: FindingCategory = Field(..., description="Analytical category")
    title: str = Field(..., description="Short finding heading")
    description: str = Field(..., description="Detailed explanation for verifiers")
    evidence_value: Optional[str] = Field(
        default=None, description="Quantitative or string evidence"
    )


class FeatureAttribution(BaseModel):
    """Local SHAP feature attribution item explaining ML model decision."""

    feature_name: str = Field(..., description="Name of feature")
    domain_group: str = Field(..., description="Analytical domain group")
    feature_value: float = Field(..., description="Raw numerical feature value")
    shap_value: float = Field(..., description="Raw SHAP contribution value")
    impact_percentage: float = Field(..., description="Relative contribution percentage [0, 100]")
    direction: str = Field(
        ...,
        description="'INCREASES_RISK' if shap_value > 0 else 'DECREASES_RISK'",
    )


class NormalizedBox(BaseModel):
    """Bounding box coordinates normalized to [0.0, 1.0] relative to original image size."""

    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    w: float = Field(..., ge=0.0, le=1.0)
    h: float = Field(..., ge=0.0, le=1.0)


class UnifiedAnomalyBox(BaseModel):
    """Spatial anomaly localized onto original high-resolution document canvas."""

    id: str = Field(..., description="Unique box ID")
    category: str = Field(..., description="Category: CLONE, BASELINE, FONT_SIZE, OCR, ELA")
    severity: FindingSeverity = Field(..., description="Severity level")
    box: PixelBoundingBox = Field(..., description="Absolute pixel coordinates on raw image")
    normalized_box: NormalizedBox = Field(..., description="Normalized coordinates [0, 1]")
    label: str = Field(..., description="Short tag for pill label on visual overlay")
    description: str = Field(..., description="Tooltip text for interactive UI")
    color: str = Field(..., description="Hex color code (e.g. #D50000)")


class InteractiveOverlayPayload(BaseModel):
    """Lightweight JSON payload for interactive client-side SVG/Canvas rendering."""

    certificate_id: str
    image_width: int
    image_height: int
    anomalies: List[UnifiedAnomalyBox] = Field(default_factory=list)


class ExplainabilityReport(BaseModel):
    """Comprehensive explainability dossier explaining verification decision."""

    certificate_id: str = Field(..., description="Certificate identifier")
    primary_verdict_rationale: str = Field(..., description="Executive summary explanation")
    key_findings: List[FindingBullet] = Field(
        default_factory=list, description="Categorized findings"
    )
    top_contributing_features: List[FeatureAttribution] = Field(
        default_factory=list,
        description="Ranked SHAP feature attributions",
    )
    spatial_anomalies: List[UnifiedAnomalyBox] = Field(
        default_factory=list,
        description="Unified spatial anomaly boxes",
    )
    unified_overlay_path: Optional[str] = Field(
        default=None,
        description="Path to high-resolution rendered visual evidence PNG",
    )
    interactive_overlay: InteractiveOverlayPayload = Field(
        ...,
        description="JSON payload for interactive frontend SVG rendering",
    )
    execution_time_ms: float = Field(default=0.0, description="Explainability pipeline latency")
