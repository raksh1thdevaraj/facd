import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

import cv2
import numpy as np

from app.config import settings
from app.modules.ocr.base_engine import BaseOCREngine
from app.modules.ocr.confidence_evaluator import ConfidenceEvaluator
from app.modules.ocr.engine_factory import EngineFactory
from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.field_extractors.cert_id_extractor import CertificateIdExtractor
from app.modules.ocr.field_extractors.date_extractor import DateExtractor
from app.modules.ocr.field_extractors.degree_extractor import DegreeExtractor
from app.modules.ocr.field_extractors.grade_extractor import GradeExtractor
from app.modules.ocr.field_extractors.institution_extractor import (
    InstitutionExtractor,
)
from app.modules.ocr.field_extractors.name_extractor import StudentNameExtractor
from app.modules.ocr.field_extractors.roll_no_extractor import RollNumberExtractor
from app.modules.ocr.spatial_analyzer import SpatialLayoutAnalyzer
from app.modules.ocr.visualizer import OCRVisualizer
from app.schemas.ocr import OCRConfig, OCRResultDTO
from app.schemas.pipeline import OCROutput

logger = logging.getLogger(__name__)


class OCRService:
    """Orchestrates optical character recognition, spatial layout reconstruction,
    academic field extraction, confidence threshold evaluation, and visual overlay rendering.
    """

    def __init__(
        self,
        engine: Optional[BaseOCREngine] = None,
        config: Optional[OCRConfig] = None,
        report_dir: Optional[Path] = None,
    ):
        self.config = config or OCRConfig(
            engine=settings.OCR_ENGINE,
            languages=settings.OCR_LANGUAGES.split(","),
            confidence_threshold=0.70,
        )
        self.engine = engine or EngineFactory.get_engine(
            engine_name=self.config.engine,
            languages=self.config.languages,
            gpu=self.config.gpu,
        )
        self.report_dir = report_dir or settings.REPORT_DIR
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.evaluator = ConfidenceEvaluator(threshold=self.config.confidence_threshold)
        self.extractors: List[BaseFieldExtractor] = [
            StudentNameExtractor(),
            RollNumberExtractor(),
            DegreeExtractor(),
            InstitutionExtractor(),
            DateExtractor(),
            GradeExtractor(),
            CertificateIdExtractor(),
        ]

    def process_document(
        self,
        document_id: str,
        image_or_path: Union[np.ndarray, Path, str],
        output_overlay_path: Optional[Path] = None,
    ) -> OCRResultDTO:
        """Run complete OCR and structured field extraction pipeline for a certificate document."""
        start_time = time.perf_counter()

        # Load image array if path was provided
        if isinstance(image_or_path, (str, Path)):
            img_path = Path(image_or_path)
            if not img_path.exists():
                raise FileNotFoundError(f"Certificate image not found: {img_path}")
            image = cv2.imread(str(img_path))
            if image is None:
                raise ValueError(f"Failed to decode image at: {img_path}")
        elif isinstance(image_or_path, np.ndarray):
            image = image_or_path
        else:
            raise TypeError(f"Invalid image type: {type(image_or_path)}")

        # Step 1: Detect and extract tokens
        tokens = self.engine.extract_tokens(image)
        self.last_tokens = tokens
        raw_text = " ".join(t.text for t in tokens).strip()

        # Step 2: Segment into reading-order lines
        lines = SpatialLayoutAnalyzer.group_tokens_into_lines(tokens)

        # Step 3: Run all field extractors
        extracted_fields: Dict[str, ExtractedField] = {}
        for extractor in self.extractors:
            try:
                # CertificateIdExtractor supports passing image for QR decoding
                if isinstance(extractor, CertificateIdExtractor):
                    field = extractor.extract(lines, tokens, image=image)
                else:
                    field = extractor.extract(lines, tokens)

                if field is not None:
                    extracted_fields[extractor.field_name] = field
            except Exception as exc:
                logger.warning(
                    "Extractor '%s' failed on document %s: %s",
                    extractor.field_name,
                    document_id,
                    exc,
                )

        # Step 4: Evaluate confidence scores and flag below threshold
        cert_fields, field_dtos, low_conf_flag, avg_conf = self.evaluator.evaluate_and_map_fields(
            extracted_fields, tokens
        )

        # Step 5: Generate annotated visual overlay if configured
        overlay_path_str: Optional[str] = None
        if self.config.generate_overlay:
            overlay_file = output_overlay_path or (
                self.report_dir / f"{document_id}_ocr_overlay.png"
            )
            OCRVisualizer.render_overlay(
                image=image,
                extracted_fields=extracted_fields,
                tokens=tokens,
                output_path=overlay_file,
            )
            overlay_path_str = str(overlay_file.resolve())

        execution_ms = (time.perf_counter() - start_time) * 1000.0

        return OCRResultDTO(
            document_id=document_id,
            engine_used=self.engine.engine_name,
            average_ocr_confidence=avg_conf,
            low_confidence_flag=low_conf_flag,
            raw_extracted_text=raw_text,
            token_count=len(tokens),
            fields=cert_fields,
            field_details=field_dtos,
            overlay_path=overlay_path_str,
            execution_time_ms=execution_ms,
        )

    def extract_to_pipeline_output(
        self,
        document_id: str,
        image_or_path: Union[np.ndarray, Path, str],
    ) -> OCROutput:
        """Run OCR and return canonical SPEC-02 OCROutput contract."""
        tokens = self.engine.extract_tokens(image_or_path)
        result = self.process_document(document_id, image_or_path)
        return result.to_pipeline_output(tokens=tokens)


_ocr_service_instance: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """FastAPI dependency injection provider for OCRService."""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    return _ocr_service_instance
