"""Unit tests for feature importance analysis (Phase 09 - TC-MOD-03).

Tests Gini importance ranking, local per-certificate contribution scoring,
and importance bar chart plotting.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
from ml.scripts.preprocess_features import FEATURE_NAMES
from sklearn.ensemble import RandomForestClassifier

from app.modules.ml_classifier.feature_importance import FeatureImportanceAnalyzer


@pytest.fixture
def trained_rf():
    """Fixture returning a fitted random forest model on synthetic features."""
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 1, size=(50, 22))
    # Make feature 13 (ela_score) and 14 (copy_move_score) strong predictors
    y = ((x[:, 13] < 0.5) | (x[:, 14] < 0.5)).astype(int)

    rf = RandomForestClassifier(n_estimators=20, random_state=42)
    rf.fit(x, y)
    return rf


def test_global_feature_importance(trained_rf):
    """Verify global feature ranking produces valid importance items sorted descending."""
    analyzer = FeatureImportanceAnalyzer(model=trained_rf)
    ranking = analyzer.get_global_importance(top_k=5)

    assert len(ranking) == 5
    # Must be sorted descending
    for i in range(len(ranking) - 1):
        assert ranking[i]["importance_score"] >= ranking[i + 1]["importance_score"]

    top_feature_names = [item["feature_name"] for item in ranking]
    assert all(name in FEATURE_NAMES for name in top_feature_names)


def test_local_sample_contributions(trained_rf):
    """Verify local per-certificate anomaly score contribution calculation."""
    analyzer = FeatureImportanceAnalyzer(model=trained_rf)

    # Anomaly sample with very low scores on ela and copy-move
    sample = np.ones(22, dtype=np.float32)
    sample[13] = 0.1  # ela_score anomalous
    sample[14] = 0.05  # copy_move anomalous

    contributions = analyzer.calculate_local_contributions(features=sample, top_k=5)

    assert len(contributions) == 5
    top_names = [c["feature_name"] for c in contributions]
    # ela_score or copy_move_score should be among top anomaly contributors
    assert "ela_score" in top_names or "copy_move_score" in top_names

    for c in contributions:
        assert "feature_name" in c
        assert "feature_value" in c
        assert "contribution_score" in c
        assert "rank" in c


def test_plot_feature_importance(trained_rf):
    """Verify feature importance plot generation to disk."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "test_importance.png"
        analyzer = FeatureImportanceAnalyzer(model=trained_rf)

        res_path = analyzer.plot_feature_importance(output_path=out_file, top_k=10)
        assert res_path.exists()
        assert res_path.stat().st_size > 0
