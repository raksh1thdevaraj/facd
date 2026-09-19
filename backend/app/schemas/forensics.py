from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from app.schemas.pipeline import ForensicsOutput, SuspiciousRegion
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class CloneMatch(BaseModel):
    """Represents a pair of duplicated/cloned regions identified in a copy-move forgery."""

    source_bbox: BoundingBox = Field(..., description="Normalized bounding box of source patch")
    target_bbox: BoundingBox = Field(..., description="Normalized bounding box of duplicated patch")
    source_pixel_bbox: PixelBoundingBox = Field(..., description="Pixel bbox of source patch")
    target_pixel_bbox: PixelBoundingBox = Field(..., description="Pixel bbox of duplicated patch")
    inlier_count: int = Field(..., ge=0, description="Number of supporting geometric inliers")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Verification confidence")
    displacement_vector: Tuple[float, float] = Field(
        ..., description="Translation vector (dx, dy) in pixels"
    )


class ForensicConfig(BaseModel):
    """Configuration parameters for Error Level Analysis, Copy-Move, and Noise analysis."""

    # Error Level Analysis parameters
    ela_quality: int = 90
    ela_qualities: List[int] = [75, 85, 90, 95]
    ela_scale_factor: int = 15
    ela_block_size: int = 32
    ela_variance_threshold: float = 450.0

    # Copy-Move keypoint parameters
    sift_max_features: int = 4000
    copy_move_ratio_thresh: float = 0.65
    copy_move_min_distance_px: float = 50.0
    dbscan_eps: float = 15.0
    dbscan_min_samples: int = 6
    ransac_reproj_thresh: float = 5.0

    # Local noise variance parameters
    noise_block_size: int = 32
    noise_mad_multiplier: float = 3.0

    # Score weighting
    weight_ela: float = 0.35
    weight_copy_move: float = 0.40
    weight_noise: float = 0.25

    # Visual output
    generate_heatmap: bool = True


class ForensicAnalysisResult(BaseModel):
    """Detailed forensic result DTO summarizing digital image manipulation findings."""

    document_id: str
    overall_forensic_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Authenticity score: 1.0 = pristine/untampered, 0.0 = heavily manipulated",
    )
    ela_score: float = Field(
        ..., ge=0.0, le=1.0, description="ELA authenticity score (1.0 = uniform compression)"
    )
    copy_move_score: float = Field(
        ..., ge=0.0, le=1.0, description="Clone score (1.0 = no clones detected)"
    )
    noise_inconsistency_score: float = Field(
        ..., ge=0.0, le=1.0, description="Noise consistency score (1.0 = uniform sensor grain)"
    )

    detected_clones: List[CloneMatch] = Field(default_factory=list)
    tampered_bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    suspicious_regions: List[SuspiciousRegion] = Field(default_factory=list)

    heatmap_image_path: Optional[str] = None
    execution_time_ms: float = 0.0

    @property
    def forensics_risk_score(self) -> float:
        """Risk score on [0.0, 100.0] scale (0 = clean, 100 = heavily tampered)."""
        return round(float(max(0.0, min(100.0, (1.0 - self.overall_forensic_score) * 100.0))), 2)

    def to_pipeline_output(self) -> ForensicsOutput:
        """Convert to canonical SPEC-02 ForensicsOutput contract."""
        return ForensicsOutput(
            document_id=self.document_id,
            ela_heatmap_path=self.heatmap_image_path or "",
            ela_score=round(1.0 - self.ela_score, 4),
            copy_move_detected=len(self.detected_clones) > 0,
            copy_move_clusters_count=len(self.detected_clones),
            copy_move_score=round(1.0 - self.copy_move_score, 4),
            font_irregularity_score=0.0,
            noise_inconsistency_score=round(1.0 - self.noise_inconsistency_score, 4),
            forensics_risk_score=self.forensics_risk_score,
            suspicious_regions=self.suspicious_regions,
        )
