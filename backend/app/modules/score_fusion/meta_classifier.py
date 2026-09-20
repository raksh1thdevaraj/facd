"""Stacking Meta-Classifier for multimodal probability blending."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Union

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


class StackingMetaClassifier:
    """Stacking meta-learner that predicts authenticity from multi-branch predictions."""

    FEATURE_NAMES: List[str] = [
        "visual_fake_prob",
        "tabular_fake_prob",
        "forensic_score",
        "text_consistency_score",
        "template_score",
    ]

    def __init__(self, model_path: Union[str, Path, None] = None) -> None:
        self.model = LogisticRegression(C=1.0, max_iter=200, random_state=42)
        self.is_fitted = False

        if model_path:
            self.load(model_path)
        else:
            # Initialize with default weights (authentic when fake probs low & scores high)
            # 1 = Authentic, 0 = Manipulated
            # Features: [p_vis_fake, p_tab_fake, s_forensic, s_text, s_template]
            X_init = np.array(
                [
                    [0.05, 0.05, 0.95, 0.95, 0.90],  # clearly authentic
                    [0.90, 0.85, 0.20, 0.30, 0.10],  # clearly fake
                    [0.30, 0.40, 0.70, 0.75, 0.60],  # somewhat authentic
                    [0.70, 0.65, 0.40, 0.45, 0.35],  # somewhat fake
                ],
                dtype=np.float32,
            )
            y_init = np.array([1, 0, 1, 0], dtype=np.int32)
            self.model.fit(X_init, y_init)
            self.is_fitted = True

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit meta-learner on out-of-fold branch predictions and authenticity labels."""
        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.asarray(y, dtype=np.int32)
        self.model.fit(X_arr, y_arr)
        self.is_fitted = True

    def predict_authenticity(self, features: Union[np.ndarray, List[float]]) -> float:
        """Predict probability that the certificate is authentic [0.0 = Fake, 1.0 = Authentic]."""
        arr = np.asarray(features, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.shape[1] != 5:
            raise ValueError(f"Expected 5 meta-features, got {arr.shape[1]}")

        probs = self.model.predict_proba(arr)
        # Class 1 is Authentic
        auth_prob = float(probs[0, 1]) if probs.shape[1] > 1 else float(probs[0, 0])
        return max(0.0, min(1.0, auth_prob))

    def save(self, output_path: Union[str, Path]) -> Path:
        """Serialize meta-classifier artifact."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "is_fitted": self.is_fitted}, path)
        return path

    def load(self, model_path: Union[str, Path]) -> None:
        """Load serialized meta-classifier artifact."""
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Meta-classifier artifact not found at {path}")
        data = joblib.load(path)
        if isinstance(data, dict):
            self.model = data.get("model", self.model)
            self.is_fitted = data.get("is_fitted", True)
        else:
            self.model = data
            self.is_fitted = True
