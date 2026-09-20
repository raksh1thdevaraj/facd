"""Explainability, feature attributions, and visual evidence overlay subsystem."""

from app.modules.explainability.coordinate_mapper import CoordinateMapper
from app.modules.explainability.nlg_generator import NLGExplanationGenerator
from app.modules.explainability.service import ExplainabilityService
from app.modules.explainability.shap_explainer import SHAPTabularExplainer
from app.modules.explainability.unified_overlay import UnifiedOverlayRenderer
from app.schemas.explainability import (
    ExplainabilityReport,
    FeatureAttribution,
    FindingBullet,
    FindingCategory,
    FindingSeverity,
    InteractiveOverlayPayload,
    NormalizedBox,
    UnifiedAnomalyBox,
)

__all__ = [
    "CoordinateMapper",
    "SHAPTabularExplainer",
    "NLGExplanationGenerator",
    "UnifiedOverlayRenderer",
    "ExplainabilityService",
    "FindingSeverity",
    "FindingCategory",
    "FindingBullet",
    "FeatureAttribution",
    "NormalizedBox",
    "UnifiedAnomalyBox",
    "InteractiveOverlayPayload",
    "ExplainabilityReport",
]
