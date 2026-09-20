from typing import Any, Dict, List, Optional, Union

import numpy as np
from pydantic import BaseModel, Field

from app.schemas.pipeline import MLInferenceOutput

FEATURE_NAMES: List[str] = [
    "file_size_kb",
    "has_exif",
    "software_editing_flag",
    "aspect_ratio_deviation",
    "ocr_mean_confidence",
    "ocr_min_confidence",
    "flagged_field_count",
    "missing_critical_fields_count",
    "baseline_alignment_score",
    "font_size_consistency_score",
    "stroke_weight_score",
    "character_spacing_score",
    "logical_consistency_score",
    "ela_score",
    "copy_move_score",
    "cloned_regions_count",
    "noise_inconsistency_score",
    "template_ssim_score",
    "template_feature_score",
    "seal_match_score",
    "record_found_flag",
    "record_match_score",
]


class FeatureVector(BaseModel):
    """Standardized 22-dimensional tabular feature vector extracted across upstream modules."""

    # Group A: Ingestion & Metadata (4)
    file_size_kb: float = Field(..., description="File size in kilobytes")
    has_exif: float = Field(..., ge=0.0, le=1.0, description="1 if EXIF exists, 0 otherwise")
    software_editing_flag: float = Field(
        ..., ge=0.0, le=1.0, description="1 if photo editing detected"
    )
    aspect_ratio_deviation: float = Field(
        ..., ge=0.0, description="Deviation from 1.414 aspect ratio"
    )

    # Group B: OCR & Text Quality (4)
    ocr_mean_confidence: float = Field(..., ge=0.0, le=1.0, description="Average OCR confidence")
    ocr_min_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Min critical field confidence"
    )
    flagged_field_count: float = Field(..., ge=0.0, description="Count of fields < 0.70 confidence")
    missing_critical_fields_count: float = Field(..., ge=0.0, description="Unextracted key fields")

    # Group C: Text Consistency (5)
    baseline_alignment_score: float = Field(..., ge=0.0, le=1.0)
    font_size_consistency_score: float = Field(..., ge=0.0, le=1.0)
    stroke_weight_score: float = Field(..., ge=0.0, le=1.0)
    character_spacing_score: float = Field(..., ge=0.0, le=1.0)
    logical_consistency_score: float = Field(..., ge=0.0, le=1.0)

    # Group D: Image Forensics (4)
    ela_score: float = Field(..., ge=0.0, le=1.0)
    copy_move_score: float = Field(..., ge=0.0, le=1.0)
    cloned_regions_count: float = Field(..., ge=0.0)
    noise_inconsistency_score: float = Field(..., ge=0.0, le=1.0)

    # Group E: Template & Record Matching (5)
    template_ssim_score: float = Field(..., ge=0.0, le=1.0)
    template_feature_score: float = Field(..., ge=0.0, le=1.0)
    seal_match_score: float = Field(..., ge=0.0, le=1.0)
    record_found_flag: float = Field(..., ge=0.0, le=1.0)
    record_match_score: float = Field(..., ge=0.0, le=1.0)

    def to_numpy(self) -> np.ndarray:
        """Convert pydantic feature model into ordered float32 NumPy array of shape (22,)."""
        return np.array(
            [getattr(self, name) for name in FEATURE_NAMES],
            dtype=np.float32,
        )

    def to_array(self) -> np.ndarray:
        """Alias for to_numpy()."""
        return self.to_numpy()

    def to_dict(self) -> Dict[str, float]:
        """Convert pydantic model to dictionary of feature name -> float."""
        return {name: float(getattr(self, name)) for name in FEATURE_NAMES}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FeatureVector":
        """Instantiate FeatureVector from arbitrary dictionary with fallback defaults."""
        return cls(**{name: float(d.get(name, 0.0)) for name in FEATURE_NAMES})


class FeatureImportanceItem(BaseModel):
    """Ranked feature contribution item for explainability."""

    feature_name: str
    importance_score: float
    rank: int
    domain_group: str


class PredictionResult(BaseModel):
    """Prediction result DTO summarizing baseline machine learning model inference."""

    certificate_id: Optional[str] = Field(default=None, description="Certificate identifier")
    model_version: str
    model_type: str = Field(default="tabular_baseline", description="Model architecture type")
    manipulation_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability that certificate is fake or manipulated [0.0, 1.0]",
    )
    predicted_class: str = Field(
        ...,
        description="'genuine' if probability < 0.50 else 'manipulated'",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in predicted class: max(p, 1-p)",
    )
    feature_contributions: Union[Dict[str, float], List[FeatureImportanceItem]] = Field(
        default_factory=dict,
        description="Feature contribution explanations",
    )
    feature_vector: Union[List[float], Dict[str, float], FeatureVector] = Field(
        default_factory=list,
        description="22D numerical feature values",
    )
    latency_ms: float = Field(
        default=0.0,
        description="Prediction latency in milliseconds",
    )

    def to_pipeline_output(self, gradcam_heatmap_path: Optional[str] = None) -> MLInferenceOutput:
        """Convert to canonical SPEC-02 MLInferenceOutput contract."""
        contribs_dict: Dict[str, float] = {}
        if isinstance(self.feature_contributions, dict):
            contribs_dict = self.feature_contributions
        elif isinstance(self.feature_contributions, list):
            for item in self.feature_contributions:
                if isinstance(item, FeatureImportanceItem):
                    contribs_dict[item.feature_name] = item.importance_score
                elif isinstance(item, dict):
                    contribs_dict[item.get("feature_name", "")] = float(
                        item.get("importance_score", item.get("contribution_score", 0.0))
                    )

        return MLInferenceOutput(
            model_version=self.model_version,
            model_type=self.model_type,
            manipulation_probability=round(self.manipulation_probability, 4),
            predicted_class=self.predicted_class,
            feature_contributions=contribs_dict,
            gradcam_heatmap_path=gradcam_heatmap_path,
        )
