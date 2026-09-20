"""Baseline ML inference engine for Phase 09.

Provides fast, thread-safe model loading, input validation, feature scaling,
and sub-20ms probability inference for academic certificate verification.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_MODELS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "ml" / "models"


class BaselineInferenceEngine:
    """Low-latency inference engine wrapping trained scikit-learn models and preprocessors."""

    def __init__(
        self,
        model_path: Path | str | None = None,
        scaler_path: Path | str | None = None,
        model_version: str = "1.0.0",
        threshold: float = 0.5,
    ) -> None:
        self.models_dir = DEFAULT_MODELS_DIR
        self.model_path = (
            Path(model_path) if model_path else self.models_dir / "baseline_model_v1.joblib"
        )
        self.scaler_path = (
            Path(scaler_path) if scaler_path else self.models_dir / "feature_scaler.joblib"
        )
        self.model_version = model_version
        self.threshold = threshold

        self.model: Any = None
        self.scaler: Any = None
        self.model_type: str = "Unknown"
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load serialized model and feature scaler from disk if available."""
        if self.model_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.model_type = type(self.model).__name__
                logger.info("Loaded baseline model: %s from %s", self.model_type, self.model_path)
            except Exception as e:
                logger.warning("Failed loading model from %s: %s", self.model_path, e)
                self.model = None

        if self.scaler_path.exists():
            try:
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded feature scaler from %s", self.scaler_path)
            except Exception as e:
                logger.warning("Failed loading scaler from %s: %s", self.scaler_path, e)
                self.scaler = None

    def is_ready(self) -> bool:
        """Check if model artifact is successfully loaded and ready for inference."""
        return self.model is not None

    def predict_single(
        self,
        features: np.ndarray | list[float],
    ) -> tuple[float, str, float, float]:
        """Perform inference on a single 22-dimensional feature vector.

        Returns:
            tuple of (manipulation_probability, predicted_class, confidence, latency_ms)
        """
        arr = np.asarray(features, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        if arr.shape[1] != 22:
            raise ValueError(f"Expected 22 features, but received {arr.shape[1]}")

        start_time = time.perf_counter()

        if self.model is None:
            # Graceful fallback: heuristic rule-based score if model is not loaded yet
            # Uses average of key anomaly scores (forensics, consistency)
            logger.warning("Model not loaded; falling back to heuristic inference.")
            # e.g., indices 13 (ela_score), 14 (copy_move), 16 (noise), 8 (baseline_alignment)
            heuristic_prob = float(np.clip(np.mean([arr[0, 13], arr[0, 14], arr[0, 16]]), 0.0, 1.0))
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            predicted_class = "manipulated" if heuristic_prob >= self.threshold else "authentic"
            confidence = abs(heuristic_prob - 0.5) * 2.0
            return heuristic_prob, predicted_class, confidence, latency_ms

        x_input = arr
        # Apply scaler if loaded and model is not tree-based (Linear / Logistic / SVM)
        if self.scaler is not None and self.model_type in [
            "LogisticRegression",
            "SVC",
            "SGDClassifier",
        ]:
            x_input = self.scaler.transform(x_input)

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(x_input)[0]
            # Assumes class 1 is manipulated
            prob_manipulated = float(probs[1]) if len(probs) > 1 else float(probs[0])
        elif hasattr(self.model, "decision_function"):
            df_val = self.model.decision_function(x_input)[0]
            # Sigmoid conversion
            prob_manipulated = float(1.0 / (1.0 + np.exp(-df_val)))
        else:
            pred = self.model.predict(x_input)[0]
            prob_manipulated = 1.0 if pred == 1 else 0.0

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        predicted_class = "manipulated" if prob_manipulated >= self.threshold else "authentic"
        confidence = float(abs(prob_manipulated - 0.5) * 2.0)

        return prob_manipulated, predicted_class, confidence, latency_ms

    def predict_batch(
        self,
        features_batch: np.ndarray,
    ) -> list[tuple[float, str, float]]:
        """Perform batch inference on an (N, 22) array of features."""
        arr = np.asarray(features_batch, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[1] != 22:
            raise ValueError(f"Expected array of shape (N, 22), got {arr.shape}")

        if self.model is None:
            results = []
            for row in arr:
                prob = float(np.clip(np.mean([row[13], row[14], row[16]]), 0.0, 1.0))
                p_class = "manipulated" if prob >= self.threshold else "authentic"
                conf = abs(prob - 0.5) * 2.0
                results.append((prob, p_class, conf))
            return results

        x_input = arr
        if self.scaler is not None and self.model_type in [
            "LogisticRegression",
            "SVC",
            "SGDClassifier",
        ]:
            x_input = self.scaler.transform(x_input)

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(x_input)
            manip_probs = probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]
        else:
            preds = self.model.predict(x_input)
            manip_probs = np.where(preds == 1, 1.0, 0.0)

        results = []
        for p in manip_probs:
            prob = float(p)
            p_class = "manipulated" if prob >= self.threshold else "authentic"
            conf = float(abs(prob - 0.5) * 2.0)
            results.append((prob, p_class, conf))
        return results
