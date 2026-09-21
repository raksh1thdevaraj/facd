# Machine Learning Training & Inference Guide: Course Certificate Authenticity

**Authoritative Technical Guide for Model Training, Cross-Validation, and Production Serving**  
**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Path:** `docs/ml_training_guide.md`  

---

## 1. Multi-Signal Machine Learning Architecture

The fraud detection pipeline rejects monolithic black-box classification in favor of a **14-dimensional multi-modal feature vector** derived from digital, optical, and forensic signals:

| # | Feature Name | Range | Description |
|---|---|---|---|
| 1 | `ocr_confidence` | $[0.0, 1.0]$ | Mean token extraction confidence from OCR engine |
| 2 | `tampering_probability` | $[0.0, 1.0]$ | Combined forensic score ($1.0 - \text{overall\_forensic\_score}$) |
| 3 | `qr_detected` | $\{0, 1\}$ | Binary flag indicating if QR code bounding box was found |
| 4 | `qr_decoded` | $\{0, 1\}$ | Binary flag indicating if QR payload successfully unmarshaled |
| 5 | `url_valid_syntax` | $\{0, 1\}$ | Binary flag indicating if extracted payload is a valid HTTPS URL |
| 6 | `issuer_trusted` | $\{0, 1\}$ | Flag indicating if domain matches the authoritative issuer registry |
| 7 | `domain_match` | $\{0, 1\}$ | Flag indicating whether certificate text issuer matches URL domain |
| 8 | `online_available` | $\{0, 1\}$ | Flag indicating if online verification HTTP endpoint was accessible |
| 9 | `name_match_score` | $[0.0, 1.0]$ | Normalized fuzzy token similarity of candidate name |
| 10 | `course_match_score` | $[0.0, 1.0]$ | Normalized fuzzy token similarity of course/degree name |
| 11 | `cert_id_match_score` | $[0.0, 1.0]$ | Canonical alphanumeric equality of certificate ID |
| 12 | `date_match_score` | $[0.0, 1.0]$ | Normalized date timestamp match score |
| 13 | `signature_score` | $[0.0, 1.0]$ | Handwritten signatory stroke density and continuity score |
| 14 | `seal_score` | $[0.0, 1.0]$ | Circular institutional seal contour and saturation score |

---

## 2. Training Pipeline & Model Comparison

The training pipeline is executed via `ml/scripts/train_course_cert_model.py`. It trains and compares three competitive model families using strictly partitioned group splits:

1. **Logistic Regression** (L2 Regularized baseline with standard scaling)
2. **Random Forest Classifier** (100 estimators, max depth 8, balanced class weights)
3. **HistGradientBoostingClassifier / XGBoost** (Early stopping, learning rate 0.05)

### 2.1 Optimization & Metrics
Evaluated on the unseen test set (732 samples):
- **Accuracy**
- **Precision**
- **Recall (Fraud Detection Sensitivity)**
- **F1-Score (Harmonic Mean)**
- **ROC-AUC**
- **Inference Latency (ms per sample)**

---

## 3. Running the Training Pipeline

To train the models from scratch and regenerate benchmarks:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run model training and benchmark comparison
python ml/scripts/train_course_cert_model.py
```

Output artifacts generated:
- `ml/models/course_cert_classifier.joblib`: Serialized production scikit-learn pipeline.
- `docs/course_certificate_model_evaluation.md`: Benchmark comparison table with real experimental metrics.

---

## 4. Inference & Decision Engine Integration

During live verification, `CourseDecisionEngine` (`backend/app/modules/course_verification/decision_engine.py`) consumes the 14-D vector, queries the serialized model, and synthesizes the final explainable verdict:

```python
from app.modules.course_verification.decision_engine import CourseDecisionEngine

engine = CourseDecisionEngine()
decision = engine.evaluate(
    extracted_fields=extracted,
    qr_result=qr_res,
    url_result=url_res,
    comparison_result=comp_res,
    forensic_result=forensic_res,
    seal_sig_result=seal_sig_res,
)

print(decision.status)  # VERIFIED | SUSPICIOUS | FRAUDULENT | UNVERIFIED
print(decision.overall_authenticity_score)  # e.g., 96.5%
print(decision.fraud_risk_score)  # e.g., 3.5%
```
