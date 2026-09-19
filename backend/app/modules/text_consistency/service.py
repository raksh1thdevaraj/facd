import logging
import time
from pathlib import Path
from typing import List, Optional, Union

import cv2
import numpy as np

from app.config import settings
from app.modules.ocr.spatial_analyzer import SpatialLayoutAnalyzer, TextLine
from app.modules.text_consistency.baseline_checker import BaselineAlignmentAnalyzer
from app.modules.text_consistency.font_size_analyzer import FontSizeAnalyzer
from app.modules.text_consistency.format_checker import FormatChecker
from app.modules.text_consistency.logical_validator import LogicalConsistencyValidator
from app.modules.text_consistency.score_aggregator import ScoreAggregator
from app.modules.text_consistency.spacing_analyzer import CharacterSpacingAnalyzer
from app.modules.text_consistency.stroke_width_analyzer import StrokeWidthAnalyzer
from app.modules.text_consistency.visualizer import TextAnomalyVisualizer
from app.schemas.pipeline import CertificateFields, OCRToken, TextConsistencyOutput
from app.schemas.text_consistency import (
    AnomalousRegion,
    TextConsistencyConfig,
    TextConsistencyResult,
)

logger = logging.getLogger(__name__)


class TextConsistencyService:
    """Orchestrates comprehensive text consistency, typographical forensics,
    and academic domain logic analysis for certificate verification.
    """

    def __init__(
        self,
        config: Optional[TextConsistencyConfig] = None,
        report_dir: Optional[Path] = None,
    ):
        self.config = config or TextConsistencyConfig()
        self.report_dir = report_dir or settings.REPORT_DIR
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # Initialize modular analyzers
        self.baseline_checker = BaselineAlignmentAnalyzer(config=self.config)
        self.font_size_analyzer = FontSizeAnalyzer(config=self.config)
        self.stroke_width_analyzer = StrokeWidthAnalyzer(config=self.config)
        self.spacing_analyzer = CharacterSpacingAnalyzer(config=self.config)
        self.format_checker = FormatChecker(config=self.config)
        self.logical_validator = LogicalConsistencyValidator(config=self.config)
        self.score_aggregator = ScoreAggregator(config=self.config)

    def analyze(
        self,
        document_id: str,
        ocr_tokens: List[OCRToken],
        text_lines: Optional[List[TextLine]] = None,
        image_or_path: Optional[Union[np.ndarray, Path, str]] = None,
        extracted_fields: Optional[CertificateFields] = None,
        output_overlay_path: Optional[Path] = None,
    ) -> TextConsistencyResult:
        """Run complete typographical forensics and logical consistency pipeline."""
        start_time = time.perf_counter()

        # Resolve image array if provided
        image: Optional[np.ndarray] = None
        if image_or_path is not None:
            if isinstance(image_or_path, (str, Path)):
                img_path = Path(image_or_path)
                if img_path.exists():
                    image = cv2.imread(str(img_path))
            elif isinstance(image_or_path, np.ndarray):
                image = image_or_path

        # Reconstruct reading-order text lines if not provided
        if text_lines is None:
            text_lines = SpatialLayoutAnalyzer.group_tokens_into_lines(ocr_tokens)

        fields = extracted_fields or CertificateFields()
        raw_text = " ".join(t.text for t in ocr_tokens).strip()

        all_anomalies: List[AnomalousRegion] = []

        # 1. Baseline Alignment
        baseline_score, baseline_anomalies = self.baseline_checker.analyze(text_lines)
        all_anomalies.extend(baseline_anomalies)

        # 2. Font Size & Height Consistency
        font_size_score, font_size_anomalies = self.font_size_analyzer.analyze(text_lines)
        all_anomalies.extend(font_size_anomalies)

        # 3. Stroke Width Transform (SWT)
        stroke_score, stroke_anomalies = self.stroke_width_analyzer.analyze(image, text_lines)
        all_anomalies.extend(stroke_anomalies)

        # 4. Character Spacing & Line Leading
        spacing_score, spacing_anomalies = self.spacing_analyzer.analyze(text_lines)
        all_anomalies.extend(spacing_anomalies)

        # 5. Format & Script Checking
        format_score, format_anomalies = self.format_checker.analyze(ocr_tokens)
        all_anomalies.extend(format_anomalies)

        # 6. Chronological & Score Logic
        logical_score, logical_anomalies, logical_checks = self.logical_validator.analyze(
            fields, raw_text
        )
        all_anomalies.extend(logical_anomalies)

        # 7. Aggregate Scores & Generate Audit Checks
        overall_score, audit_checks = self.score_aggregator.aggregate(
            baseline_score=baseline_score,
            font_size_score=font_size_score,
            stroke_weight_score=stroke_score,
            spacing_score=spacing_score,
            format_score=format_score,
            logical_score=logical_score,
            anomalies=all_anomalies,
            existing_checks=logical_checks,
        )

        # 8. Render Visual Heatmap / Overlay if configured
        overlay_path_str: Optional[str] = None
        if self.config.generate_overlay:
            overlay_file = output_overlay_path or (
                self.report_dir / f"{document_id}_text_anomalies.png"
            )
            TextAnomalyVisualizer.render_overlay(
                image=image,
                anomalies=all_anomalies,
                output_path=overlay_file,
            )
            overlay_path_str = str(overlay_file.resolve())

        execution_ms = (time.perf_counter() - start_time) * 1000.0
        if execution_ms > 2000.0:
            logger.warning(
                "TextConsistencyService execution time exceeded 2.0s limit: %.2fms for document %s",
                execution_ms,
                document_id,
            )

        return TextConsistencyResult(
            document_id=document_id,
            overall_text_consistency_score=overall_score,
            baseline_alignment_score=baseline_score,
            font_size_consistency_score=font_size_score,
            stroke_weight_consistency_score=stroke_score,
            spacing_consistency_score=spacing_score,
            format_consistency_score=format_score,
            logical_consistency_score=logical_score,
            anomalous_regions=all_anomalies,
            checks=audit_checks,
            visualization_image_path=overlay_path_str,
            execution_time_ms=execution_ms,
        )

    def analyze_to_pipeline_output(
        self,
        document_id: str,
        ocr_tokens: List[OCRToken],
        text_lines: Optional[List[TextLine]] = None,
        image_or_path: Optional[Union[np.ndarray, Path, str]] = None,
        extracted_fields: Optional[CertificateFields] = None,
    ) -> TextConsistencyOutput:
        """Run text consistency analysis and return canonical SPEC-02 TextConsistencyOutput."""
        result = self.analyze(
            document_id=document_id,
            ocr_tokens=ocr_tokens,
            text_lines=text_lines,
            image_or_path=image_or_path,
            extracted_fields=extracted_fields,
        )
        return result.to_pipeline_output()


_text_consistency_service_instance: Optional[TextConsistencyService] = None


def get_text_consistency_service() -> TextConsistencyService:
    """FastAPI dependency injection provider for TextConsistencyService."""
    global _text_consistency_service_instance
    if _text_consistency_service_instance is None:
        _text_consistency_service_instance = TextConsistencyService()
    return _text_consistency_service_instance
