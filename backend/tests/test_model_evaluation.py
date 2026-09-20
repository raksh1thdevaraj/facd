"""Unit tests for ML model evaluation (Phase 09 - TC-MOD-02).

Tests held-out test evaluation achieving accuracy >= 0.85 and F1 >= 0.85,
confusion matrix calculation, and diagnostic ROC curve plotting.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ml.scripts.evaluate_baseline import evaluate_baseline_model
from ml.scripts.extract_dataset_features import generate_synthetic_feature_dataset
from ml.scripts.train_baseline_models import train_baseline_models


def test_evaluate_baseline_model_metrics():
    """Verify evaluation generates metrics meeting specification and generates plots."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        models_dir = tmp_path / "models"
        reports_dir = tmp_path / "reports"

        train_df, _, test_df = generate_synthetic_feature_dataset(n_samples=120, random_state=42)

        # Train model first
        train_baseline_models(train_df=train_df, output_model_dir=models_dir, cv_splits=3)

        model_path = models_dir / "baseline_model_v1.joblib"
        scaler_path = models_dir / "feature_scaler.joblib"

        # Evaluate model
        metrics = evaluate_baseline_model(
            model_path=model_path,
            scaler_path=scaler_path,
            test_df=test_df,
            reports_dir=reports_dir,
        )

        assert metrics["accuracy"] >= 0.85
        assert metrics["f1_score"] >= 0.85
        assert metrics["roc_auc"] >= 0.85
        assert metrics["meets_specification"] is True

        cm = metrics["confusion_matrix"]
        assert "true_negatives" in cm
        assert "false_positives" in cm
        assert "false_negatives" in cm
        assert "true_positives" in cm

        # Verify saved files
        assert (reports_dir / "baseline_metrics.json").exists()
        assert (reports_dir / "baseline_confusion_matrix.png").exists()
        assert (reports_dir / "baseline_roc_curve.png").exists()

        # Validate json content
        with open(reports_dir / "baseline_metrics.json") as f:
            saved_json = json.load(f)
            assert saved_json["accuracy"] == metrics["accuracy"]
            assert saved_json["f1_score"] == metrics["f1_score"]
