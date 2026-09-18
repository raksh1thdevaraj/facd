from typing import List, Literal, Tuple

from pydantic import BaseModel, ConfigDict, Field


class PreprocessingConfig(BaseModel):
    """Configuration parameters for the preprocessing pipeline stages."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Noise reduction
    noise_filter: Literal["bilateral", "median", "none"] = "bilateral"
    bilateral_d: int = 9
    bilateral_sigma_color: float = 75.0
    bilateral_sigma_space: float = 75.0

    # Contrast enhancement (CLAHE)
    contrast_enhancement_enabled: bool = True
    clahe_clip_limit: float = 2.0
    clahe_tile_grid_size: Tuple[int, int] = (8, 8)

    # Skew correction
    deskew_enabled: bool = True
    max_deskew_angle: float = 45.0
    min_angle_threshold: float = 0.2

    # Perspective rectification
    perspective_enabled: bool = True
    min_document_area_ratio: float = 0.25

    # Adaptive binarization for OCR
    binarization_method: Literal["adaptive_gaussian", "otsu"] = "adaptive_gaussian"
    adaptive_block_size: int = 21
    adaptive_c: float = 11.0

    # Resolution boundaries
    min_long_edge: int = 1200
    max_long_edge: int = 3200
    thumbnail_max_edge: int = 400


class PreprocessingStepMetric(BaseModel):
    """Execution timing and status for an individual pipeline step."""

    step_name: str
    duration_ms: float = Field(..., ge=0.0)
    status: str = Field(default="COMPLETED")


class PreprocessingResultDTO(BaseModel):
    """Serialized summary of preprocessing results matching API and inspection needs."""

    document_id: str
    enhanced_image_path: str
    binarized_image_path: str
    thumbnail_path: str
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    deskew_angle_degrees: float = 0.0
    perspective_corrected: bool = False
    contrast_applied: bool = True
    noise_reduction_applied: bool = True
    step_metrics: List[PreprocessingStepMetric] = Field(default_factory=list)
    total_duration_ms: float = 0.0
