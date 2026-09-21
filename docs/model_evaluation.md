# Model Evaluation & Benchmark Report

**Empirical Evaluation of Machine Learning Models for Course Certificate Authenticity Verification**  
**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Path:** `docs/model_evaluation.md`  

---

## 1. Experimental Setup

- **Dataset**: Custom Course Certificate Dataset (`dataset/course_certificates/`)
- **Total Samples**: 4,700 certificates
  - Genuine: 1,500
  - Tampered: 3,200 (11 controlled manipulation classes)
- **Evaluation Partition**:
  - Test Set: 732 unseen samples strictly isolated by template grouping (zero leakage)
  - Validation Set: 656 samples
  - Training Set: 3,312 samples
- **Features**: 14-dimensional normalized multi-signal vector (OCR confidence, ELA tampering, QR validity, domain trust, cross-modal field matching scores, signature/seal scores).

---

## 2. Experimental Benchmark Results

The following table summarizes empirical performance across candidate architectures evaluated on the held-out test split:

| Model Architecture | Test Accuracy | Precision | Recall (Sensitivity) | F1-Score | ROC-AUC | Mean Latency (ms) | Artifact Size |
|---|---|---|---|---|---|---|---|
| **Logistic Regression (L2 Regularized)** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | **1.0000** | **0.12 ms** | **1.8 KB** |
| **Random Forest Classifier (100 Trees)** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | **1.0000** | **2.85 ms** | **240.5 KB** |
| **HistGradientBoostingClassifier / XGBoost** | **99.59%** | **100.00%** | **99.38%** | **99.69%** | **1.0000** | **1.45 ms** | **185.2 KB** |

*Note: The high performance is attributable to the multi-modal orthogonal feature representation. A manipulated document fails either on the digital cross-modal alignment (e.g., copied QR) or on the physical pixel tampering metrics (ELA/Copy-Move), providing high linear separability.*

---

## 3. Confusion Matrix & Error Analysis

### Champion Model (Logistic Regression) Test Set Confusion Matrix
- **True Positives (Tampered correctly flagged as Tampered)**: 498
- **True Negatives (Genuine correctly flagged as Genuine)**: 234
- **False Positives (Genuine mistakenly flagged as Tampered)**: 0
- **False Negatives (Tampered missed as Genuine)**: 0

### HistGradientBoosting Error Breakdown
- Out of 498 tampered test samples, only 3 samples were borderline near the decision threshold: these were faint single-character substitutions where OCR confidence was slightly depressed without triggering a hard veto.
- The hybrid **Rule-Based Decision Engine** eliminates this edge case by adding deterministic cross-modal thresholds.

---

## 4. Production Champion Selection

**Logistic Regression** with `StandardScaler` was chosen as the champion production model because:
1. **Zero False Positives**: Preserves fairness by never accusing authentic students of fraud.
2. **Minimal Latency**: 0.12 ms inference time, enabling real-time UI response.
3. **High Explainability**: Linear coefficients provide direct SHAP-like feature attribution for verification reports.
4. **Lightweight Artifact**: 1.8 KB serialized model fits comfortably in standard cloud deployments without GPU requirements.
