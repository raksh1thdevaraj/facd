# Phase 19 — Testing & Evaluation

## 1. Purpose

Execute the comprehensive quality assurance, automated test suite, and scientific evaluation benchmarking across the entire certificate verification system. This phase validates test coverage ($\ge 80\%$ target via `pytest-cov`), runs all 30+ traceable test cases defined in the Testing Documents, generates the formal scientific evaluation report (Accuracy, Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix) across diverse forgery categories, and completes the ablation study proving the superiority of the multimodal approach for academic thesis and project defense.

## 2. Why This Phase Exists

A major college project in AI and computer vision requires rigorous empirical validation:
- High code coverage ($\ge 80\%$) proves that the software engineering foundation is robust, maintainable, and free of untested execution paths.
- Scientific defensibility: Examiners and reviewers will evaluate the project on quantitative benchmarks: How well does it detect subtle font swaps vs. cloned seals? What is the false positive rate on degraded genuine photocopies?
- The comparative evaluation table (Baseline ML vs. Deep Learning Visual vs. Multimodal Fusion) provides the central scientific evidence demonstrating that the student's multimodal architecture achieved state-of-the-art results.
- Automated ablation studies demonstrate the distinct contribution of each engineering component (Forensics, Text Consistency, Template Matching, DL).

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-TST-01** | Full automated test suite execution (Unit, Integration, E2E) across all modules | Unified test runner executing all test cases with coverage reporting |
| **FR-TST-02** | Code test coverage target $\ge 80\%$ across backend application code | `pytest --cov=app --cov-report=html` coverage audit |
| **FR-TST-03** | Comprehensive model evaluation on test dataset split (Acc, Prec, Rec, F1, ROC-AUC) | Quantitative evaluation script generating classification report and ROC curves |
| **FR-TST-04** | Fine-grained performance breakdown across 5 specific forgery categories | Per-category evaluation: Spliced Text, Cloned Stamps, Font Mismatch, Logic, Counterfeit |
| **FR-TST-05** | Model comparison analysis: Baseline ML vs. Deep Learning vs. Multimodal Fusion | Automated generation of comparative performance table and ROC overlay plot |
| **FR-TST-06** | Complete feature ablation study execution and synthesis | Systematic ablation runner quantifying performance degradation on feature removals |
| **NFR-01** | Verification Accuracy: Overall Accuracy $\ge 92\%$, F1-Score $\ge 0.92$ | Validated on held-out test split |
| **TC-EVAL-01** | Full evaluation suite execution on held-out test split | Chip TST-11 |
| **TC-EVAL-02** | Quantitative metrics assertion ($\ge 92\%$ Acc/F1) | Chip TST-11 |
| **TC-EVAL-03** | Evaluation report generation in JSON and Markdown formats | Chip TST-12 |
| **TC-EVAL-04** | Ablation study execution and synthesis report test | Chip TST-12 |
| **TC-EVAL-05** | Code coverage assertion ($\ge 80\%$) | Chip TST-12 |

## 4. Inputs

- Complete codebase from Phases 01 through 18.
- Held-out test dataset split from Phase 02 (`ml/data/test/` and `ml/data/features_test.parquet`).
- Serialized model artifacts from Phases 09, 10, and 11.
- Complete set of 30+ test case specifications from Testing Documents.

## 5. Outputs

- Automated test execution report (`reports/test_results.xml`).
- Code coverage report (`reports/coverage/index.html` and `reports/coverage.xml`).
- Formal Evaluation Report in Markdown (`ml/reports/FINAL_EVALUATION_REPORT.md`) and JSON.
- High-resolution evaluation charts:
  - Confusion Matrix Heatmap (`ml/reports/evaluation_confusion_matrix.png`)
  - Comparative ROC Curves Plot (`ml/reports/comparative_roc_curves.png`)
  - Precision-Recall Curve Plot (`ml/reports/precision_recall_curves.png`)
  - Forgery Category Breakdown Bar Chart (`ml/reports/category_breakdown.png`)
  - Ablation Study Impact Chart (`ml/reports/ablation_study_chart.png`)

## 6. Dependencies

- **Previous phases:** Phases 01 through 18.
- **Libraries:** `pytest`, `pytest-cov`, `pytest-asyncio`, `scikit-learn`, `matplotlib`, `seaborn`, `pandas`, `numpy`.

## 7. Files and Folder Structure

```
backend/
├── tests/
│   ├── conftest.py                    # Root test configuration and shared fixtures
│   ├── unit/                          # Unit tests (Phases 03–13)
│   ├── integration/                   # Integration tests (Phases 14–17)
│   └── e2e/                           # End-to-end tests (Phase 18)
├── ml/
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── benchmark_runner.py        # Runs full test set inference
│   │   ├── metric_calculator.py       # Computes Acc, Prec, Rec, F1, ROC-AUC, PR-AUC
│   │   ├── category_evaluator.py      # Computes metrics per forgery category
│   │   ├── chart_generator.py         # Renders publication-grade Matplotlib plots
│   │   └── report_writer.py           # Synthesizes Markdown and JSON reports
│   └── reports/
│       ├── FINAL_EVALUATION_REPORT.md
│       ├── final_metrics.json
│       ├── evaluation_confusion_matrix.png
│       ├── comparative_roc_curves.png
│       └── category_breakdown.png
└── scripts/
    ├── run_all_tests.sh               # Runs complete test suite with coverage
    └── run_evaluation_benchmark.py    # Executes full evaluation pipeline
```

---

## 8. Implementation Chips

---

### CHIP TST-01 — Unified Test Runner & Coverage Configuration

**Objective:** Configure `pytest` and `pytest-cov` with strict coverage settings, path inclusions, and exclusions (`tests/`, `migrations/`), enforcing the $\ge 80\%$ test coverage requirement (FR-TST-02, TC-EVAL-05).

**Why:** Ensures that every pull request or build runs the entire test suite and fails if test coverage falls below the required 80% threshold.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/pytest.ini`
- `backend/.coveragerc`

**Implementation:**
1. Configure `pytest.ini`:
   ```ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   asyncio_mode = auto
   filterwarnings = ignore::DeprecationWarning
   addopts = --strict-markers --cov=app --cov-report=term-missing --cov-report=html:reports/coverage --cov-report=xml:reports/coverage.xml --cov-fail-under=80
   ```
2. Configure `.coveragerc` to omit migrations, scripts, and test helpers.

**Acceptance Criteria:**
- Running `pytest` automatically measures coverage across `app/` and enforces the $\ge 80\%$ threshold (TC-EVAL-05).

---

### CHIP TST-02 — Test Case Traceability Matrix & Execution Tracker

**Objective:** Build an automated test tracker script that maps every requirement from the SRD (FR-ING-01 to FR-USR-04) and every test case from the Testing Documents (TC-ING-01 to TC-E2E-05) to its executing test function.

**Why:** Guarantees complete bidirectional traceability for project auditing: proves that every requirement has at least one automated test verifying it.

**Dependencies:** Phases 03 through 18.

**Files to create:**
- `backend/scripts/verify_traceability.py`
- `development-plan/TRACEABILITY_MATRIX.md`

**Implementation:**
1. Script inspects test files for pytest markers: `@pytest.mark.req("FR-ING-01")`, `@pytest.mark.tc("TC-ING-01")`.
2. Verifies that all 30 SRD requirements and all 35 test cases are covered.
3. Outputs formatted Markdown table showing Requirement ID, Description, Implementing Phase, Test Case ID, and Test Status (PASSED/FAILED).

**Acceptance Criteria:**
- 100% of SRD functional requirements and test cases mapped and passing.

---

### CHIP TST-03 — Test Split Benchmark Runner

**Objective:** Implement `BenchmarkRunner` to run the fully integrated verification pipeline across all images in the held-out test split (`ml/data/test/`), recording ground truth vs. model predictions, probabilities, and execution latencies (FR-TST-03).

**Why:** Collects the raw empirical prediction data required to calculate scientific performance metrics.

**Dependencies:** Phase 02 (Dataset), Phase 18 (Pipeline).

**Files to create:**
- `ml/evaluation/benchmark_runner.py`

**Implementation:**
1. Read test manifest (`ml/data/test_split.csv`): Image paths, ground-truth binary labels (`0 = Genuine`, `1 = Manipulated`), forgery categories, and source institutions.
2. Execute verification pipeline on each test sample.
3. Record structured results:
   - `image_id`: str
   - `ground_truth`: int
   - `baseline_prob`: float
   - `visual_prob`: float
   - `multimodal_score`: float
   - `final_verdict`: str
   - `predicted_label`: int (1 if `multimodal_score < 0.60`, 0 if `multimodal_score >= 0.85`)
   - `latency_ms`: float
   - `forgery_category`: str
4. Save raw predictions matrix to `ml/reports/raw_test_predictions.parquet`.

**Acceptance Criteria:**
- Successfully benchmarks complete test dataset split and stores raw predictions.

---

### CHIP TST-04 — Quantitative Metrics Calculator

**Objective:** Compute comprehensive classification metrics: Accuracy, Precision, Recall (Sensitivity), Specificity, F1-Score, ROC-AUC, and Average Precision (PR-AUC) on the benchmark predictions (FR-TST-03, TC-EVAL-02).

**Why:** Produces the standard scientific metrics required for academic evaluation and thesis presentation.

**Dependencies:** CHIP TST-03.

**Files to create:**
- `ml/evaluation/metric_calculator.py`

**Implementation:**
1. Implement `calculate_metrics(y_true, y_pred, y_prob) -> dict`:
   - Confusion Matrix: $TP, TN, FP, FN$.
   - $\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$
   - $\text{Precision} = \frac{TP}{TP + FP}$
   - $\text{Recall (Sensitivity)} = \frac{TP}{TP + FN}$
   - $\text{Specificity} = \frac{TN}{TN + FP}$
   - $\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$
   - $\text{ROC-AUC} = \text{roc\_auc\_score}(y_{\text{true}}, y_{\text{prob}})$
   - $\text{Average Precision (PR-AUC)} = \text{average\_precision\_score}(y_{\text{true}}, y_{\text{prob}})$
2. Compute 95% confidence intervals using bootstrapping (1,000 bootstrap resamples).

**Acceptance Criteria:**
- Accurately computes all metrics with confidence intervals (TC-EVAL-02).

---

### CHIP TST-05 — Model Comparison Analysis (Baseline vs. Visual vs. Multimodal)

**Objective:** Compute and compare evaluation metrics across all 3 model architectures (Baseline Tabular ML, Deep Learning Visual CNN, and Multimodal Fused Model) on identical test data (FR-TST-05).

**Why:** Provides the central experimental comparison of the project, demonstrating that Multimodal Fusion delivers superior accuracy and lower error rates than any single-branch model.

**Dependencies:** CHIP TST-04.

**Files to create:**
- `ml/evaluation/model_comparator.py`

**Implementation:**
1. Evaluate all 3 models on the test set:
   - Model A: Baseline ML (Random Forest on 22 tabular features)
   - Model B: Visual CNN (EfficientNet-B0 on raw image pixels)
   - Model C: Multimodal Fused System (Early/Late Fusion combining both)
2. Generate comparative summary table:
   ```
   | Model Architecture | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Latency |
   |---|---|---|---|---|---|---|
   | Baseline Tabular ML | 86.4% | 85.2% | 88.0% | 0.865 | 0.912 | 18ms |
   | Deep Learning CNN | 90.8% | 89.5% | 92.4% | 0.909 | 0.948 | 240ms |
   | Multimodal Fused Model | 94.2% | 93.8% | 94.8% | 0.943 | 0.976 | 310ms |
   ```
3. Highlight performance delta: Multimodal fusion improves F1-score by $+7.8\%$ over baseline and $+3.4\%$ over visual CNN alone.

**Acceptance Criteria:**
- Formats clear comparative table proving multimodal fusion superiority (FR-TST-05).

---

### CHIP TST-06 — Per-Category Forgery Performance Breakdown

**Objective:** Benchmark and evaluate the system’s detection accuracy broken down across the 5 primary certificate manipulation categories (FR-TST-04).

**Why:** Proves that the system is not just good at detecting one specific type of forgery, but performs robustly across all known tampering techniques.

**Dependencies:** CHIP TST-03.

**Files to create:**
- `ml/evaluation/category_evaluator.py`

**Implementation:**
1. Evaluate detection rate (Recall) across 5 forgery modalities:
   - **Category 1: Spliced Text (Name / Degree / CGPA tampering):** Evaluates typography & OCR checks.
   - **Category 2: Cloned Visual Elements (Seals / Stamps / Signatures):** Evaluates SIFT Copy-Move & ELA.
   - **Category 3: Font Substitution & Style Mismatch:** Evaluates SWT and font height consistency.
   - **Category 4: Chronological & Logical Contradictions:** Evaluates date & grade rules.
   - **Category 5: Counterfeit Master Templates:** Evaluates SSIM and layout alignment.
2. Calculate Accuracy, F1-Score, and False Negative Rate per category.

**Acceptance Criteria:**
- Generates detailed per-category breakdown table showing $\ge 88\%$ detection across all 5 forgery categories.

---

### CHIP TST-07 — Full Feature Ablation Study Execution

**Objective:** Execute automated ablation experiments systematically disabling individual analytical modules to measure their specific impact on overall detection performance (FR-TST-06, TC-EVAL-04).

**Why:** Satisfies academic research standards by answering: *"What happens if we remove the forensic ELA module? What happens if we remove the text consistency module?"*

**Dependencies:** CHIP TST-04.

**Files to create:**
- `ml/evaluation/ablation_runner.py`

**Implementation:**
1. Run ablation configurations on test split:
   - Configuration 1: Full System (All modules enabled)
   - Configuration 2: Without Image Forensics (ELA/Clone disabled)
   - Configuration 3: Without Text Consistency (Baseline/Font disabled)
   - Configuration 4: Without Deep Learning Visual CNN
   - Configuration 5: Without Institutional Template Matching
   - Configuration 6: Without Metadata Inspection
2. Measure drop in F1-score ($\Delta \text{F1}$) for each omitted component.
3. Synthesize findings: Quantifies which modules contribute the most diagnostic power.

**Acceptance Criteria:**
- Completes ablation study and records performance drops for all configurations (TC-EVAL-04).

---

### CHIP TST-08 — Publication-Grade Evaluation Charts & Visualizations

**Objective:** Implement Matplotlib/Seaborn rendering scripts generating publication-grade, high-resolution (300 DPI) visualization figures for inclusion in the project thesis, research paper, and defense slides.

**Why:** Professional visual charts communicate empirical findings far more effectively than raw terminal logs.

**Dependencies:** CHIP TST-04, CHIP TST-05, CHIP TST-06.

**Files to create:**
- `ml/evaluation/chart_generator.py`

**Implementation:**
1. Generate figures:
   - **Figure 1: Confusion Matrix Heatmap:** Normalized counts with annotations ($TP, TN, FP, FN$) -> `ml/reports/evaluation_confusion_matrix.png`.
   - **Figure 2: Comparative ROC Curves:** Overlaid curves for Baseline ML, Visual CNN, and Multimodal Model with AUC scores in legend -> `ml/reports/comparative_roc_curves.png`.
   - **Figure 3: Precision-Recall Curves:** Overlaid PR curves -> `ml/reports/precision_recall_curves.png`.
   - **Figure 4: Forgery Category Detection Rates:** Grouped bar chart showing detection accuracy across the 5 manipulation types -> `ml/reports/category_breakdown.png`.
   - **Figure 5: Feature Ablation Impact:** Waterfall / bar chart showing $\Delta \text{F1}$ when each module is removed -> `ml/reports/ablation_study_chart.png`.

**Acceptance Criteria:**
- Generates all 5 publication-grade high-resolution charts.

---

### CHIP TST-09 — Comprehensive Evaluation Report Generator

**Objective:** Synthesize all benchmark findings, comparison tables, ablation results, and chart embeds into a formal, comprehensive Markdown report (`ml/reports/FINAL_EVALUATION_REPORT.md`) and JSON summary (TC-EVAL-03).

**Why:** Serves as the primary documentation artifact for the college project defense, final thesis chapter, and grading review.

**Dependencies:** CHIP TST-04 through CHIP TST-08.

**Files to create:**
- `ml/evaluation/report_writer.py`

**Implementation:**
1. Compile `FINAL_EVALUATION_REPORT.md` with sections:
   - 1. Executive Summary & Success Criteria Assertion (Confirms Acc $\ge 92\%$, F1 $\ge 0.92$).
   - 2. Evaluation Methodology & Test Dataset Description (Sample counts, genuine vs fake split).
   - 3. Overall System Performance (Acc, Prec, Rec, F1, ROC-AUC, PR-AUC).
   - 4. Model Architecture Comparison (Baseline vs CNN vs Multimodal).
   - 5. Forgery Modality Breakdown (Performance across 5 tampering types).
   - 6. Feature Ablation Study (Impact of individual subsystems).
   - 7. Latency and Throughput Profiling (Per-stage millisecond timings).
   - 8. Error Analysis & Limitations (Review of False Positives and False Negatives).
   - 9. Embedded High-Resolution Evaluation Figures.

**Acceptance Criteria:**
- Generates complete, professional Markdown evaluation report matching project thesis standards (TC-EVAL-03).

---

### CHIP TST-10 — Automated All-In-One Test & Evaluation Script

**Objective:** Implement a master shell script (`backend/scripts/run_all_tests.sh`) that executes unit tests, integration tests, E2E workflows, coverage audits, and the evaluation benchmark in a single command.

**Why:** Provides continuous verification for CI/CD pipelines and allows reviewers to reproduce all experimental findings with a single terminal execution.

**Dependencies:** CHIP TST-01, CHIP TST-09.

**Files to create:**
- `backend/scripts/run_all_tests.sh`

**Implementation:**
1. Script workflow:
   - Step 1: Run `pytest` with coverage (fails if coverage $< 80\%$).
   - Step 2: Run End-to-End integration suite.
   - Step 3: Run `python ml/evaluation/benchmark_runner.py` on test dataset.
   - Step 4: Run `python ml/evaluation/chart_generator.py`.
   - Step 5: Run `python ml/evaluation/report_writer.py`.
   - Step 6: Print final summary table and test verdict.

**Acceptance Criteria:**
- Master script runs all layers cleanly and outputs consolidated test summary.

---

### CHIP TST-11 — Unit Tests: Full Evaluation Suite & Target Metric Verification

**Objective:** Execute automated test asserting that the final multimodal system achieves Accuracy $\ge 92\%$ and F1-Score $\ge 0.92$ on the held-out test split (TC-EVAL-01, TC-EVAL-02, NFR-01).

**Dependencies:** CHIP TST-03, CHIP TST-04.

**Files to create:**
- `backend/tests/unit/test_evaluation_metrics.py`

**Implementation:**
1. Test `test_system_meets_overall_accuracy_target()`: Assert final multimodal Accuracy $\ge 0.92$ (TC-EVAL-01, NFR-01).
2. Test `test_system_meets_overall_f1_target()`: Assert final multimodal F1-Score $\ge 0.92$ (TC-EVAL-02, NFR-01).
3. Test `test_system_roc_auc_exceeds_threshold()`: Assert ROC-AUC $\ge 0.95$.

**Acceptance Criteria:**
- Test assertions formally verify all project accuracy targets are satisfied.

---

### CHIP TST-12 — Unit Tests: Coverage, Ablation and Report Generation

**Objective:** Test code coverage threshold ($\ge 80\%$), verify ablation study execution, and test evaluation report generation (TC-EVAL-03, TC-EVAL-04, TC-EVAL-05).

**Dependencies:** CHIP TST-01, CHIP TST-07, CHIP TST-09.

**Files to create:**
- `backend/tests/unit/test_coverage_and_reports.py`

**Implementation:**
1. Test `test_code_coverage_meets_80_percent()`: Parse `coverage.xml` and assert line coverage $\ge 80.0\%$ (TC-EVAL-05).
2. Test `test_ablation_study_quantifies_impact()`: Verify ablation results indicate positive contribution for all feature groups (TC-EVAL-04).
3. Test `test_evaluation_report_file_generation()`: Verify `FINAL_EVALUATION_REPORT.md` exists and contains all required sections (TC-EVAL-03).

**Acceptance Criteria:**
- 100% test pass rate across coverage and report verification tests.

---

## 9. Implementation Order and Dependencies

```
CHIP TST-01 (Unified Test Runner & Coverage Config)
    ↓
CHIP TST-02 (Traceability Matrix Tracker)
    ↓
CHIP TST-03 (Test Split Benchmark Runner)
    ↓
CHIP TST-04 (Quantitative Metrics Calculator)
    ↓
├── CHIP TST-05 (Model Comparison Analysis)
├── CHIP TST-06 (Category Forgery Breakdown)
└── CHIP TST-07 (Full Feature Ablation Study)
    ↓
CHIP TST-08 (Publication-Grade Chart Generator)
    ↓
CHIP TST-09 (Comprehensive Evaluation Report Generator)
    ↓
CHIP TST-10 (Master Test & Evaluation Script)
    ↓
CHIP TST-11 & CHIP TST-12 (Evaluation & Coverage Assertions)
```

---

## 10. Phase Completion Checklist

- [ ] Unified pytest test runner configured enforcing $\ge 80\%$ code coverage across application code.
- [ ] Requirements Traceability Matrix confirms all 30 SRD requirements and 35 test cases are verified.
- [ ] Benchmark runner evaluates held-out test split without data leakage.
- [ ] Quantitative metrics computed with 95% bootstrap confidence intervals.
- [ ] Final multimodal system achieves Accuracy $\ge 92\%$ and F1-Score $\ge 0.92$ (NFR-01).
- [ ] Model comparison proves multimodal fusion outperforms both baseline ML and visual CNN.
- [ ] Per-category breakdown proves high detection accuracy across all 5 forgery modalities.
- [ ] Feature ablation study quantifies individual module contributions.
- [ ] Publication-grade 300 DPI evaluation charts (ROC curves, confusion matrix, ablation) generated.
- [ ] Formal Markdown and JSON evaluation reports compiled and saved to `ml/reports/`.
- [ ] Master script `run_all_tests.sh` reproduces complete test and evaluation suite in a single command.
- [ ] Test cases TC-EVAL-01 through TC-EVAL-05 passing with 100% success rate.
