import logging
import time
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from app.config import settings
from app.modules.forensics.copy_move_detector import CopyMoveDetector
from app.modules.forensics.ela_analyzer import ELAAnalyzer
from app.modules.forensics.heatmap_generator import ForensicHeatmapGenerator
from app.modules.forensics.noise_analyzer import NoiseAnalyzer
from app.modules.forensics.score_calculator import ForensicScoreCalculator
from app.schemas.forensics import ForensicAnalysisResult, ForensicConfig
from app.schemas.pipeline import ForensicsOutput

logger = logging.getLogger(__name__)


class ForensicService:
    """Orchestrates comprehensive classical digital image forensics:
    Error Level Analysis, Copy-Move clone detection, and local sensor noise variance.
    """

    def __init__(
        self,
        config: Optional[ForensicConfig] = None,
        report_dir: Optional[Path] = None,
    ):
        self.config = config or ForensicConfig()
        self.report_dir = report_dir or settings.REPORT_DIR
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.ela_analyzer = ELAAnalyzer(config=self.config)
        self.copy_move_detector = CopyMoveDetector(config=self.config)
        self.noise_analyzer = NoiseAnalyzer(config=self.config)
        self.score_calculator = ForensicScoreCalculator(config=self.config)

    def analyze(
        self,
        document_id: str,
        raw_image_or_path: Union[np.ndarray, Path, str],
        output_heatmap_path: Optional[Path] = None,
    ) -> ForensicAnalysisResult:
        """Run complete forensic analysis suite on the pristine uploaded certificate image."""
        start_time = time.perf_counter()

        # Load image array
        if isinstance(raw_image_or_path, (str, Path)):
            img_path = Path(raw_image_or_path)
            if not img_path.exists():
                raise FileNotFoundError(f"Raw certificate image not found: {img_path}")
            image = cv2.imread(str(img_path))
            if image is None:
                raise ValueError(f"Failed to read image at: {img_path}")
            image_source = img_path
        elif isinstance(raw_image_or_path, np.ndarray):
            image = raw_image_or_path
            image_source = raw_image_or_path
        else:
            raise TypeError(f"Invalid image type: {type(raw_image_or_path)}")

        # 1. Error Level Analysis
        ela_map, ela_score, ela_bboxes, ela_pix_bboxes = self.ela_analyzer.analyze(image_source)

        # 2. Copy-Move / Clone Keypoint Analysis
        copy_move_score, clones = self.copy_move_detector.analyze(image)

        # 3. Local Noise Variance Inconsistency Analysis
        noise_map, noise_score, noise_bboxes, noise_pix_bboxes = self.noise_analyzer.analyze(image)

        # 4. Score Aggregation & Suspicious Region Formulation
        ela_pairs = list(zip(ela_bboxes, ela_pix_bboxes, strict=False))
        noise_pairs = list(zip(noise_bboxes, noise_pix_bboxes, strict=False))

        overall_score, suspicious_regions, category = self.score_calculator.calculate(
            ela_score=ela_score,
            copy_move_score=copy_move_score,
            noise_score=noise_score,
            ela_bboxes=ela_pairs,
            clones=clones,
            noise_bboxes=noise_pairs,
        )

        # 5. Thermal Heatmap Generation
        heatmap_path_str: Optional[str] = None
        if self.config.generate_heatmap:
            heatmap_file = output_heatmap_path or (
                self.report_dir / f"{document_id}_forensics_heatmap.png"
            )
            ForensicHeatmapGenerator.generate_composite_heatmap(
                raw_image=image,
                ela_map=ela_map,
                clone_matches=clones,
                noise_map=noise_map,
                output_path=heatmap_file,
            )
            heatmap_path_str = str(heatmap_file.resolve())

        all_tampered_bboxes = ela_bboxes + [c.target_bbox for c in clones] + noise_bboxes

        execution_ms = (time.perf_counter() - start_time) * 1000.0
        if execution_ms > 5000.0:
            logger.warning(
                "ForensicService execution exceeded 5.0s limit: %.2fms for document %s",
                execution_ms,
                document_id,
            )

        return ForensicAnalysisResult(
            document_id=document_id,
            overall_forensic_score=overall_score,
            ela_score=ela_score,
            copy_move_score=copy_move_score,
            noise_inconsistency_score=noise_score,
            detected_clones=clones,
            tampered_bounding_boxes=all_tampered_bboxes,
            suspicious_regions=suspicious_regions,
            heatmap_image_path=heatmap_path_str,
            execution_time_ms=execution_ms,
        )

    def analyze_to_pipeline_output(
        self,
        document_id: str,
        raw_image_or_path: Union[np.ndarray, Path, str],
        output_heatmap_path: Optional[Path] = None,
    ) -> ForensicsOutput:
        """Run forensics and return canonical SPEC-02 ForensicsOutput."""
        result = self.analyze(
            document_id=document_id,
            raw_image_or_path=raw_image_or_path,
            output_heatmap_path=output_heatmap_path,
        )
        return result.to_pipeline_output()


_forensic_service_instance: Optional[ForensicService] = None


def get_forensic_service() -> ForensicService:
    """FastAPI dependency injection provider for ForensicService."""
    global _forensic_service_instance
    if _forensic_service_instance is None:
        _forensic_service_instance = ForensicService()
    return _forensic_service_instance
