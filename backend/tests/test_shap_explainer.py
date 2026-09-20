"""Unit tests for SHAPTabularExplainer local feature attributions."""

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.modules.explainability.shap_explainer import SHAPTabularExplainer
from app.schemas.explainability import FeatureAttribution
from app.schemas.ml_prediction import FEATURE_NAMES


def test_shap_explainer_with_rf_model():
    """Verify SHAP TreeExplainer computes feature attributions and ranks them (TC-EXP-01)."""
    # Create simple fitted Random Forest model
    X = np.random.randn(20, len(FEATURE_NAMES)).astype(np.float32)
    y = np.random.randint(0, 2, size=20)
    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X, y)

    explainer = SHAPTabularExplainer(model=rf)
    sample_feat = X[0]
    attributions = explainer.explain(sample_feat, top_k=5)

    assert len(attributions) == 5
    for attr in attributions:
        assert isinstance(attr, FeatureAttribution)
        assert attr.feature_name in FEATURE_NAMES
        assert attr.direction in ("INCREASES_RISK", "DECREASES_RISK")
        assert 0.0 <= attr.impact_percentage <= 100.0

    # Verify sorted by impact
    for i in range(len(attributions) - 1):
        assert abs(attributions[i].shap_value) >= abs(attributions[i + 1].shap_value)


def test_shap_explainer_fallback():
    """Verify fallback attribution when model is None or unweighted."""
    explainer = SHAPTabularExplainer(model=None)
    feats = np.array([1000.0, 1.0, 0.0, 0.05] + [0.8] * (len(FEATURE_NAMES) - 4), dtype=np.float32)
    attributions = explainer.explain(feats, top_k=6)

    assert len(attributions) == 6
    assert all(isinstance(a, FeatureAttribution) for a in attributions)
