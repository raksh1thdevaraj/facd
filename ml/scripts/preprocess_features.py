"""Tabular feature preprocessing and normalization for Phase 09 ML Baseline.

Defines the authoritative 22-dimensional feature schema, StandardScaler serialization,
and dataset preparation utilities.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES: list[str] = [
    # Group 1: Document Metadata & Quality (4)
    "file_size_kb",
    "has_exif",
    "software_editing_flag",
    "aspect_ratio_deviation",
    # Group 2: OCR Confidence & Text Completeness (4)
    "ocr_mean_confidence",
    "ocr_min_confidence",
    "flagged_field_count",
    "missing_critical_fields_count",
    # Group 3: Text & Layout Consistency (5)
    "baseline_alignment_score",
    "font_size_consistency_score",
    "stroke_weight_score",
    "character_spacing_score",
    "logical_consistency_score",
    # Group 4: Forensic Anomaly Scores (4)
    "ela_score",
    "copy_move_score",
    "cloned_regions_count",
    "noise_inconsistency_score",
    # Group 5: Template & Registry Verification (5)
    "template_ssim_score",
    "template_feature_score",
    "seal_match_score",
    "record_found_flag",
    "record_match_score",
]


class TabularDataPreprocessor:
    """Preprocesses and normalizes 22-dimensional tabular certificate features."""

    def __init__(self, scaler: StandardScaler | None = None) -> None:
        self.scaler = scaler or StandardScaler()
        self.is_fitted = scaler is not None

    def fit(self, X: np.ndarray) -> TabularDataPreprocessor:
        """Fit scaler on training data matrix strictly."""
        self.scaler.fit(X)
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Standardize feature matrix."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor has not been fitted yet.")
        if X.ndim == 1:
            return self.scaler.transform(X.reshape(1, -1))
        return self.scaler.transform(X)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform."""
        return self.fit(X).transform(X)

    def save(self, filepath: str | Path) -> None:
        """Serialize fitted preprocessor to disk."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler, str(p))

    @classmethod
    def load(cls, filepath: str | Path) -> TabularDataPreprocessor:
        """Load fitted preprocessor from disk."""
        scaler = joblib.load(str(filepath))
        return cls(scaler=scaler)

    @staticmethod
    def extract_features_and_labels(
        df: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Extract (X, y, certificate_ids) from dataframe with 22 features."""
        # Check all features present or fill default 0.0
        missing = [f for f in FEATURE_NAMES if f not in df.columns]
        if missing:
            for f in missing:
                df[f] = 0.0

        x = df[FEATURE_NAMES].to_numpy(dtype=np.float32)
        y = (
            df["is_manipulated"].to_numpy(dtype=np.int32)
            if "is_manipulated" in df.columns
            else np.zeros(len(df), dtype=np.int32)
        )
        cert_ids = (
            df["certificate_id"].astype(str).tolist()
            if "certificate_id" in df.columns
            else [f"cert_{i}" for i in range(len(df))]
        )
        return x, y, cert_ids

    @staticmethod
    def prepare_datasets(
        data_dir: Path,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load or generate train/val/test DataFrames."""
        from ml.scripts.extract_dataset_features import (
            generate_synthetic_feature_dataset,
        )

        train_path = data_dir / "features_train.csv"
        val_path = data_dir / "features_val.csv"
        test_path = data_dir / "features_test.csv"

        if train_path.exists() and val_path.exists() and test_path.exists():
            return (
                pd.read_csv(train_path),
                pd.read_csv(val_path),
                pd.read_csv(test_path),
            )

        # Generate standard dataset if not existing
        train_df, val_df, test_df = generate_synthetic_feature_dataset(
            n_samples=600, random_state=42
        )

        data_dir.mkdir(parents=True, exist_ok=True)
        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)

        return train_df, val_df, test_df
