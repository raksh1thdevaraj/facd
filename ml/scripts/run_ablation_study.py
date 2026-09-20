"""Feature ablation study script for Phase 09 ML Baseline.

Systematically trains baseline models omitting each feature group (domain-specific ablation)
to validate that multi-modal fusion of visual, text, forensics, and metadata signals outperforms
any individual feature subset (validates TC-MOD-05).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from ml.scripts.preprocess_features import FEATURE_NAMES, TabularDataPreprocessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT_DIR / "ml" / "configs" / "tabular_features.json"
DATA_DIR = ROOT_DIR / "ml" / "data"
REPORTS_DIR = ROOT_DIR / "ml" / "reports"


def load_feature_groups() -> dict[str, list[str]]:
    """Load defined feature groups from tabular_features.json."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Feature config not found at {CONFIG_PATH}")
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    return data.get("groups", {})


def evaluate_feature_subset(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    feature_indices: list[int],
    random_state: int = 42,
) -> dict[str, float]:
    """Train and evaluate Random Forest on a subset of features using 5-fold CV on train

    and final evaluation on test.
    """
    x_train_sub = x_train[:, feature_indices]
    x_test_sub = x_test[:, feature_indices]

    # 5-fold CV on training set
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_f1_scores = []
    cv_acc_scores = []

    for fold_train_idx, fold_val_idx in skf.split(x_train_sub, y_train):
        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            min_samples_leaf=2,
            random_state=random_state,
        )
        clf.fit(x_train_sub[fold_train_idx], y_train[fold_train_idx])
        y_val_pred = clf.predict(x_train_sub[fold_val_idx])
        cv_f1_scores.append(
            float(f1_score(y_train[fold_val_idx], y_val_pred, zero_division=0))
        )
        cv_acc_scores.append(float(accuracy_score(y_train[fold_val_idx], y_val_pred)))

    # Fit on full training set and evaluate on test set
    final_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        min_samples_leaf=2,
        random_state=random_state,
    )
    final_clf.fit(x_train_sub, y_train)
    y_test_pred = final_clf.predict(x_test_sub)
    y_test_proba = final_clf.predict_proba(x_test_sub)[:, 1]

    test_acc = float(accuracy_score(y_test, y_test_pred))
    test_f1 = float(f1_score(y_test, y_test_pred, zero_division=0))
    try:
        test_auc = float(roc_auc_score(y_test, y_test_proba))
    except ValueError:
        test_auc = 0.5

    return {
        "num_features": len(feature_indices),
        "cv_mean_f1": float(np.mean(cv_f1_scores)),
        "cv_std_f1": float(np.std(cv_f1_scores)),
        "cv_mean_acc": float(np.mean(cv_acc_scores)),
        "test_accuracy": test_acc,
        "test_f1": test_f1,
        "test_roc_auc": test_auc,
    }


def run_ablation_study(output_dir: Path | None = None) -> dict[str, Any]:
    """Execute ablation experiments comparing:

    1. All features (full 22-dimensional vector baseline).
    2. Leave-one-group-out (omitting Metadata, OCR, Text Consistency, Forensics, or Template/Record).
    3. Standalone single group models (only Metadata, only OCR, only Forensics, etc.).
    """
    out_dir = output_dir or REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    preprocessor = TabularDataPreprocessor()
    train_df, val_df, test_df = preprocessor.prepare_datasets(DATA_DIR)

    # Combine train + val for ablation cross-validation & held-out test evaluation
    full_train_df = pd.concat([train_df, val_df], ignore_index=True)
    x_train, y_train, _ = preprocessor.extract_features_and_labels(full_train_df)
    x_test, y_test, _ = preprocessor.extract_features_and_labels(test_df)

    groups = load_feature_groups()
    all_indices = list(range(len(FEATURE_NAMES)))
    feature_to_idx = {name: i for i, name in enumerate(FEATURE_NAMES)}

    results: dict[str, Any] = {
        "full_baseline": {},
        "leave_one_group_out": {},
        "standalone_groups": {},
    }

    # 1. Full 22-feature baseline
    logger.info("Evaluating full feature set (%d features)...", len(all_indices))
    full_eval = evaluate_feature_subset(x_train, y_train, x_test, y_test, all_indices)
    results["full_baseline"] = {
        "features": FEATURE_NAMES,
        **full_eval,
    }

    # 2. Leave-one-group-out ablation
    for group_name, feats in groups.items():
        omitted_indices = [feature_to_idx[f] for f in feats if f in feature_to_idx]
        subset_indices = [i for i in all_indices if i not in omitted_indices]
        subset_names = [FEATURE_NAMES[i] for i in subset_indices]

        logger.info(
            "Ablation: Omitting group '%s' (%d features left)...",
            group_name,
            len(subset_indices),
        )
        res = evaluate_feature_subset(x_train, y_train, x_test, y_test, subset_indices)
        f1_delta = res["test_f1"] - full_eval["test_f1"]
        acc_delta = res["test_accuracy"] - full_eval["test_accuracy"]

        results["leave_one_group_out"][group_name] = {
            "omitted_features": feats,
            "retained_count": len(subset_indices),
            "retained_features": subset_names,
            "f1_delta": round(f1_delta, 4),
            "acc_delta": round(acc_delta, 4),
            **res,
        }

    # 3. Standalone group models
    for group_name, feats in groups.items():
        subset_indices = [feature_to_idx[f] for f in feats if f in feature_to_idx]
        if not subset_indices:
            continue
        logger.info(
            "Evaluating standalone group '%s' (%d features)...",
            group_name,
            len(subset_indices),
        )
        res = evaluate_feature_subset(x_train, y_train, x_test, y_test, subset_indices)
        results["standalone_groups"][group_name] = {
            "features": feats,
            **res,
        }

    # Save ablation study results
    report_file = out_dir / "ablation_study_results.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Ablation study saved to %s", report_file)
    return results


if __name__ == "__main__":
    run_ablation_study()
