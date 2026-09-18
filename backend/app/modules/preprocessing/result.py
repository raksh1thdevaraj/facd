from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import numpy as np

from app.schemas.pipeline import PreprocessingOutput
from app.schemas.preprocessing import PreprocessingResultDTO, PreprocessingStepMetric


@dataclass
class PreprocessingResult:
    """Encapsulates in-memory arrays, transformation metrics, and persisted paths."""

    enhanced_image: np.ndarray
    binarized_image: np.ndarray
    thumbnail_image: Optional[np.ndarray] = None
    applied_skew_angle: float = 0.0
    perspective_corrected: bool = False
    contrast_applied: bool = True
    noise_reduction_applied: bool = True
    original_width: int = 0
    original_height: int = 0
    processed_width: int = 0
    processed_height: int = 0
    step_metrics: Dict[str, float] = field(default_factory=dict)
    enhanced_image_path: Optional[Path] = None
    binarized_image_path: Optional[Path] = None
    thumbnail_path: Optional[Path] = None

    def to_pipeline_output(self, document_id: str) -> PreprocessingOutput:
        """Produce the canonical SPEC-02 PreprocessingOutput model."""
        return PreprocessingOutput(
            document_id=document_id,
            processed_image_path=(
                str(self.enhanced_image_path.resolve()) if self.enhanced_image_path else ""
            ),
            thumbnail_path=(str(self.thumbnail_path.resolve()) if self.thumbnail_path else ""),
            original_width=self.original_width,
            original_height=self.original_height,
            processed_width=self.processed_width,
            processed_height=self.processed_height,
            deskew_angle_degrees=self.applied_skew_angle,
            contrast_applied=self.contrast_applied,
            noise_reduction_applied=self.noise_reduction_applied,
        )

    def to_dto(self, document_id: str) -> PreprocessingResultDTO:
        """Produce the API serializable PreprocessingResultDTO."""
        step_metric_items = [
            PreprocessingStepMetric(step_name=k, duration_ms=v)
            for k, v in self.step_metrics.items()
        ]
        total_time = sum(self.step_metrics.values())
        return PreprocessingResultDTO(
            document_id=document_id,
            enhanced_image_path=(str(self.enhanced_image_path) if self.enhanced_image_path else ""),
            binarized_image_path=(
                str(self.binarized_image_path) if self.binarized_image_path else ""
            ),
            thumbnail_path=str(self.thumbnail_path) if self.thumbnail_path else "",
            original_width=self.original_width,
            original_height=self.original_height,
            processed_width=self.processed_width,
            processed_height=self.processed_height,
            deskew_angle_degrees=self.applied_skew_angle,
            perspective_corrected=self.perspective_corrected,
            contrast_applied=self.contrast_applied,
            noise_reduction_applied=self.noise_reduction_applied,
            step_metrics=step_metric_items,
            total_duration_ms=total_time,
        )
