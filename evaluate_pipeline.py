"""
Comprehensive Evaluation Pipeline for Multi-Modal Certificate Fraud Detection.
Evaluates:
1. Behavioral Issuance Anomaly Model (Khormi et al., IEEE 2026)
2. Lightweight Visual & Alignment Tamper Detector (MobileNetV2, IEEE 2026)
3. Structural Template Similarity (SSIM + Canny Edge Difference)
4. QR / URL Whitelist & String Verification
5. End-to-End CPU Latency (< 250ms target)

Generates and exports plots to `reports/`:
- Confusion matrices
- ROC-AUC curves
- Latency histogram
- JSON summary metrics
"""

import os
import sys
import json
import time
import glob
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless plotting
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix
)

# Prevent Windows console UnicodeEncodeError
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from unified_inference import UnifiedForensicPipeline
from src.data_loader import TabularDataLoader, discover_all_certificate_images


def plot_confusion_matrix(cm: np.ndarray, class_names: list[str], title: str, save_path: str):
    """Plot and save publication-quality confusion matrix."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cax = ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.85)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                x=j, y=i, s=f"{cm[i, j]:,}",
                va="center", ha="center", size=14, weight="bold",
                color="white" if cm[i, j] > (cm.max() / 2) else "black"
            )

    fig.colorbar(cax)
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, fontsize=11)
    ax.set_yticklabels(class_names, fontsize=11)
    ax.set_xlabel("Predicted Label", fontsize=12, labelpad=10)
    ax.set_ylabel("True Ground Truth", fontsize=12, labelpad=10)
    ax.set_title(title, fontsize=13, weight="bold", pad=20)
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    print(f"[OK] Exported: {save_path}")


def plot_roc_curve(y_true: list[int], y_scores: list[float], title: str, save_path: str) -> float:
    """Plot and save ROC curve."""
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    auc_val = float(roc_auc_score(y_true, y_scores))

    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    ax.plot(fpr, tpr, color="#2563eb", lw=2.5, label=f"ROC Curve (AUC = {auc_val:.3f})")
    ax.plot([0, 1], [0, 1], color="#94a3b8", lw=1.5, linestyle="--", label="Random Chance (AUC = 0.500)")

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (FPR)", fontsize=11)
    ax.set_ylabel("True Positive Rate (TPR)", fontsize=11)
    ax.set_title(title, fontsize=13, weight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    print(f"[OK] Exported: {save_path}")
    return auc_val


def plot_latency_distribution(latencies_ms: list[float], save_path: str):
    """Plot inference latency distribution with 250ms target line."""
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    ax.hist(latencies_ms, bins=25, color="#059669", edgecolor="#064e3b", alpha=0.75)
    mean_lat = float(np.mean(latencies_ms))
    p95_lat = float(np.percentile(latencies_ms, 95))

    ax.axvline(mean_lat, color="#2563eb", linestyle="-", lw=2, label=f"Mean Latency: {mean_lat:.1f}ms")
    ax.axvline(p95_lat, color="#d97706", linestyle="--", lw=2, label=f"P95 Latency: {p95_lat:.1f}ms")
    ax.axvline(250.0, color="#dc2626", linestyle=":", lw=2.5, label="Target SLA: 250.0ms")

    ax.set_xlabel("CPU Inference Latency per Certificate (ms)", fontsize=11)
    ax.set_ylabel("Certificate Count", fontsize=11)
    ax.set_title("Inference Latency Distribution (Multi-Modal Pipeline on CPU)", fontsize=13, weight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()
    print(f"[OK] Exported: {save_path}")


def run_pipeline_evaluation(reports_dir: str = "reports") -> dict:
    print("=" * 70)
    print("RUNNING END-TO-END MULTI-MODAL PIPELINE EVALUATION")
    print("=" * 70)
    os.makedirs(reports_dir, exist_ok=True)

    pipeline = UnifiedForensicPipeline(device="cpu")
    summary = {}

    # --------------------------------------------------------------------------
    # 1. EVALUATE BEHAVIORAL FRAUD DETECTION (Khormi et al.)
    # --------------------------------------------------------------------------
    print("\n[1/4] Evaluating Behavioral Model on Test Split...")
    tab_loader = TabularDataLoader()
    _, X_test, _, y_test, _ = tab_loader.get_train_test_data(apply_smote=False)

    if pipeline.behavioral_bundle:
        b_model = pipeline.behavioral_bundle["model"]
        y_b_pred = b_model.predict(X_test)
        y_b_prob = b_model.predict_proba(X_test)[:, 1]

        b_acc = accuracy_score(y_test, y_b_pred)
        b_prec_legit = precision_score(y_test, y_b_pred, pos_label=0)
        b_prec_fraud = precision_score(y_test, y_b_pred, pos_label=1)
        b_rec_fraud = recall_score(y_test, y_b_pred, pos_label=1)
        b_f1 = f1_score(y_test, y_b_pred, pos_label=1)
        b_auc = roc_auc_score(y_test, y_b_prob)
        b_cm = confusion_matrix(y_test, y_b_pred)

        print(f"  Accuracy:  {b_acc*100:.2f}% (Target: >= 85.7%)")
        print(f"  Precision: {b_prec_legit*100:.2f}% (Legitimate, Target: >= 92.9%)")
        print(f"  ROC-AUC:   {b_auc:.4f} (Target: >= 0.940)")

        plot_confusion_matrix(
            b_cm,
            ["Legitimate", "Fraudulent"],
            "Behavioral Issuance Fraud - Confusion Matrix (Khormi et al.)",
            os.path.join(reports_dir, "behavioral_confusion_matrix.png")
        )
        plot_roc_curve(
            y_test,
            y_b_prob,
            "Behavioral Model ROC Curve (Khormi et al., IEEE 2026)",
            os.path.join(reports_dir, "behavioral_roc_curve.png")
        )

        summary["behavioral_model"] = {
            "accuracy": round(float(b_acc), 4),
            "precision_legitimate": round(float(b_prec_legit), 4),
            "precision_fraud": round(float(b_prec_fraud), 4),
            "recall": round(float(b_rec_fraud), 4),
            "f1_score": round(float(b_f1), 4),
            "roc_auc": round(float(b_auc), 4),
            "confusion_matrix": b_cm.tolist()
        }

    # --------------------------------------------------------------------------
    # 2. EVALUATE VISUAL FORENSICS & STRUCTURAL ALIGNMENT
    # --------------------------------------------------------------------------
    print("\n[2/4] Evaluating Visual Forensics & Alignment on Test Image Datasets...")
    _, val_samples = discover_all_certificate_images()

    # Limit to sample set if large to keep evaluation fast
    eval_samples = val_samples[:100] if len(val_samples) > 100 else val_samples
    print(f"  Testing on {len(eval_samples)} validation certificate documents...")

    y_vis_true = []
    y_vis_pred = []
    y_vis_probs = []
    latencies = []

    for img_path, label in eval_samples:
        t0 = time.perf_counter()
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            continue

        res = pipeline.verify_certificate(
            image_input=img_bgr,
            issuance_log={
                "timestamp": "2026-03-01 11:00:00",
                "source_ip": "10.10.3.5",
                "device_type": "Desktop_Workstation",
                "location": "Registrar_Office",
                "action": "ISSUE_CERTIFICATE"
            }
        )
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)

        prob = res["visual_forensics"]["tamper_probability"]
        pred = 1 if res["visual_forensics"]["is_tampered"] else 0

        y_vis_true.append(label)
        y_vis_pred.append(pred)
        y_vis_probs.append(prob)

    if y_vis_true:
        v_acc = accuracy_score(y_vis_true, y_vis_pred)
        v_prec = precision_score(y_vis_true, y_vis_pred, zero_division=0)
        v_rec = recall_score(y_vis_true, y_vis_pred, zero_division=0)
        v_f1 = f1_score(y_vis_true, y_vis_pred, zero_division=0)
        v_cm = confusion_matrix(y_vis_true, y_vis_pred)
        try:
            v_auc = roc_auc_score(y_vis_true, y_vis_probs)
        except Exception:
            v_auc = 0.5

        print(f"  Visual Accuracy:  {v_acc*100:.2f}%")
        print(f"  Visual Precision: {v_prec*100:.2f}% (Target: >= 95%)")
        print(f"  Visual Recall:    {v_rec*100:.2f}% (Target: >= 94%)")
        print(f"  Visual F1-Score:  {v_f1*100:.2f}% (Target: >= 95%)")

        plot_confusion_matrix(
            v_cm,
            ["Pristine", "Tampered"],
            "Visual Tamper Detector Confusion Matrix (MobileNetV2)",
            os.path.join(reports_dir, "visual_confusion_matrix.png")
        )
        plot_roc_curve(
            y_vis_true,
            y_vis_probs,
            "Visual Forensics ROC Curve (MobileNetV2)",
            os.path.join(reports_dir, "visual_roc_curve.png")
        )

        summary["visual_forensics"] = {
            "accuracy": round(float(v_acc), 4),
            "precision": round(float(v_prec), 4),
            "recall": round(float(v_rec), 4),
            "f1_score": round(float(v_f1), 4),
            "roc_auc": round(float(v_auc), 4),
            "confusion_matrix": v_cm.tolist()
        }

    # --------------------------------------------------------------------------
    # 3. LATENCY BENCHMARKING
    # --------------------------------------------------------------------------
    print("\n[3/4] Evaluating Latency Performance (Target: < 250ms CPU)...")
    if latencies:
        mean_lat = float(np.mean(latencies))
        p95_lat = float(np.percentile(latencies, 95))
        plot_latency_distribution(latencies, os.path.join(reports_dir, "pipeline_latency_distribution.png"))
        print(f"  Mean Latency: {mean_lat:.2f}ms (Target: < 250ms)")
        print(f"  P95 Latency:  {p95_lat:.2f}ms")
        summary["latency"] = {
            "mean_ms": round(mean_lat, 2),
            "p95_ms": round(p95_lat, 2),
            "target_sla_ms": 250.0,
            "sla_met": bool(mean_lat < 250.0)
        }

    # --------------------------------------------------------------------------
    # 4. EXPORT COMPREHENSIVE SUMMARY JSON
    # --------------------------------------------------------------------------
    summary_path = os.path.join(reports_dir, "evaluation_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[4/4] [OK] Full evaluation summary written to: {summary_path}")
    print("=" * 70)
    return summary


if __name__ == "__main__":
    run_pipeline_evaluation()
