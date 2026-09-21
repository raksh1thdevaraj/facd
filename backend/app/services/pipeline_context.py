"""Pipeline Execution Context data bus for shared in-memory state across analysis stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from app.schemas.decision import FinalVerificationDecision
from app.schemas.explainability import ExplainabilityReport
from app.schemas.forensics import ForensicAnalysisResult
from app.schemas.ml_prediction import PredictionResult
from app.schemas.ocr import OCRResultDTO
from app.schemas.pipeline import CertificateFields, OCRToken
from app.schemas.report import FullVerificationReport
from app.schemas.template_matching import TemplateVerificationResult
from app.schemas.text_consistency import TextConsistencyResult
from app.schemas.visual_prediction import VisualPredictionResult


@dataclass
class PipelineExecutionContext:
    """Strongly-typed memory-resident context flowing across all pipeline stages."""

    certificate_id: str
    user_id: Optional[str] = None
    raw_image_path: Optional[Path] = None
    raw_image: Optional[np.ndarray] = None
    enhanced_image: Optional[np.ndarray] = None
    binarized_image: Optional[np.ndarray] = None
    ingestion_doc: Optional[Any] = None
    ocr_fields: Optional[CertificateFields] = None
    ocr_tokens: List[OCRToken] = field(default_factory=list)
    ocr_result: Optional[OCRResultDTO] = None
    text_result: Optional[TextConsistencyResult] = None
    forensic_result: Optional[ForensicAnalysisResult] = None
    template_result: Optional[TemplateVerificationResult] = None
    tier_result: Optional[str] = None
    tabular_features: Optional[np.ndarray] = None
    tabular_prediction: Optional[PredictionResult] = None
    visual_prediction: Optional[VisualPredictionResult] = None
    final_decision: Optional[FinalVerificationDecision] = None
    explainability_report: Optional[ExplainabilityReport] = None
    final_report: Optional[FullVerificationReport] = None
    stage_timings_ms: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
