"""Multimodal score fusion and decision subsystem."""

from app.modules.score_fusion.early_fusion import (
    MultimodalFusionMLP,
    concatenate_features,
)
from app.modules.score_fusion.late_fusion import WeightedLateFusion
from app.modules.score_fusion.meta_classifier import StackingMetaClassifier
from app.modules.score_fusion.service import ScoreFusionService
from app.modules.score_fusion.verdict_engine import VerdictEngine
from app.modules.score_fusion.veto_rules import InstitutionalVetoEngine
from app.schemas.decision import (
    FinalVerificationDecision,
    SubScoresBreakdown,
    VerificationVerdict,
)

__all__ = [
    "ScoreFusionService",
    "WeightedLateFusion",
    "StackingMetaClassifier",
    "MultimodalFusionMLP",
    "InstitutionalVetoEngine",
    "VerdictEngine",
    "FinalVerificationDecision",
    "SubScoresBreakdown",
    "VerificationVerdict",
    "concatenate_features",
]
