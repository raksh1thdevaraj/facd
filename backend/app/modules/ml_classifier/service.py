"""Baseline ML Service for Phase 09.

Orchestrates tabular feature extraction, model inference, local feature contribution
explanations, optional database persistence, and conversion to canonical SPEC-02
MLInferenceOutput schema.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.ml_prediction import MLPredictionModel
from app.modules.ml_classifier.feature_extractor import TabularFeatureExtractor
from app.modules.ml_classifier.feature_importance import FeatureImportanceAnalyzer
from app.modules.ml_classifier.inference_engine import BaselineInferenceEngine
from app.schemas.ml_prediction import (
    FeatureImportanceItem,
    FeatureVector,
    PredictionResult,
)
from app.schemas.pipeline import MLInferenceOutput

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BaselineMLService:
    """End-to-end service for Phase 09 ML baseline classification."""

    def __init__(
        self,
        model_path: Path | str | None = None,
        scaler_path: Path | str | None = None,
        threshold: float = 0.5,
    ) -> None:
        self.feature_extractor = TabularFeatureExtractor()
        self.inference_engine = BaselineInferenceEngine(
            model_path=model_path,
            scaler_path=scaler_path,
            threshold=threshold,
        )
        self.importance_analyzer = FeatureImportanceAnalyzer(
            model=self.inference_engine.model,
        )

    def classify_certificate(
        self,
        certificate_id: str,
        ingestion_data: Any = None,
        ocr_result: Any = None,
        text_consistency_result: Any = None,
        forensics_result: Any = None,
        template_result: Any = None,
        db_session: Session | None = None,
        top_k_contributions: int = 5,
    ) -> PredictionResult:
        """Extract features, run inference, calculate local contributions,

        and return full PredictionResult.
        """
        # 1. Extract 22-dimensional feature vector
        feat_vector: FeatureVector = self.feature_extractor.extract_from_upstream(
            ingestion_data=ingestion_data,
            ocr_result=ocr_result,
            text_consistency_result=text_consistency_result,
            forensics_result=forensics_result,
            template_result=template_result,
        )

        vector_array = feat_vector.to_array()

        # 2. Run inference
        manip_prob, pred_class, confidence, latency_ms = self.inference_engine.predict_single(
            vector_array
        )

        # 3. Calculate local feature contributions
        contributions = self.importance_analyzer.calculate_local_contributions(
            features=vector_array,
            top_k=top_k_contributions,
        )
        contrib_items = [FeatureImportanceItem(**c) for c in contributions]

        # 4. Construct PredictionResult
        result = PredictionResult(
            certificate_id=certificate_id,
            manipulation_probability=round(manip_prob, 4),
            predicted_class=pred_class,
            confidence=round(confidence, 4),
            feature_contributions=contrib_items,
            model_version=self.inference_engine.model_version,
            model_type=self.inference_engine.model_type,
            latency_ms=round(latency_ms, 2),
            feature_vector=feat_vector,
        )

        # 5. Persist to database if session provided
        if db_session is not None:
            try:
                db_record = MLPredictionModel(
                    id=str(uuid.uuid4()),
                    certificate_id=certificate_id,
                    manipulation_probability=result.manipulation_probability,
                    predicted_class=result.predicted_class,
                    confidence=result.confidence,
                    model_version=result.model_version,
                    execution_time_ms=result.latency_ms,
                    feature_vector_json=feat_vector.to_dict(),
                    feature_contributions_json=[c.model_dump() for c in contrib_items],
                )
                db_session.add(db_record)
                db_session.commit()
                db_session.refresh(db_record)
            except Exception as e:
                logger.error("Failed saving ML prediction to DB for cert %s: %s", certificate_id, e)
                db_session.rollback()

        return result

    def get_pipeline_output(
        self,
        certificate_id: str,
        ingestion_data: Any = None,
        ocr_result: Any = None,
        text_consistency_result: Any = None,
        forensics_result: Any = None,
        template_result: Any = None,
        db_session: Session | None = None,
    ) -> MLInferenceOutput:
        """Convenience method returning canonical SPEC-02 pipeline contract schema."""
        prediction = self.classify_certificate(
            certificate_id=certificate_id,
            ingestion_data=ingestion_data,
            ocr_result=ocr_result,
            text_consistency_result=text_consistency_result,
            forensics_result=forensics_result,
            template_result=template_result,
            db_session=db_session,
        )
        return prediction.to_pipeline_output()
