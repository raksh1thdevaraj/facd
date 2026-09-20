"""Production orchestrator service for multimodal score fusion and verdict generation."""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
import torch
from sqlalchemy.orm import Session

from app.models.report import VerificationReportModel
from app.modules.score_fusion.early_fusion import (
    MultimodalFusionMLP,
    concatenate_features,
)
from app.modules.score_fusion.late_fusion import WeightedLateFusion
from app.modules.score_fusion.meta_classifier import StackingMetaClassifier
from app.modules.score_fusion.verdict_engine import VerdictEngine
from app.modules.score_fusion.veto_rules import InstitutionalVetoEngine
from app.schemas.decision import FinalVerificationDecision
from app.schemas.pipeline import ScoreFusionOutput
from app.schemas.template_matching import TierStatus

logger = logging.getLogger(__name__)


class ScoreFusionService:
    """Production service coordinating multimodal fusion, veto overrides, and final decisions."""

    def __init__(
        self,
        meta_model_path: Optional[Union[str, Path]] = None,
        early_mlp_path: Optional[Union[str, Path]] = None,
        default_fusion_method: str = "late_fusion",
    ) -> None:
        self.default_fusion_method = default_fusion_method
        self.late_fusion = WeightedLateFusion()
        self.meta_classifier = StackingMetaClassifier(model_path=meta_model_path)
        self.early_mlp: Optional[MultimodalFusionMLP] = None

        if early_mlp_path and Path(early_mlp_path).exists():
            try:
                self.early_mlp = MultimodalFusionMLP()
                chk = torch.load(early_mlp_path, map_location="cpu")
                state = chk.get("state_dict", chk)
                self.early_mlp.load_state_dict(state)
                self.early_mlp.eval()
            except Exception as e:
                logger.warning("Could not load early fusion MLP from %s: %s", early_mlp_path, e)

    def fuse_and_decide(
        self,
        certificate_id: str,
        visual_fake_prob: float,
        tabular_fake_prob: float,
        forensic_score: float,
        text_consistency_score: float,
        template_score: float,
        tier_status: Union[str, TierStatus] = TierStatus.TIER_3_UNVERIFIED,
        record_found: bool = False,
        discrepancies: Optional[List[str]] = None,
        primary_reason: Optional[str] = None,
        visual_embedding: Optional[np.ndarray] = None,
        tabular_vector: Optional[np.ndarray] = None,
        fusion_method: Optional[str] = None,
        db_session: Optional[Session] = None,
    ) -> FinalVerificationDecision:
        """Run multimodal score fusion, apply veto overrides, and generate final verdict."""
        start_time = time.perf_counter()
        method = fusion_method or self.default_fusion_method

        # 1. Compute baseline late fusion sub-scores and factors
        (
            late_auth_score,
            _late_risk,
            sub_scores,
            contributing_factors,
        ) = self.late_fusion.blend(
            visual_fake_prob=visual_fake_prob,
            tabular_fake_prob=tabular_fake_prob,
            forensic_score=forensic_score,
            text_consistency_score=text_consistency_score,
            template_score=template_score,
        )

        # 2. Compute raw authenticity score based on chosen method
        if method == "stacking_meta_learner":
            meta_features = [
                float(visual_fake_prob),
                float(tabular_fake_prob),
                float(forensic_score),
                float(text_consistency_score),
                float(template_score),
            ]
            raw_score = self.meta_classifier.predict_authenticity(meta_features)
        elif (
            method == "early_fusion_mlp"
            and visual_embedding is not None
            and tabular_vector is not None
        ):
            if self.early_mlp is not None:
                fused_534d = concatenate_features(visual_embedding, tabular_vector)
                prob_fake = self.early_mlp.predict_probability(fused_534d)
                raw_score = max(0.0, min(1.0, 1.0 - prob_fake))
            else:
                raw_score = late_auth_score
        else:
            raw_score = late_auth_score

        # 3. Apply authoritative institutional veto overrides
        adjusted_score, veto_applied, veto_reason = InstitutionalVetoEngine.apply_vetoes(
            raw_authenticity_score=raw_score,
            tier_status=tier_status,
            record_found=record_found,
            discrepancies=discrepancies,
            primary_reason=primary_reason,
        )

        # 4. Map final score to Verdict and Risk Band
        verdict, risk_band, confidence, rationale = VerdictEngine.evaluate(
            authenticity_score=adjusted_score,
            veto_applied=veto_applied,
            veto_reason=veto_reason,
        )

        overall_risk_score = (1.0 - adjusted_score) * 100.0
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        decision = FinalVerificationDecision(
            certificate_id=certificate_id,
            overall_authenticity_score=round(adjusted_score, 4),
            overall_risk_score=round(overall_risk_score, 2),
            risk_band=risk_band,
            verdict=verdict,
            confidence=round(confidence, 4),
            sub_scores=sub_scores,
            tier_status=tier_status.value
            if isinstance(tier_status, TierStatus)
            else str(tier_status),
            veto_applied=veto_applied,
            veto_reason=veto_reason,
            contributing_factors=contributing_factors,
            summary_rationale=rationale,
            fusion_method=method,
            latency_ms=round(latency_ms, 2),
        )

        # 5. Persist to DB if session provided
        if db_session is not None:
            try:
                db_record = VerificationReportModel(
                    id=str(uuid.uuid4()),
                    certificate_id=certificate_id,
                    overall_score=decision.overall_authenticity_score,
                    risk_score=decision.overall_risk_score,
                    verdict=decision.verdict.value,
                    confidence_score=decision.confidence,
                    sub_scores_json=decision.sub_scores.model_dump(),
                    veto_applied=decision.veto_applied,
                    veto_reason=decision.veto_reason,
                    contributing_factors_json=[
                        f.model_dump() for f in decision.contributing_factors
                    ],
                    execution_time_ms=decision.latency_ms,
                )
                db_session.add(db_record)
                db_session.commit()
                db_session.refresh(db_record)
            except Exception as e:
                logger.error(
                    "Failed persisting verification report to DB for cert %s: %s", certificate_id, e
                )
                db_session.rollback()

        return decision

    def get_pipeline_output(self, **kwargs: Any) -> ScoreFusionOutput:
        """Convenience method returning canonical SPEC-02 pipeline output contract."""
        decision = self.fuse_and_decide(**kwargs)
        return decision.to_score_fusion_output()
