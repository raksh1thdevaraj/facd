# Phase 09 — ML Baseline Model

## 1. Purpose

Implement the baseline machine learning classification subsystem using tabular feature engineering extracted from all upstream modules (OCR, Text Consistency, Image Forensics, Template Matching, and Document Metadata). This subsystem trains, evaluates, serializes, and serves classical machine learning classifiers (Random Forest, Logistic Regression, Support Vector Machine, and Gradient Boosting) to predict the binary authenticity of academic certificates (`0 = Genuine`, `1 = Manipulated/Fake`) and produce calibrated prediction probabilities.

## 2. Why This Phase Exists

While individual heuristic checks (such as an ELA score or a baseline drift measurement) provide localized clues, no single heuristic alone is 100% reliable across all document types. Some genuine certificates are compressed heavily; some genuine fonts have natural stylistic variations.
A machine learning classifier synthesizes these diverse signals into an optimal non-linear decision boundary:
- Learns the statistical correlation between combinations of forensic and textual anomalies.
- Provides a fast, deterministic, lightweight baseline that runs in under 20 milliseconds without requiring GPU hardware.
- Establishes the benchmark accuracy ($\ge 85\%$ F1-score) that any subsequent Deep Learning or Multimodal model must beat.
- Delivers transparent global and local feature importance (e.g. which specific test contributed most to flagging the document).

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-MOD-01** | Train baseline ML model (Random Forest, Logistic Regression, SVM) using extracted features | Scikit-learn training pipeline with cross-validation and hyperparameter tuning |
| **FR-MOD-02** | Tabular feature vector extraction from all upstream modules | 22-dimensional feature extractor covering OCR, text, forensics, template, metadata |
| **FR-MOD-03** | Comprehensive evaluation metrics (Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix) | Evaluation suite generating classification report and ROC curves |
| **FR-MOD-04** | Baseline target performance: Accuracy $\ge 85\%$, F1-Score $\ge 0.85$ | Model optimization, class weighting, and threshold calibration |
| **FR-MOD-05** | Model serialization, versioning, and real-time inference serving | `joblib` / ONNX serialization with inference latency $< 50$ms |
| **NFR-01** | Accuracy (Baseline $\ge 85\%$ F1-score) | Model tuning and balanced dataset evaluation |
| **NFR-03** | Performance (Inference time $< 100$ms) | Vectorized NumPy feature scaling and tree evaluation |
| **TC-MOD-01** | Baseline ML model training pipeline test | Chip MOD-11 |
| **TC-MOD-02** | Baseline evaluation metrics verification ($\ge 85\%$ Acc/F1) | Chip MOD-11 |
| **TC-MOD-03** | Feature importance extraction and ranking test | Chip MOD-12 |
| **TC-MOD-04** | Model serialization and inference latency test ($< 50$ms) | Chip MOD-12 |
| **TC-MOD-05** | Feature ablation study test | Chip MOD-12 |

## 4. Inputs

- Dataset generated in Phase 02 (`ml/data/train.csv`, `ml/data/val.csv`, `ml/data/test.csv`).
- Ingestion metadata (Phase 03).
- OCR extraction results and confidence metrics (Phase 05).
- Text consistency scores and anomaly counts (Phase 06).
- Forensic scores (ELA, Copy-Move, Noise) (Phase 07).
- Template matching scores and seal correlation (Phase 08).

## 5. Outputs

- Trained baseline model artifacts (`ml/models/baseline_random_forest_v1.joblib`, `ml/models/feature_scaler.joblib`).
- Feature definition configuration (`ml/configs/tabular_features.json`).
- Model evaluation metrics report and confusion matrix visualization (`ml/reports/baseline_evaluation_report.json`, `ml/reports/confusion_matrix.png`).
- Production inference service (`BaselineMLService`) exposing `predict(feature_vector) -> PredictionResult`.
- Database entity in `ml_prediction` table.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 02 (Dataset), Phases 03–08 (Feature sources).
- **Libraries:** `scikit-learn`, `pandas`, `numpy`, `joblib`, `scipy`, `matplotlib`, `seaborn`, `pydantic`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── ml_classifier/
│   │       ├── __init__.py
│   │       ├── feature_extractor.py   # Converts upstream results into 22D feature vector
│   │       ├── inference_engine.py    # Loads serialized model and runs inference
│   │       ├── feature_importance.py  # Feature ranking and SHAP/tree explainability
│   │       └── service.py             # Orchestrator: BaselineMLService
│   └── schemas/
│       └── ml_prediction.py           # Pydantic schemas: PredictionResult, FeatureVector
├── ml/
│   ├── configs/
│   │   └── tabular_features.json      # Schema of 22 feature definitions and normalization
│   ├── scripts/
│   │   ├── extract_dataset_features.py # Bulk feature extraction across dataset
│   │   ├── train_baseline_models.py   # Model training and cross-validation
│   │   ├── evaluate_baseline.py       # Metrics, confusion matrix, ROC-AUC
│   │   └── run_ablation_study.py      # Feature ablation analysis
│   ├── models/
│   │   └── baseline_random_forest.joblib
│   └── reports/
│       ├── baseline_metrics.json
│       └── feature_importance.png
└── tests/
    └── unit/
        ├── test_feature_extractor.py
        ├── test_baseline_inference.py
        └── test_model_evaluation.py
```

---

## 8. Implementation Chips

---

### CHIP MOD-01 — 22-Dimensional Tabular Feature Vector Definition

**Objective:** Define the complete, standardized 22-dimensional tabular feature vector extracted from all upstream analysis stages (FR-MOD-02).

**Why:** A consistent, rigorously defined numerical schema is required so training scripts, offline experiments, and production inference engines operate on identical feature columns with zero schema drift.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `ml/configs/tabular_features.json`
- `backend/app/schemas/ml_prediction.py`

**Implementation:**
1. Define the 22 feature attributes across 5 domain groups:
   - **Group A: Ingestion & Metadata (4 features)**
     1. `file_size_kb`: Normalized file size in kilobytes.
     2. `has_exif`: Binary flag (1 if EXIF exists, 0 otherwise).
     3. `software_editing_flag`: Binary flag (1 if Photoshop/Canva detected, 0 otherwise).
     4. `aspect_ratio_deviation`: Absolute difference from standard A4 aspect ratio (1.414).
   - **Group B: OCR & Text Quality (4 features)**
     5. `ocr_mean_confidence`: Average OCR token confidence $[0.0, 1.0]$.
     6. `ocr_min_confidence`: Minimum confidence among critical fields.
     7. `flagged_field_count`: Number of extracted fields with confidence $< 0.70$.
     8. `missing_critical_fields_count`: Number of unextracted critical fields (out of 5).
   - **Group C: Text Consistency (5 features)**
     9. `baseline_alignment_score`: Score from Phase 06 $[0.0, 1.0]$.
     10. `font_size_consistency_score`: Score from Phase 06 $[0.0, 1.0]$.
     11. `stroke_weight_score`: SWT score from Phase 06 $[0.0, 1.0]$.
     12. `character_spacing_score`: Spacing score from Phase 06 $[0.0, 1.0]$.
     13. `logical_consistency_score`: Chronological/score validity $[0.0, 1.0]$.
   - **Group D: Image Forensics (4 features)**
     14. `ela_score`: Error Level Analysis score $[0.0, 1.0]$.
     15. `copy_move_score`: Copy-move score $[0.0, 1.0]$.
     16. `cloned_regions_count`: Number of detected clone clusters.
     17. `noise_inconsistency_score`: Local noise variance score $[0.0, 1.0]$.
   - **Group E: Template & Record Matching (5 features)**
     18. `template_ssim_score`: SSIM score from Phase 08 $[0.0, 1.0]$.
     19. `template_feature_score`: ORB feature alignment score $[0.0, 1.0]$.
     20. `seal_match_score`: Seal correlation score $[0.0, 1.0]$.
     21. `record_found_flag`: Binary (1 if found in DB, 0 otherwise).
     22. `record_match_score`: Fuzzy field match score $[0.0, 1.0]$.
2. Save JSON schema with descriptions, types, and valid numerical ranges.

**Acceptance Criteria:**
- 22 features strictly defined with clear bounds and documented sources.

---

### CHIP MOD-02 — Production Feature Extractor Service

**Objective:** Implement `TabularFeatureExtractor` that collects raw outputs from Ingestion, OCR, Text Consistency, Forensics, and Template Matching, and constructs a clean, validated 22D NumPy vector.

**Why:** Centralizes feature generation for both dataset creation scripts and real-time backend API requests, preventing training-serving skew.

**Dependencies:** CHIP MOD-01, Phases 03–08.

**Files to create:**
- `backend/app/modules/ml_classifier/feature_extractor.py`

**Implementation:**
1. Implement `TabularFeatureExtractor`:
   ```python
   class TabularFeatureExtractor:
       def extract(
           self,
           ingestion: IngestedDocument,
           ocr: ExtractedCertificateFields,
           text_cons: TextConsistencyResult,
           forensics: ForensicAnalysisResult,
           template: TemplateMatchResult,
           record: RecordVerificationResult
       ) -> np.ndarray:
           # Build 22D feature array with deterministic ordering
           # Handle missing values: replace NaNs with domain-specific defaults (e.g. 0.5 for missing template)
           # Return float32 NumPy array of shape (22,)
   ```
2. Validate output shape: `assert vector.shape == (22,)`.
3. Check for invalid `NaN` or `Inf` values and clamp all scores into $[0.0, 1.0]$.

**Acceptance Criteria:**
- Generates complete 22-dimensional float32 vector with zero NaNs or shape errors.

---

### CHIP MOD-03 — Dataset Feature Extraction Pipeline Script

**Objective:** Create an offline batch script to execute the feature extractor across all genuine and manipulated images in the Phase 02 dataset, producing training and test CSV matrices.

**Why:** Converts raw image datasets into structured tabular datasets (`X_train.csv`, `y_train.csv`, `X_val.csv`, etc.) required for ML model training.

**Dependencies:** CHIP MOD-02, Phase 02 Dataset.

**Files to create:**
- `ml/scripts/extract_dataset_features.py`

**Implementation:**
1. Read split manifests (`ml/data/train_split.csv`, `ml/data/val_split.csv`, `ml/data/test_split.csv`).
2. Run pipeline modules on each image with parallel multiprocessing (`multiprocessing.Pool(cpu_count() - 1)`).
3. Append 22 extracted features along with binary label `is_manipulated` (0 = genuine, 1 = manipulated).
4. Save resulting dataframes to:
   - `ml/data/features_train.parquet`
   - `ml/data/features_val.parquet`
   - `ml/data/features_test.parquet`
5. Print extraction progress bar and summary statistics.

**Acceptance Criteria:**
- Successfully processes full dataset and outputs clean, labeled Parquet/CSV feature tables.

---

### CHIP MOD-04 — Feature Preprocessing & Standardization Pipeline

**Objective:** Implement Scikit-learn `ColumnTransformer` and `StandardScaler` to normalize continuous features and handle missing data.

**Why:** Continuous features like `file_size_kb` have vastly different scales than $[0.0, 1.0]$ scores. Logistic Regression and SVM require zero-mean, unit-variance standardization.

**Dependencies:** CHIP MOD-03.

**Files to create:**
- `ml/scripts/preprocess_features.py`

**Implementation:**
1. Define feature transformation pipeline:
   ```python
   preprocessor = ColumnTransformer(
       transformers=[
           ("num_scaler", StandardScaler(), continuous_feature_indices),
           ("passthrough", "passthrough", binary_score_indices),
       ]
   )
   ```
2. Fit scaler strictly on `features_train` (prevent data leakage).
3. Transform `features_val` and `features_test`.
4. Serialize fitted preprocessor to `ml/models/feature_scaler.joblib`.

**Acceptance Criteria:**
- Scaler fits on training split only and serializes to disk.

---

### CHIP MOD-05 — Multi-Model Training & Hyperparameter Tuning

**Objective:** Train and evaluate 4 candidate classical ML algorithms (Random Forest, Logistic Regression, Linear SVM, and Gradient Boosting) using Stratified 5-Fold Cross-Validation and GridSearchCV (FR-MOD-01).

**Why:** Comparing multiple algorithms identifies which classifier produces the highest generalization performance on certificate forgery detection.

**Dependencies:** CHIP MOD-04.

**Files to create:**
- `ml/scripts/train_baseline_models.py`

**Implementation:**
1. Configure candidate algorithms with hyperparameter search grids:
   - **Model 1: Random Forest Classifier (Primary):**
     - `n_estimators: [100, 200, 300]`
     - `max_depth: [6, 10, 15, None]`
     - `min_samples_split: [2, 5, 10]`
     - `class_weight: ["balanced", None]`
   - **Model 2: Gradient Boosting (XGBoost / HistGradientBoosting):**
     - `learning_rate: [0.01, 0.05, 0.1]`
     - `max_iter: [100, 200]`
   - **Model 3: Logistic Regression (Baseline sanity check):**
     - `C: [0.01, 0.1, 1.0, 10.0]`
     - `penalty: ["l2"]`
   - **Model 4: Support Vector Classifier (RBF kernel):**
     - `C: [0.5, 1.0, 5.0]`, `gamma: ["scale", "auto"]`
2. Run `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
3. Optimize for F1-score: `scoring="f1"`.
4. Save best hyperparameters and cross-validation score logs.

**Acceptance Criteria:**
- Trains all 4 candidate models across 5 folds and logs cross-validation metrics.

---

### CHIP MOD-06 — Baseline Model Evaluation & Performance Benchmark

**Objective:** Evaluate trained models on the held-out test set (`features_test.parquet`) across Accuracy, Precision, Recall, F1-Score, and ROC-AUC, verifying the target benchmark of $\ge 85\%$ Accuracy and $\ge 0.85$ F1-Score (FR-MOD-03, FR-MOD-04, NFR-01).

**Why:** Demonstrates that the baseline system meets contractual project specifications on unseen data before deep learning models are introduced.

**Dependencies:** CHIP MOD-05.

**Files to create:**
- `ml/scripts/evaluate_baseline.py`

**Implementation:**
1. Compute metrics on test set:
   - `accuracy_score(y_test, y_pred)`
   - `precision_score(y_test, y_pred)`
   - `recall_score(y_test, y_pred)`
   - `f1_score(y_test, y_pred)`
   - `roc_auc_score(y_test, y_prob)`
2. Generate Confusion Matrix:
   - True Positives (Manipulated correctly flagged)
   - True Negatives (Genuine correctly accepted)
   - False Positives (Genuine mistakenly flagged as fake)
   - False Negatives (Fake mistakenly accepted as genuine)
3. Render visualizations using Matplotlib/Seaborn:
   - Confusion Matrix heatmap -> `ml/reports/baseline_confusion_matrix.png`
   - ROC Curve plot -> `ml/reports/baseline_roc_curve.png`
4. Assert performance thresholds:
   ```python
   assert test_accuracy >= 0.85, f"Accuracy {test_accuracy} below 0.85 target"
   assert test_f1 >= 0.85, f"F1-score {test_f1} below 0.85 target"
   ```
5. Save comprehensive metrics dictionary to `ml/reports/baseline_metrics.json`.

**Acceptance Criteria:**
- Best model achieves $\ge 85\%$ accuracy and $\ge 0.85$ F1-score on held-out test set (TC-MOD-02).

---

### CHIP MOD-07 — Feature Importance Extraction and Ranking

**Objective:** Extract Gini feature importance (for Random Forest) and Permutation Feature Importance to identify which forensic and textual signals contribute most to fraud detection (TC-MOD-03).

**Why:** Explains the global behavior of the model to stakeholders (e.g. showing that ELA score and baseline drift are the top 2 predictive indicators).

**Dependencies:** CHIP MOD-06.

**Files to create:**
- `backend/app/modules/ml_classifier/feature_importance.py`

**Implementation:**
1. Extract `model.feature_importances_` from Random Forest.
2. Compute Permutation Feature Importance using `sklearn.inspection.permutation_importance(model, X_test, y_test, n_repeats=10)`.
3. Sort features by importance descending.
4. Generate horizontal bar chart showing top 15 most important features -> `ml/reports/feature_importance.png`.
5. Return JSON ranking for frontend explainability display.

**Acceptance Criteria:**
- Correctly ranks features and generates feature importance chart (TC-MOD-03).

---

### CHIP MOD-08 — Feature Ablation Study

**Objective:** Perform a systematic feature ablation study by training models with specific feature groups removed (e.g. without Forensics, without Text Consistency, without Template Matching) (TC-MOD-05).

**Why:** Proves the necessity and value of each engineering module in the final detection pipeline, satisfying the project thesis and research defense requirements.

**Dependencies:** CHIP MOD-05.

**Files to create:**
- `ml/scripts/run_ablation_study.py`

**Implementation:**
1. Define ablation configurations:
   - All 22 features (Full baseline)
   - Without Group A (No Metadata)
   - Without Group B (No OCR confidence)
   - Without Group C (No Text Consistency)
   - Without Group D (No Image Forensics)
   - Without Group E (No Template/Record matching)
   - Single-group models (Forensics only, Text Consistency only)
2. Train Random Forest on each subset and record test F1-score and ROC-AUC.
3. Generate comparison summary table and save to `ml/reports/ablation_study_results.json`.

**Acceptance Criteria:**
- Completes ablation experiments and proves multi-module fusion outperforms individual feature groups (TC-MOD-05).

---

### CHIP MOD-09 — Model Serialization, Versioning & Packaging

**Objective:** Serialize the best-performing model, scaler, and feature metadata into versioned production artifacts (FR-MOD-05).

**Why:** Enables the backend API to load the model instantly at startup without any training dependencies.

**Dependencies:** CHIP MOD-06.

**Files to create:**
- `ml/scripts/export_model.py`

**Implementation:**
1. Save model bundle:
   - `ml/models/baseline_model_v1.joblib`
   - `ml/models/feature_scaler_v1.joblib`
2. Create manifest `ml/models/model_manifest.json`:
   - `model_version: "1.0.0"`
   - `algorithm: "RandomForestClassifier"`
   - `training_date: ISO 8601`
   - `test_accuracy: float`
   - `test_f1_score: float`
   - `feature_count: 22`
   - `feature_names: List[str]`
3. Verify integrity by loading the saved artifact and running a test prediction.

**Acceptance Criteria:**
- Model bundle loads cleanly and passes verification inference test.

---

### CHIP MOD-10 — Production Baseline ML Inference Service

**Objective:** Implement the real-time `BaselineMLService` that loads serialized model artifacts into memory and executes fast inference ($< 50$ms latency) (FR-MOD-05, NFR-03).

**Why:** Serves predictions to the verification pipeline and populates the `ml_prediction` database table.

**Dependencies:** CHIP MOD-02, CHIP MOD-09.

**Files to create:**
- `backend/app/modules/ml_classifier/inference_engine.py`
- `backend/app/modules/ml_classifier/service.py`

**Implementation:**
1. Implement `BaselineMLService` singleton:
   - Loads `baseline_model_v1.joblib` and `feature_scaler_v1.joblib` at startup.
   - Expose `predict(feature_vector: np.ndarray) -> PredictionResult`:
     ```python
     # 1. Scale input vector using preprocessor
     # 2. Predict probability: proba = model.predict_proba(scaled_vec)[0]
     # 3. fake_probability = float(proba[1])
     # 4. is_fake = fake_probability >= 0.50
     # 5. Extract top local contributing features (tree path or feature deltas)
     # 6. Return PredictionResult(
     #        predicted_label="MANIPULATED" if is_fake else "GENUINE",
     #        fake_probability=fake_probability,
     #        confidence=max(fake_probability, 1 - fake_probability),
     #        latency_ms=elapsed_ms
     #    )
     ```
2. Persist prediction to `ml_prediction` database table.

**Acceptance Criteria:**
- Executes prediction in $< 20$ms on standard CPU (TC-MOD-04).

---

### CHIP MOD-11 — Unit Tests: Baseline Training & Evaluation Metrics

**Objective:** Test automated baseline model training, hyperparameter selection, and verify evaluation metrics meet the $\ge 85\%$ accuracy and F1 threshold (TC-MOD-01, TC-MOD-02).

**Dependencies:** CHIP MOD-05, CHIP MOD-06.

**Files to create:**
- `backend/tests/unit/test_model_training.py`
- `backend/tests/unit/test_model_evaluation.py`

**Implementation:**
1. Test `test_model_training_completes()`: Run training script on synthetic 22D dataset fixture (TC-MOD-01).
2. Test `test_evaluation_metrics_meet_spec()`: Verify test accuracy $\ge 0.85$ and F1-score $\ge 0.85$ (TC-MOD-02).
3. Test `test_confusion_matrix_dimensions()`: Verify $2 \times 2$ confusion matrix with zero negative entries.

**Acceptance Criteria:**
- Confirms baseline model meets or exceeds all target accuracy specifications.

---

### CHIP MOD-12 — Unit Tests: Feature Importance, Serialization & Latency

**Objective:** Test feature importance extraction, model serialization, and verify inference latency is $< 50$ms (TC-MOD-03, TC-MOD-04, TC-MOD-05).

**Dependencies:** CHIP MOD-07, CHIP MOD-08, CHIP MOD-10.

**Files to create:**
- `backend/tests/unit/test_baseline_inference.py`

**Implementation:**
1. Test `test_feature_importance_ranking()`: Verify top features returned match expected domain signals (TC-MOD-03).
2. Test `test_inference_latency_under_50ms()`: Run 100 consecutive predictions; assert mean latency $< 25$ms (TC-MOD-04, NFR-03).
3. Test `test_ablation_study_execution()`: Verify ablation script computes performance delta for omitted groups (TC-MOD-05).

**Acceptance Criteria:**
- 100% test pass rate across ML baseline test cases.

---

## 9. Implementation Order and Dependencies

```
CHIP MOD-01 (22D Feature Vector Definition)
    ↓
CHIP MOD-02 (Feature Extractor Service)
    ↓
CHIP MOD-03 (Dataset Feature Extraction Script)
    ↓
CHIP MOD-04 (Scaler & Preprocessing Pipeline)
    ↓
CHIP MOD-05 (Multi-Model Training & Tuning)
    ↓
CHIP MOD-06 (Evaluation & Metrics Benchmark) ──┐
    ↓                                          │
CHIP MOD-07 (Feature Importance Ranking)       │
    ↓                                          │
CHIP MOD-08 (Feature Ablation Study)           │
    ↓                                          │
CHIP MOD-09 (Model Serialization & Packaging) ◄┘
    ↓
CHIP MOD-10 (Production Inference Service)
    ↓
CHIP MOD-11 & CHIP MOD-12 (Unit Tests & Benchmarks)
```

---

## 10. Phase Completion Checklist

- [ ] Standard 22-dimensional feature schema defined and documented in `tabular_features.json`.
- [ ] Feature extractor transforms upstream pipeline outputs into validated 22D NumPy vectors.
- [ ] Training/val/test feature matrices extracted across full certificate dataset.
- [ ] Scaler fits strictly on training split and handles continuous feature normalization.
- [ ] Random Forest, Gradient Boosting, Logistic Regression, and SVM trained with 5-fold cross-validation.
- [ ] Best model achieves test Accuracy $\ge 85\%$ and F1-Score $\ge 0.85$ (FR-MOD-04, NFR-01).
- [ ] Confusion matrix, ROC curve, and classification reports generated and saved.
- [ ] Global feature importance ranked and visualized in horizontal bar chart.
- [ ] Feature ablation study proves multi-feature fusion outperforms individual heuristics.
- [ ] Production inference service executes predictions in $< 20$ms per certificate.
- [ ] Test cases TC-MOD-01 through TC-MOD-05 passing with 100% success rate.
