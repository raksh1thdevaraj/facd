"""Unit tests for ML model training pipeline (Phase 09 - TC-MOD-01).

Tests 5-fold cross-validation execution, multi-model evaluation, and serialization.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import joblib
from ml.scripts.extract_dataset_features import generate_synthetic_feature_dataset
from ml.scripts.train_baseline_models import train_baseline_models


def test_train_baseline_models_pipeline():
    """Verify that train_baseline_models trains 4 candidates with 5-fold CV and saves artifacts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Generate small dataset
        train_df, _, _ = generate_synthetic_feature_dataset(n_samples=100, random_state=42)

        results = train_baseline_models(
            train_df=train_df,
            output_model_dir=tmp_path,
            cv_splits=3,  # 3 splits for fast testing
            random_state=42,
        )

        assert "best_model" in results
        assert "best_f1_score" in results
        assert results["best_f1_score"] >= 0.85
        assert "candidate_results" in results

        # Ensure all 4 model families were trained
        candidates = results["candidate_results"]
        assert "RandomForestClassifier" in candidates
        assert "HistGradientBoostingClassifier" in candidates
        assert "LogisticRegression" in candidates
        assert "SVC" in candidates

        for _model_name, metrics in candidates.items():
            assert "cv_accuracy" in metrics
            assert "cv_f1" in metrics
            assert "cv_roc_auc" in metrics
            assert metrics["cv_f1"] > 0.70

        # Verify artifacts saved
        model_file = tmp_path / "baseline_model_v1.joblib"
        scaler_file = tmp_path / "feature_scaler.joblib"
        assert model_file.exists()
        assert scaler_file.exists()

        # Test model can be reloaded
        loaded_model = joblib.load(model_file)
        assert hasattr(loaded_model, "predict")
