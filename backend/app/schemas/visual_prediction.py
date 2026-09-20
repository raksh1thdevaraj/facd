"""Pydantic V2 schemas for deep learning visual model predictions."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.pipeline import MLInferenceOutput


class VisualPredictionResult(BaseModel):
    """Result DTO from deep learning visual CNN model inference."""

    certificate_id: Optional[str] = Field(default=None, description="Certificate identifier")
    model_version: str = Field(default="visual_cnn_v1.0.0", description="Model version tag")
    model_type: str = Field(default="cnn_visual", description="Architecture type: cnn_visual")
    manipulation_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability that certificate image contains visual tampering [0.0, 1.0]",
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
    visual_embedding: List[float] = Field(
        default_factory=list,
        description="512-dimensional L2-normalized visual embedding vector",
    )
    gradcam_heatmap_path: Optional[str] = Field(
        default=None,
        description="Relative or absolute path to generated Grad-CAM heatmap overlay image",
    )
    latency_ms: float = Field(
        default=0.0,
        description="Inference and feature extraction latency in milliseconds",
    )

    def to_pipeline_output(self) -> MLInferenceOutput:
        """Convert to canonical SPEC-02 MLInferenceOutput contract."""
        return MLInferenceOutput(
            model_version=self.model_version,
            model_type=self.model_type,
            manipulation_probability=round(self.manipulation_probability, 4),
            predicted_class=self.predicted_class,
            feature_contributions={},
            gradcam_heatmap_path=self.gradcam_heatmap_path,
        )
