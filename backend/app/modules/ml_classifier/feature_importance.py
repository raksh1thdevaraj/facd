"""Feature importance analysis and local anomaly explanations for Phase 09.

Provides Gini / permutation importance extraction, domain group mapping,
per-certificate anomaly contribution scoring, and diagnostic plotting.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from app.schemas.ml_prediction import FEATURE_NAMES, FeatureImportanceItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FEATURE_DOMAIN_GROUPS: dict[str, str] = {
    "file_size_kb": "Ingestion & Metadata",
    "has_exif": "Ingestion & Metadata",
    "software_editing_flag": "Ingestion & Metadata",
    "aspect_ratio_deviation": "Ingestion & Metadata",
    "ocr_mean_confidence": "OCR & Text Quality",
    "ocr_min_confidence": "OCR & Text Quality",
    "flagged_field_count": "OCR & Text Quality",
    "missing_critical_fields_count": "OCR & Text Quality",
    "baseline_alignment_score": "Text Consistency",
    "font_size_consistency_score": "Text Consistency",
    "stroke_weight_score": "Text Consistency",
    "character_spacing_score": "Text Consistency",
    "logical_consistency_score": "Text Consistency",
    "ela_score": "Image Forensics",
    "copy_move_score": "Image Forensics",
    "cloned_regions_count": "Image Forensics",
    "noise_inconsistency_score": "Image Forensics",
    "template_ssim_score": "Template & Record Matching",
    "template_feature_score": "Template & Record Matching",
    "seal_match_score": "Template & Record Matching",
    "record_found_flag": "Template & Record Matching",
    "record_match_score": "Template & Record Matching",
}


def extract_feature_importances(
    model: Any,
    feature_names: list[str] | None = None,
) -> list[FeatureImportanceItem]:
    """Extract global Gini or coefficient feature importances and rank them descending."""
    names = feature_names or FEATURE_NAMES

    if model is not None and hasattr(model, "feature_importances_"):
        raw_importances = model.feature_importances_
    elif model is not None and hasattr(model, "coef_"):
        raw_importances = np.abs(model.coef_[0])
    else:
        raw_importances = np.ones(len(names)) / len(names)

    total = np.sum(raw_importances)
    norm_importances = raw_importances / total if total > 0 else raw_importances

    sorted_indices = np.argsort(norm_importances)[::-1]

    items: list[FeatureImportanceItem] = []
    for rank, idx in enumerate(sorted_indices, start=1):
        fname = names[idx]
        group = FEATURE_DOMAIN_GROUPS.get(fname, "General")
        items.append(
            FeatureImportanceItem(
                feature_name=fname,
                importance_score=round(float(norm_importances[idx]), 4),
                rank=rank,
                domain_group=group,
            )
        )
    return items


def compute_local_contributions(
    model: Any,
    feature_vector: np.ndarray,
    feature_names: list[str] | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Calculate local feature contribution weights explaining why certificate was flagged."""
    names = feature_names or FEATURE_NAMES
    global_items = extract_feature_importances(model, names)
    global_weights = {item.feature_name: item.importance_score for item in global_items}

    canonical_genuine = {
        "file_size_kb": 1200.0,
        "has_exif": 1.0,
        "software_editing_flag": 0.0,
        "aspect_ratio_deviation": 0.0,
        "ocr_mean_confidence": 0.95,
        "ocr_min_confidence": 0.90,
        "flagged_field_count": 0.0,
        "missing_critical_fields_count": 0.0,
        "baseline_alignment_score": 1.0,
        "font_size_consistency_score": 1.0,
        "stroke_weight_score": 1.0,
        "character_spacing_score": 1.0,
        "logical_consistency_score": 1.0,
        "ela_score": 1.0,
        "copy_move_score": 1.0,
        "cloned_regions_count": 0.0,
        "noise_inconsistency_score": 1.0,
        "template_ssim_score": 1.0,
        "template_feature_score": 1.0,
        "seal_match_score": 1.0,
        "record_found_flag": 1.0,
        "record_match_score": 1.0,
    }

    vec = np.asarray(feature_vector).flatten()
    contributions: list[dict[str, Any]] = []

    for i, name in enumerate(names):
        val = float(vec[i]) if i < len(vec) else 0.0
        expected = canonical_genuine.get(name, 1.0)
        weight = global_weights.get(name, 1.0 / len(names))

        if name in (
            "software_editing_flag",
            "cloned_regions_count",
            "flagged_field_count",
            "missing_critical_fields_count",
        ):
            anomaly_delta = max(0.0, val - expected)
        elif name == "file_size_kb":
            anomaly_delta = max(0.0, 1.0 - (val / 1200.0))
        elif name == "aspect_ratio_deviation":
            anomaly_delta = val * 2.0
        else:
            anomaly_delta = max(0.0, expected - val)

        score = round(float(anomaly_delta * weight), 4)
        contributions.append(
            {
                "feature_name": name,
                "feature_value": val,
                "importance_score": score,
                "contribution_score": score,
                "domain_group": FEATURE_DOMAIN_GROUPS.get(name, "General"),
            }
        )

    # Sort descending by contribution score
    contributions.sort(key=lambda item: item["contribution_score"], reverse=True)
    for rank, item in enumerate(contributions, start=1):
        item["rank"] = rank

    return contributions[:top_k]


def plot_feature_importance(
    items: list[FeatureImportanceItem],
    output_path: Path,
    top_n: int = 15,
) -> Path:
    """Render horizontal bar chart of top N feature importances."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    top_items = items[:top_n][::-1]

    names = [it.feature_name for it in top_items]
    scores = [it.importance_score for it in top_items]

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(names, scores, color="#2b5c8f", edgecolor="none", height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 0.003,
            bar.get_y() + bar.get_height() / 2.0,
            f"{w:.3f}",
            va="center",
            fontsize=9,
            color="#333333",
        )

    ax.set_xlabel("Relative Importance Score", fontweight="bold")
    ax.set_title(
        f"Top {top_n} Forensic & Typographical Features (Random Forest)",
        pad=15,
        fontweight="bold",
    )
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


class FeatureImportanceAnalyzer:
    """Analyzer class wrapping global and local importance routines."""

    def __init__(self, model: Any = None) -> None:
        self.model = model

    def get_global_importance(self, top_k: int = 22) -> list[dict[str, Any]]:
        """Return top_k global feature importance dictionaries."""
        items = extract_feature_importances(self.model)
        return [item.model_dump() for item in items[:top_k]]

    def calculate_local_contributions(
        self,
        features: np.ndarray,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Calculate local feature contribution scores for a single certificate."""
        return compute_local_contributions(self.model, features, top_k=top_k)

    def plot_feature_importance(
        self,
        output_path: Path,
        top_k: int = 15,
    ) -> Path:
        """Generate and save feature importance chart."""
        items = extract_feature_importances(self.model)
        return plot_feature_importance(items, output_path, top_n=top_k)
