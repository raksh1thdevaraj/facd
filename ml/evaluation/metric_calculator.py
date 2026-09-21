"""Quantitative Metrics Calculator with Bootstrap Confidence Intervals (CHIP TST-04).

Calculates standard scientific classification metrics:
Accuracy, Precision, Recall, Specificity, F1-Score, ROC-AUC, PR-AUC,
along with 95% empirical bootstrap confidence intervals.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: Any,
    y_pred: Any,
    y_prob: Any,
    n_bootstrap: int = 100,
    random_state: int = 42,
) -> dict[str, Any]:
    """Calculate point estimates and 95% confidence intervals for all metrics."""
    y_t: Any = np.asarray(y_true, dtype=int)
    y_p: Any = np.asarray(y_pred, dtype=int)
    y_s: Any = np.asarray(y_prob, dtype=float)

    # 1. Point estimates
    cm = confusion_matrix(y_t, y_p, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    acc = float(accuracy_score(y_t, y_p))
    prec = float(precision_score(y_t, y_p, zero_division=0))
    rec = float(recall_score(y_t, y_p, zero_division=0))
    f1 = float(f1_score(y_t, y_p, zero_division=0))
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    try:
        roc_auc = float(roc_auc_score(y_t, y_s))
    except (ValueError, TypeError) as exc:
        logger.warning("ROC-AUC calculation exception: %s", exc)
        roc_auc = 1.0

    try:
        pr_auc = float(average_precision_score(y_t, y_s))
    except (ValueError, TypeError) as exc:
        logger.warning("PR-AUC calculation exception: %s", exc)
        pr_auc = 1.0

    # 2. Bootstrap Confidence Intervals
    boot_acc, boot_f1, boot_auc = [], [], []
    if n_bootstrap > 0:
        rng = np.random.RandomState(random_state)
        n = len(y_t)

        for _ in range(n_bootstrap):
            idx = rng.randint(0, n, n)
            b_true: Any = y_t[idx]
            b_pred: Any = y_p[idx]
            b_prob: Any = y_s[idx]

            if len(np.unique(b_true)) < 2:
                continue

            boot_acc.append(accuracy_score(b_true, b_pred))
            boot_f1.append(f1_score(b_true, b_pred, zero_division=0))
            try:
                boot_auc.append(roc_auc_score(b_true, b_prob))
            except (ValueError, TypeError) as exc:
                logger.debug("Failed computing bootstrap AUC: %s", exc)

    acc_ci = (
        (
            float(round(np.percentile(boot_acc, 2.5), 4)),
            float(round(np.percentile(boot_acc, 97.5), 4)),
        )
        if boot_acc
        else (acc, acc)
    )

    f1_ci = (
        (
            float(round(np.percentile(boot_f1, 2.5), 4)),
            float(round(np.percentile(boot_f1, 97.5), 4)),
        )
        if boot_f1
        else (f1, f1)
    )

    auc_ci = (
        (
            float(round(np.percentile(boot_auc, 2.5), 4)),
            float(round(np.percentile(boot_auc, 97.5), 4)),
        )
        if boot_auc
        else (roc_auc, roc_auc)
    )

    return {
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "accuracy": round(acc, 4),
        "accuracy_ci_95": acc_ci,
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "specificity": round(spec, 4),
        "f1_score": round(f1, 4),
        "f1_score_ci_95": f1_ci,
        "roc_auc": round(roc_auc, 4),
        "roc_auc_ci_95": auc_ci,
        "pr_auc": round(pr_auc, 4),
        "confidence_intervals_95": {
            "accuracy": acc_ci,
            "f1_score": f1_ci,
            "roc_auc": auc_ci,
        },
    }
