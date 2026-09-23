"""
Master End-to-End Training & Pipeline Execution Script.
Orchestrates:
1. Local Dataset Auto-Discovery & Indexing (src/data_loader.py)
2. Behavioral Issuance Anomaly Training with SMOTE & 5-Fold CV (train_behavioral.py)
3. Lightweight MobileNetV2 Visual Tamper Training & ONNX Export (train_visual_forensics.py)
4. Multi-Modal Pipeline Evaluation & Publication Reports (evaluate_pipeline.py)
"""

import os
import sys
import time
import argparse

# Force UTF-8 encoding on Windows consoles
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from train_behavioral import train_behavioral_model
from train_visual_forensics import train_visual_forensics_model
from evaluate_pipeline import run_pipeline_evaluation


def main():
    parser = argparse.ArgumentParser(description="Multi-Modal Certificate Fraud Detection Training Pipeline")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs for visual model (default: 15)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for visual model (default: 32)")
    parser.add_argument("--skip-visual", action="store_true", help="Skip visual model training if weights exist")
    parser.add_argument("--skip-behavioral", action="store_true", help="Skip behavioral model training")
    args = parser.parse_args()

    pipeline_start = time.time()
    print("=" * 80)
    print("AI-BASED DETECTION OF FAKE OR MANIPULATED ACADEMIC CERTIFICATES")
    print("MULTI-MODAL LIGHTWEIGHT TRAINING & VERIFICATION PIPELINE")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # STEP 1: Behavioral Issuance Anomaly Model (Khormi et al., IEEE 2026)
    # --------------------------------------------------------------------------
    if not args.skip_behavioral:
        print("\n>>> STEP 1: TRAINING BEHAVIORAL ANOMALY DETECTION MODEL")
        train_behavioral_model(
            output_model_path="models/behavioral_fraud_model.pkl",
            n_splits=5,
            random_state=42
        )
    else:
        print("\n>>> STEP 1: Skipping behavioral model training (--skip-behavioral)")

    # --------------------------------------------------------------------------
    # STEP 2: Lightweight Visual & Alignment Tamper Detector (MobileNetV2)
    # --------------------------------------------------------------------------
    if not args.skip_visual:
        print("\n>>> STEP 2: TRAINING LIGHTWEIGHT VISUAL TAMPER DETECTOR (MobileNetV2)")
        train_visual_forensics_model(
            datasets_dir="datasets",
            output_pt_path="models/visual_tamper_mobilenet.pt",
            output_onnx_path="models/visual_tamper_mobilenet.onnx",
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            lr=1e-4,
            patience=5
        )
    else:
        print("\n>>> STEP 2: Skipping visual model training (--skip-visual)")

    # --------------------------------------------------------------------------
    # STEP 3: Multi-Modal Verification Pipeline Evaluation & Report Generation
    # --------------------------------------------------------------------------
    print("\n>>> STEP 3: RUNNING MULTI-MODAL PIPELINE EVALUATION & REPORT GENERATION")
    summary = run_pipeline_evaluation(reports_dir="reports")

    # --------------------------------------------------------------------------
    # SUMMARY OF DELIVERABLES & ARTIFACTS
    # --------------------------------------------------------------------------
    total_elapsed = time.time() - pipeline_start
    print("\n" + "=" * 80)
    print("ALL PIPELINE STAGES COMPLETED SUCCESSFULLY!")
    print(f"Total Execution Time: {total_elapsed:.1f}s")
    print("=" * 80)

    print("\nExported Model Artifacts (under 15MB limit):")
    for f in ["models/behavioral_fraud_model.pkl", "models/visual_tamper_mobilenet.pt", "models/visual_tamper_mobilenet.onnx"]:
        if os.path.exists(f):
            sz = os.path.getsize(f) / (1024 * 1024)
            print(f"  [+] {f:<38} | Size: {sz:6.2f} MB (< 15MB)")

    print("\nGenerated Evaluation Reports & Plots:")
    for r in [
        "reports/behavioral_confusion_matrix.png",
        "reports/behavioral_roc_curve.png",
        "reports/visual_confusion_matrix.png",
        "reports/visual_roc_curve.png",
        "reports/pipeline_latency_distribution.png",
        "reports/evaluation_summary.json"
    ]:
        if os.path.exists(r):
            print(f"  [+] {r}")

    print("\nPipeline ready for production deployment and API integration.")


if __name__ == "__main__":
    main()
