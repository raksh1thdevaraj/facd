"""Document Tampering & Forensic Localization Engine (Phase 7).

Leverages classical forensic analysis (ELA, Copy-Move block matching, Laplacian noise variance)
and localized text bounding-box consistency to detect pixel-level alterations, text splicing,
and compression artifacts.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from app.config import settings
from app.modules.forensics.service import ForensicService
from app.schemas.course_certificate import TamperingAnalysisResult

logger = logging.getLogger(__name__)


class CourseTamperingAnalyzer:
    """Detects physical and pixel-level tampering in course certificates."""

    def __init__(self, forensic_service: Optional[ForensicService] = None) -> None:
        self.forensics = forensic_service or ForensicService()

    def analyze_certificate(
        self,
        image_input: Union[np.ndarray, Path, str],
        document_id: Optional[str] = None,
        key_regions: Optional[list[list[int]]] = None,
    ) -> TamperingAnalysisResult:
        """Execute full forensic analysis and synthesize localized tampering probabilities."""
        doc_id = document_id or str(uuid.uuid4())
        heatmap_name = f"tamper_heatmap_{doc_id[:8]}.png"
        heatmap_path = settings.REPORT_DIR / heatmap_name

        try:
            forensic_res = self.forensics.analyze(
                document_id=doc_id,
                raw_image_or_path=image_input,
                output_heatmap_path=heatmap_path,
            )

            ela_score = float(forensic_res.ela_score)
            copy_move_score = float(forensic_res.copy_move_score)
            noise_score = float(forensic_res.noise_inconsistency_score)

            # Combined tampering probability (lower authenticity score means higher
            # tampering probability)
            # Forensics score is 1.0 = clean, 0.0 = manipulated
            tampering_prob = max(0.0, min(1.0, 1.0 - float(forensic_res.overall_forensic_score)))

            # Identify tampering type
            tampering_type = "none"
            if copy_move_score < 0.60:
                tampering_type = "copy_move_splicing"
            elif ela_score < 0.60:
                tampering_type = "compression_manipulation"
            elif noise_score < 0.60:
                tampering_type = "noise_inconsistency"
            elif tampering_prob > 0.40:
                tampering_type = "pixel_alteration"

            # Suspicious bounding boxes
            regions: list[list[int]] = []
            if forensic_res.suspicious_regions:
                for reg in forensic_res.suspicious_regions:
                    pixel_b = getattr(reg, "pixel_bbox", None)
                    norm_b = getattr(reg, "bbox", None)
                    if pixel_b is not None and hasattr(pixel_b, "x"):
                        regions.append(
                            [
                                int(pixel_b.x),
                                int(pixel_b.y),
                                int(pixel_b.width),
                                int(pixel_b.height),
                            ]
                        )
                    elif norm_b is not None and hasattr(norm_b, "x1"):
                        regions.append(
                            [
                                int(norm_b.x1),
                                int(norm_b.y1),
                                int(norm_b.x2 - norm_b.x1),
                                int(norm_b.y2 - norm_b.y1),
                            ]
                        )
            elif key_regions and tampering_prob > 0.35:
                # Include highlighted key regions if elevated tampering detected
                regions.extend(key_regions)

            heatmap_rel = f"/storage/reports/{heatmap_name}" if heatmap_path.exists() else None

            return TamperingAnalysisResult(
                tampering_probability=round(tampering_prob, 4),
                tampering_regions=regions,
                tampering_type=tampering_type,
                model_confidence=round(
                    float(
                        getattr(
                            forensic_res,
                            "confidence_score",
                            getattr(forensic_res, "overall_forensic_score", 0.85),
                        )
                    ),
                    4,
                ),
                ela_anomaly_score=round(1.0 - ela_score, 4),
                copy_move_score=round(1.0 - copy_move_score, 4),
                noise_anomaly_score=round(1.0 - noise_score, 4),
                heatmap_relative_path=heatmap_rel,
            )

        except Exception as err:
            logger.warning("Forensic analysis error in course tampering analyzer: %s", err)
            return TamperingAnalysisResult(
                tampering_probability=0.0,
                tampering_regions=[],
                tampering_type="analysis_unavailable",
                model_confidence=0.50,
            )

    def analyze(self, image_input: Union[np.ndarray, Path, str]) -> Any:
        """Adapter returning CourseForensicResult for unified pipeline."""
        from app.schemas.course_certificate import CourseForensicResult

        res = self.analyze_certificate(image_input)
        is_tampered = res.tampering_probability > 0.45 or res.copy_move_score > 0.40
        return CourseForensicResult(
            tampering_detected=is_tampered,
            tampering_probability=res.tampering_probability,
            copy_move_detected=res.copy_move_score > 0.40,
            noise_inconsistency_score=res.noise_anomaly_score,
            suspicious_bounding_boxes=res.tampering_regions,
        )
