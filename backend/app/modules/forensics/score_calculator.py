import uuid
from typing import List, Tuple

from app.schemas.forensics import CloneMatch, ForensicConfig
from app.schemas.pipeline import SuspiciousRegion
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class ForensicScoreCalculator:
    """Aggregates Error Level Analysis, Copy-Move, and Noise consistency scores
    into a calibrated overall score and generates standardized suspicious regions.
    """

    def __init__(self, config: ForensicConfig):
        self.config = config

    def calculate(
        self,
        ela_score: float,
        copy_move_score: float,
        noise_score: float,
        ela_bboxes: List[Tuple[BoundingBox, PixelBoundingBox]],
        clones: List[CloneMatch],
        noise_bboxes: List[Tuple[BoundingBox, PixelBoundingBox]],
    ) -> Tuple[float, List[SuspiciousRegion], str]:
        """Compute composite forensic authenticity score [0.0, 1.0], assemble suspicious regions,
        and assign authenticity classification band.

        Returns:
            Tuple of:
            - overall_forensic_score: float [0.0, 1.0]
            - suspicious_regions: List[SuspiciousRegion]
            - category: str ("AUTHENTIC", "INCONCLUSIVE", "MANIPULATED")
        """
        raw_score = (
            self.config.weight_ela * ela_score
            + self.config.weight_copy_move * copy_move_score
            + self.config.weight_noise * noise_score
        )

        # Veto Rule 1: Confirmed copy-move clone with strong support (>= 8 inliers)
        strong_clones = [c for c in clones if c.inlier_count >= 8]
        if strong_clones:
            raw_score = min(raw_score, 0.30)
        elif clones:
            raw_score = min(raw_score, 0.50)

        # Veto Rule 2: Severe ELA compression anomaly
        if ela_score < 0.50 and ela_bboxes:
            raw_score = min(raw_score, 0.45)

        overall_score = round(max(0.0, min(1.0, raw_score)), 4)

        # Authenticity classification
        if overall_score >= 0.85:
            category = "AUTHENTIC"
        elif overall_score >= 0.60:
            category = "INCONCLUSIVE"
        else:
            category = "MANIPULATED"

        # Build SuspiciousRegion objects for SPEC-02
        suspicious_regions: List[SuspiciousRegion] = []

        # 1. ELA Anomaly regions
        for norm_box, pix_box in ela_bboxes:
            suspicious_regions.append(
                SuspiciousRegion(
                    region_id=f"reg_ela_{uuid.uuid4().hex[:6]}",
                    bbox=norm_box,
                    pixel_bbox=pix_box,
                    forensic_type="ELA_ANOMALY",
                    anomaly_score=round(max(0.0, min(1.0, 1.0 - ela_score)), 3),
                    description=(
                        f"JPEG recompression discrepancy (error variance indicates foreign patch "
                        f"at {pix_box.x},{pix_box.y} {pix_box.width}x{pix_box.height})"
                    ),
                )
            )

        # 2. Copy-Move Clone regions
        for clone in clones:
            suspicious_regions.append(
                SuspiciousRegion(
                    region_id=f"reg_clone_{uuid.uuid4().hex[:6]}",
                    bbox=clone.target_bbox,
                    pixel_bbox=clone.target_pixel_bbox,
                    forensic_type="COPY_MOVE",
                    anomaly_score=round(clone.confidence, 3),
                    description=(
                        f"Copy-Move forgery detected: patch cloned from "
                        f"({clone.source_pixel_bbox.x},{clone.source_pixel_bbox.y}) with "
                        f"{clone.inlier_count} geometric inliers"
                    ),
                )
            )

        # 3. Noise Inconsistency regions
        for norm_box, pix_box in noise_bboxes:
            suspicious_regions.append(
                SuspiciousRegion(
                    region_id=f"reg_noise_{uuid.uuid4().hex[:6]}",
                    bbox=norm_box,
                    pixel_bbox=pix_box,
                    forensic_type="NOISE_INCONSISTENCY",
                    anomaly_score=round(max(0.0, min(1.0, 1.0 - noise_score)), 3),
                    description=(
                        f"Sensor noise variance discontinuity (patch at {pix_box.x},{pix_box.y} "
                        f"originates from different capture device or graphic editing)"
                    ),
                )
            )

        return overall_score, suspicious_regions, category
