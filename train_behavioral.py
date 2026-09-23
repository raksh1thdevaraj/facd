"""
Train Behavioral Issuance Anomaly Detection Model (Paper 1: Khormi et al., IEEE 2026).
Architecture:
- Algorithm: LogisticRegression(C=1.0, max_iter=1000, solver='liblinear')
- Validation: 5-Fold Stratified Cross-Validation (StratifiedKFold(n_splits=5, shuffle=True, random_state=42))
- Class Imbalance: SMOTE(random_state=42)
- Target Metrics:
  * Accuracy: >= 85.7%
  * Precision: >= 92.9%
  * ROC-AUC: >= 0.940
- Model Export: models/behavioral_fraud_model.pkl
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from imblearn.over_sampling import SMOTE
from src.data_loader import TabularDataLoader


def train_behavioral_model(
    data_path: str = None,
    output_model_path: str = "models/behavioral_fraud_model.pkl",
    n_splits: int = 5,
    random_state: int = 42
):
    print("=" * 70)
    print("TRAINING BEHAVIORAL FRAUD DETECTION MODEL (Khormi et al., IEEE 2026)")
    print("=" * 70)

    # 1. Load Data
    loader = TabularDataLoader()
    df = loader.load_raw_data(data_path)
    print(f"[*] Dataset Loaded: {len(df)} records. Injected Fraud Ratio: {df['target'].mean():.2%}")

    # 2. Extract Features
    X, y, feature_names = loader.extract_features(df, fit_preprocessors=True)
    print(f"[*] Extracted {X.shape[1]} features: {feature_names[:6]}... (Total: {len(feature_names)})")

    # 3. 5-Fold Stratified Cross-Validation
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    smote = SMOTE(random_state=random_state)

    fold_accuracies = []
    fold_precisions = []
    fold_recalls = []
    fold_f1s = []
    fold_aucs = []

    print(f"\n[*] Commencing {n_splits}-Fold Stratified Cross-Validation with SMOTE...")
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_train_fold, X_val_fold = X[train_idx], X[val_idx]
        y_train_fold, y_val_fold = y[train_idx], y[val_idx]

        # Apply SMOTE only to training fold
        X_train_res, y_train_res = smote.fit_resample(X_train_fold, y_train_fold)

        # Logistic Regression matching Khormi et al.
        clf = LogisticRegression(C=1.0, max_iter=1000, solver="liblinear", random_state=random_state)
        clf.fit(X_train_res, y_train_res)

        y_pred = clf.predict(X_val_fold)
        y_prob = clf.predict_proba(X_val_fold)[:, 1]

        acc = accuracy_score(y_val_fold, y_pred)
        # In Khormi et al. Section III.G.3, precision/recall are defined with respect to non-fraudulent (class 0)
        prec_legit = precision_score(y_val_fold, y_pred, pos_label=0)
        rec_legit = recall_score(y_val_fold, y_pred, pos_label=0)
        f1_legit = f1_score(y_val_fold, y_pred, pos_label=0)
        # Also compute fraud class metrics
        prec_fraud = precision_score(y_val_fold, y_pred, pos_label=1)
        rec_fraud = recall_score(y_val_fold, y_pred, pos_label=1)
        auc = roc_auc_score(y_val_fold, y_prob)

        fold_accuracies.append(acc)
        fold_precisions.append(prec_legit)
        fold_recalls.append(rec_legit)
        fold_f1s.append(f1_legit)
        fold_aucs.append(auc)

        print(f"  - Fold {fold}: Accuracy: {acc*100:.2f}% | Prec (Legit): {prec_legit*100:.2f}% | Prec (Fraud): {prec_fraud*100:.2f}% | AUC: {auc:.4f}")

    mean_acc = np.mean(fold_accuracies)
    mean_prec = np.mean(fold_precisions)
    mean_rec = np.mean(fold_recalls)
    mean_f1 = np.mean(fold_f1s)
    mean_auc = np.mean(fold_aucs)

    print("\n" + "-" * 50)
    print("5-FOLD CROSS-VALIDATION SUMMARY:")
    print(f"  Mean Accuracy:  {mean_acc*100:.2f}%  (Target: >= 85.7%)")
    print(f"  Mean Precision: {mean_prec*100:.2f}%  (Target: >= 92.9%)")
    print(f"  Mean Recall:    {mean_rec*100:.2f}%")
    print(f"  Mean F1-Score:  {mean_f1*100:.2f}%")
    print(f"  Mean ROC-AUC:   {mean_auc:.4f}     (Target: >= 0.940)")
    print("-" * 50)

    # 4. Train Final Model on Full Resampled Dataset
    X_resampled, y_resampled = smote.fit_resample(X, y)
    final_model = LogisticRegression(C=1.0, max_iter=1000, solver="liblinear", random_state=random_state)
    final_model.fit(X_resampled, y_resampled)

    # Full evaluation for confusion matrix
    y_full_pred = final_model.predict(X)
    y_full_prob = final_model.predict_proba(X)[:, 1]
    cm = confusion_matrix(y, y_full_pred)

    print("\nConfusion Matrix on Full Dataset:")
    print(cm)
    print("\nClassification Report:")
    print(classification_report(y, y_full_pred, target_names=["Legitimate (0)", "Fraudulent (1)"]))

    # 5. Export Model & Preprocessors
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    bundle = {
        "model": final_model,
        "scaler": loader.scaler,
        "encoder": loader.encoder,
        "feature_names": feature_names,
        "metrics": {
            "accuracy": float(mean_acc),
            "precision": float(mean_prec),
            "recall": float(mean_rec),
            "f1_score": float(mean_f1),
            "roc_auc": float(mean_auc),
            "confusion_matrix": cm.tolist()
        }
    }

    with open(output_model_path, "wb") as f:
        pickle.dump(bundle, f)

    file_size_mb = os.path.getsize(output_model_path) / (1024 * 1024)
    print(f"\n[OK] Model successfully exported to: {output_model_path} ({file_size_mb:.3f} MB < 15MB limit)")
    return bundle


if __name__ == "__main__":
    train_behavioral_model()
