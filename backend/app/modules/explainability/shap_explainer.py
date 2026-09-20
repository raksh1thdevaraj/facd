"""SHAP TreeExplainer for local tabular feature attribution."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional, Union

import joblib
import numpy as np

try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from app.modules.ml_classifier.feature_importance import FEATURE_DOMAIN_GROUPS
from app.schemas.explainability import FeatureAttribution
from app.schemas.ml_prediction import FEATURE_NAMES

logger = logging.getLogger(__name__)


class SHAPTabularExplainer:
    """Computes local SHAP feature attributions for baseline ML model predictions."""

    def __init__(
        self,
        model: Optional[Any] = None,
        model_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self.model = model
        self.explainer: Optional[Any] = None

        if self.model is None and model_path:
            p = Path(model_path)
            if p.exists():
                try:
                    loaded = joblib.load(p)
                    self.model = loaded.get("model", loaded) if isinstance(loaded, dict) else loaded
                except Exception as e:
                    logger.warning("Failed loading model from %s for SHAP: %s", p, e)

        if SHAP_AVAILABLE and self.model is not None and hasattr(self.model, "estimators_"):
            try:
                self.explainer = shap.TreeExplainer(self.model)
                logger.info("Initialized SHAP TreeExplainer successfully.")
            except Exception as e:
                logger.warning(
                    "Failed creating SHAP TreeExplainer: %s. Using heuristic attribution.", e
                )

    def explain(
        self,
        feature_vector: np.ndarray,
        feature_names: Optional[List[str]] = None,
        top_k: int = 6,
    ) -> List[FeatureAttribution]:
        """Compute local feature attributions, ranked by absolute impact descending."""
        names = feature_names or FEATURE_NAMES
        feats = np.nan_to_num(np.asarray(feature_vector, dtype=np.float32).flatten(), nan=0.0)
        if len(feats) != len(names):
            feats = np.resize(feats, len(names))

        shap_vals: Optional[np.ndarray] = None
        if self.explainer is not None:
            try:
                raw_shap = self.explainer.shap_values(feats.reshape(1, -1))
                # For binary classification: class 1 (manipulated)
                if isinstance(raw_shap, list) and len(raw_shap) > 1:
                    shap_vals = raw_shap[1][0]
                elif isinstance(raw_shap, np.ndarray) and raw_shap.ndim == 3:
                    shap_vals = raw_shap[0, :, 1]
                elif isinstance(raw_shap, np.ndarray) and raw_shap.ndim == 2:
                    shap_vals = raw_shap[0]
            except Exception as e:
                logger.warning("TreeExplainer execution failed: %s. Using fallback.", e)

        # Heuristic fallback if SHAP execution unavailable
        if shap_vals is None:
            shap_vals = np.zeros(len(names), dtype=np.float32)
            for i, name in enumerate(names):
                val = float(feats[i])
                # Anomaly deviations push towards manipulation risk
                if "score" in name or "confidence" in name:
                    shap_vals[i] = (0.75 - val) * 0.4
                elif "count" in name:
                    shap_vals[i] = val * 0.25
                elif "deviation" in name or "flag" in name:
                    shap_vals[i] = val * 0.35

        abs_total = float(np.sum(np.abs(shap_vals))) or 1e-6
        attributions: List[FeatureAttribution] = []

        for i, name in enumerate(names):
            s_val = float(shap_vals[i])
            impact_pct = (abs(s_val) / abs_total) * 100.0
            direction = "INCREASES_RISK" if s_val > 0.0 else "DECREASES_RISK"
            domain = FEATURE_DOMAIN_GROUPS.get(name, "General")

            attributions.append(
                FeatureAttribution(
                    feature_name=name,
                    domain_group=domain,
                    feature_value=round(float(feats[i]), 4),
                    shap_value=round(s_val, 4),
                    impact_percentage=round(impact_pct, 1),
                    direction=direction,
                )
            )

        # Sort descending by absolute SHAP impact
        attributions.sort(key=lambda a: abs(a.shap_value), reverse=True)
        return attributions[:top_k]
