"""Phase 09: ML Baseline Classifier Module.

Provides tabular feature extraction, classical ML inference, feature importance
analysis, and high-level service integration for fake academic certificate detection.
"""

from app.modules.ml_classifier.feature_extractor import TabularFeatureExtractor
from app.modules.ml_classifier.feature_importance import FeatureImportanceAnalyzer
from app.modules.ml_classifier.inference_engine import BaselineInferenceEngine
from app.modules.ml_classifier.service import BaselineMLService

__all__ = [
    "BaselineInferenceEngine",
    "BaselineMLService",
    "FeatureImportanceAnalyzer",
    "TabularFeatureExtractor",
]
