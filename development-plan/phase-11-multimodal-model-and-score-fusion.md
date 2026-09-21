# Phase 11 — Multimodal Model & Score Fusion

## 1. Purpose

Implement the multimodal fusion and composite scoring subsystem. This module unites the two primary analytical branches:
1. **Visual Branch:** 512-dimensional CNN visual embeddings and raw pixel predictions from Phase 10.
2. **Textual / Tabular Branch:** 22-dimensional forensic and OCR feature vector from Phase 09, combined with text semantic embeddings from Phase 05.

It implements multiple fusion strategies (Early Feature Concatenation, Late Score Fusion, and Stacking Meta-Classifier), calculates the final **Composite Authenticity Score** $[0.0, 1.0]$, determines the final verification verdict (`AUTHENTIC`, `SUSPICIOUS`, `MANIPULATED`), and enforces strict institutional veto override rules based on database record verification (Phase 08).

## 2. Why This Phase Exists

Neither image pixels alone nor extracted text alone provide a complete picture of certificate authenticity:
- A visual CNN might detect a low-contrast signature border, but cannot know that the graduation date on the certificate post-dates the university's accreditation or that the roll number belongs to another student.
- An OCR text analysis might find the words grammatically correct, but miss that the gold university medallion was cloned from an internet thumbnail (pixel copy-move).
- Multimodal fusion combines visual textures, text semantics, forensic signatures, and database records into a single coherent judgment.
- By fusing complementary signals, the multimodal system surpasses individual branch performance, achieving the ultimate project milestone of $\ge 92\%$ Accuracy and $\ge 0.92$ F1-Score while providing clear, multi-tiered verdicts.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-FUS-01** | Two-branch multimodal architecture combining visual embeddings and tabular/text features | Feature fusion module uniting 512D visual embeddings and 22D tabular vectors |
| **FR-FUS-02** | Implement Early Fusion (feature concatenation + MLP) and Late Fusion (weighted score blending) | Dual-path fusion engine allowing configurable or comparative fusion modes |
| **FR-FUS-03** | Stacking Meta-Classifier (Logistic Regression / Shallow MLP on branch predictions) | Meta-learner trained on out-of-fold predictions from baseline and visual models |
| **FR-FUS-04** | Calculate final Composite Authenticity Score $[0.0, 1.0]$ and categorize into 3 verdicts | Calibrated score aggregator: `AUTHENTIC` ($\ge 0.85$), `SUSPICIOUS` ($0.60–0.84$), `MANIPULATED` ($< 0.60$) |
| **FR-FUS-05** | Enforce Institutional Veto Overrides based on Tier 1 and Tier 3 statuses | Ground-truth database veto logic overriding statistical model scores |
| **FR-FUS-06** | Multimodal target performance: Accuracy $\ge 92\%$, F1-Score $\ge 0.92$ | Optimal fusion weight tuning and threshold calibration |
| **NFR-01** | Accuracy ($\ge 92\%$ F1-score) | Synergistic multimodal model beating single-branch baselines |
| **NFR-03** | Performance (Fusion execution $< 100$ms) | Vectorized NumPy/PyTorch inference |
| **TC-FUS-01** | Early fusion feature concatenation and MLP training test | Chip FUS-11 |
| **TC-FUS-02** | Late fusion weighted score calculation test | Chip FUS-11 |
| **TC-FUS-03** | Stacking meta-classifier evaluation ($\ge 92\%$ Acc/F1) | Chip FUS-12 |
| **TC-FUS-04** | Authenticity verdict classification test (Authentic, Suspicious, Manipulated) | Chip FUS-12 |
| **TC-FUS-05** | Veto override rule enforcement test (Tier 1 & Tier 3) | Chip FUS-12 |

## 4. Inputs

- 22-dimensional tabular feature vector from Phase 09 (`TabularFeatureExtractor`).
- Baseline ML prediction probability ($P_{\text{tabular}}$) from Phase 09.
- 512-dimensional visual embedding vector from Phase 10 (`VisualEmbeddingExtractor`).
- Visual CNN prediction probability ($P_{\text{visual}}$) from Phase 10.
- Extracted OCR text corpus from Phase 05.
- Three-tier verification status (`TierStatus`: Tier 1, Tier 2, or Tier 3) from Phase 08.

## 5. Outputs

- `FinalVerificationDecision` Pydantic model containing:
  - `overall_authenticity_score`: float $[0.0, 1.0]$ (1.0 = Genuine, 0.0 = Manipulated)
  - `verdict`: `VerificationVerdict` (`AUTHENTIC`, `SUSPICIOUS`, `MANIPULATED`)
  - `confidence`: float $[0.0, 1.0]$
  - `visual_branch_score`: float
  - `tabular_branch_score`: float
  - `text_consistency_score`: float
  - `forensic_score`: float
  - `template_score`: float
  - `tier_status`: str
  - `veto_applied`: bool
  - `veto_reason`: Optional[str]
- Trained fusion model artifacts (`ml/models/multimodal_fusion_mlp.pt`, `ml/models/meta_classifier.joblib`).
- Comprehensive evaluation metrics report (`ml/reports/multimodal_metrics.json`).
- Database records in `verification_report` table.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 05 (OCR), Phase 08 (Records), Phase 09 (ML Baseline), Phase 10 (Deep Learning).
- **Libraries:** `torch`, `scikit-learn`, `numpy`, `scipy`, `pydantic`, `matplotlib`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── score_fusion/
│   │       ├── __init__.py
│   │       ├── early_fusion.py        # 534D concatenated feature MLP
│   │       ├── late_fusion.py         # Weighted heuristic and probability blender
│   │       ├── meta_classifier.py     # Stacking meta-learner (Logistic Regression / MLP)
│   │       ├── veto_rules.py          # Institutional ground-truth override rules
│   │       ├── verdict_engine.py      # Score categorization (Authentic / Suspicious / Manipulated)
│   │       └── service.py             # Orchestrator: ScoreFusionService
│   └── schemas/
│       └── decision.py                # Pydantic schemas: FinalVerificationDecision, Verdict
├── ml/
│   ├── scripts/
│   │   ├── train_early_fusion_mlp.py  # Trains multimodal neural network
│   │   ├── train_meta_classifier.py   # Trains stacking meta-learner
│   │   ├── evaluate_multimodal.py     # Benchmarks fusion models against test set
│   │   └── tune_fusion_weights.py     # Grid search for optimal late fusion weights
│   ├── models/
│   │   ├── multimodal_fusion_mlp.pt
│   │   └── meta_classifier.joblib
│   └── reports/
│       ├── multimodal_metrics.json
│       ├── multimodal_roc_curves.png
│       └── fusion_ablation_comparison.png
└── tests/
    └── unit/
        ├── test_early_fusion.py
        ├── test_late_fusion.py
        ├── test_meta_classifier.py
        ├── test_veto_rules.py
        └── test_verdict_engine.py
```

---

## 8. Implementation Chips

---

### CHIP FUS-01 — Multimodal Feature Fusion Representation (534D Vector)

**Objective:** Combine the 512-dimensional visual embedding vector with the 22-dimensional tabular feature vector into a unified 534-dimensional multimodal feature representation (FR-FUS-01).

**Why:** Early fusion requires a unified representation vector that captures both high-level visual/texture cues and granular heuristic metrics (ELA, baseline drift, OCR confidence).

**Dependencies:** Phase 09 (Tabular Features), Phase 10 (Visual Embeddings).

**Files to create:**
- `backend/app/modules/score_fusion/early_fusion.py`

**Implementation:**
1. Implement `concatenate_features(visual_embedding: np.ndarray, tabular_vector: np.ndarray) -> np.ndarray`:
   - Visual embedding shape: `(512,)` (L2-normalized float32).
   - Tabular vector shape: `(22,)` (standard-scaled float32).
   - Concatenate along axis 0:
     ```python
     fused_vector = np.concatenate(
         [visual_embedding, tabular_vector], axis=0
     )  # Shape (534,)
     ```
2. Verify dimensional integrity: `assert fused_vector.shape == (534,)`.
3. Check for NaN or Inf values and replace with zeros.

**Inputs:** 512D visual embedding, 22D tabular vector.

**Outputs:** 534D fused float32 vector.

**Acceptance Criteria:**
- Accurately constructs 534-dimensional multimodal feature vectors.

---

### CHIP FUS-02 — Early Fusion Multimodal Neural Network Architecture

**Objective:** Design and implement a Multi-Layer Perceptron (MLP) with residual connections and dropout that ingests the 534-dimensional fused representation and outputs an authenticity prediction (FR-FUS-02).

**Why:** A joint neural network learns complex cross-modal interactions (e.g. how a specific visual texture anomaly correlates with a high ELA variance and a dropped character confidence).

**Dependencies:** CHIP FUS-01.

**Files to modify:**
- `backend/app/modules/score_fusion/early_fusion.py`

**Implementation:**
1. Implement `MultimodalFusionMLP(nn.Module)`:
   ```python
   class MultimodalFusionMLP(nn.Module):
       def __init__(
           self,
           input_dim: int = 534,
           hidden_dims: List[int] = [256, 64],
           dropout_rate: float = 0.3,
       ):
           super().__init__()
           self.network = nn.Sequential(
               nn.Linear(input_dim, hidden_dims[0]),
               nn.BatchNorm1d(hidden_dims[0]),
               nn.ReLU(inplace=True),
               nn.Dropout(dropout_rate),
               nn.Linear(hidden_dims[0], hidden_dims[1]),
               nn.BatchNorm1d(hidden_dims[1]),
               nn.ReLU(inplace=True),
               nn.Dropout(dropout_rate),
               nn.Linear(hidden_dims[1], 1),  # Output logit
           )

       def forward(self, x: torch.Tensor) -> torch.Tensor:
           return self.network(x).squeeze(-1)
   ```
2. Export inference method returning probability: `prob_fake = torch.sigmoid(model(tensor)).item()`.

**Acceptance Criteria:**
- Passes forward pass cleanly with input shape `(B, 534)` and outputs valid logits `(B,)`.

---

### CHIP FUS-03 — Late Fusion Weighted Probability Blender

**Objective:** Implement a weighted late fusion score blender combining probabilities and sub-scores from the baseline ML model, the visual CNN model, the forensic engine, and the text consistency engine (FR-FUS-02).

**Why:** Late fusion provides an interpretable, transparent alternative to neural early fusion. Each branch contributes a configurable weight, allowing verification officers to see exactly how much weight came from visual AI vs forensic math.

**Dependencies:** Phases 06, 07, 08, 09, 10.

**Files to create:**
- `backend/app/modules/score_fusion/late_fusion.py`

**Implementation:**
1. Define late fusion weights (calibrated via optimization script):
   - Visual CNN probability: $w_{\text{visual}} = 0.30$
   - Tabular ML probability: $w_{\text{tabular}} = 0.30$
   - Forensic analysis score: $w_{\text{forensic}} = 0.15$
   - Text consistency score: $w_{\text{text}} = 0.15$
   - Template match score: $w_{\text{template}} = 0.10$
2. Compute composite authenticity score:
   $$\text{Authenticity Score} = w_v \cdot (1 - P_{\text{visual}}) + w_t \cdot (1 - P_{\text{tabular}}) + w_f \cdot S_{\text{forensic}} + w_x \cdot S_{\text{text}} + w_m \cdot S_{\text{template}}$$
   *(Note: $P_{\text{visual}}$ and $P_{\text{tabular}}$ represent probability of being fake; $1 - P$ represents probability of being authentic).*
3. Clamp score strictly into $[0.0, 1.0]$.
4. Return composite score and dictionary of weighted contributions.

**Acceptance Criteria:**
- Computes normalized composite authenticity score $[0.0, 1.0]$ within 2ms.

---

### CHIP FUS-04 — Stacking Meta-Classifier (Stacking Ensemble)

**Objective:** Train a Stacking Meta-Classifier (Logistic Regression or Shallow Gradient Booster) that takes the out-of-fold probability predictions from the Visual CNN, Baseline Random Forest, Forensics, and Text Consistency modules as input features (FR-FUS-03).

**Why:** Rather than relying on fixed human-chosen weights, a stacking meta-classifier automatically learns the optimal non-linear blending weights from data, typically delivering the highest overall accuracy.

**Dependencies:** CHIP FUS-02, CHIP FUS-03.

**Files to create:**
- `backend/app/modules/score_fusion/meta_classifier.py`
- `ml/scripts/train_meta_classifier.py`

**Implementation:**
1. Generate meta-training dataset using 5-fold cross-validation out-of-fold (OOF) predictions on the training set:
   - Feature 1: $P_{\text{visual\_fake}}$ (from Visual CNN)
   - Feature 2: $P_{\text{tabular\_fake}}$ (from Random Forest)
   - Feature 3: $S_{\text{forensic}}$ (from Phase 07)
   - Feature 4: $S_{\text{text\_consistency}}$ (from Phase 06)
   - Feature 5: $S_{\text{template\_ssim}}$ (from Phase 08)
2. Train meta-learner:
   - Primary: `LogisticRegression(C=1.0, penalty="l2")`
   - Secondary: `GradientBoostingClassifier(n_estimators=50, max_depth=3)`
3. Save trained meta-model to `ml/models/meta_classifier.joblib`.
4. Inference method: `predict_authenticity(meta_features) -> float` returning final authenticity probability $[0.0, 1.0]$.

**Acceptance Criteria:**
- Trains meta-classifier on OOF predictions and serializes model artifact (TC-FUS-03).

---

### CHIP FUS-05 — Institutional Veto Override Engine

**Objective:** Implement the deterministic institutional veto rules based on database record verification (Phase 08), overriding any statistical ML or DL score when authoritative ground truth exists (FR-FUS-05).

**Why:** Ground truth database records always supersede statistical predictions:
- If university records prove that roll number `1MS20CS001` belongs to "Alice Smith", but the certificate says "Bob Jones", the certificate is definitively forged—even if the image has a 99% authentic visual score!
- Conversely, if the certificate has an exact record match in the university database (Tier 1 Verified), minor scanner compression artifacts must not cause the certificate to be rejected.

**Dependencies:** Phase 08 (TierStatus & RecordVerificationResult).

**Files to create:**
- `backend/app/modules/score_fusion/veto_rules.py`

**Implementation:**
1. Implement `apply_institutional_vetoes(raw_authenticity_score: float, tier_result: TierClassification, record_result: RecordVerificationResult) -> Tuple[float, bool, Optional[str]]`:
   ```python
   # VETO 1: Definitive Inconsistency -> Force to MANIPULATED
   if tier_result.tier == TierStatus.TIER_3_INCONSISTENT:
       if record_result.record_found and (
           not record_result.name_match or not record_result.cgpa_match
       ):
           veto_score = min(raw_authenticity_score, 0.15)
           reason = f"CRITICAL VETO: Certificate details contradict official university database record ({record_result.discrepancies[0]})."
           return veto_score, True, reason

       if tier_result.primary_reason == "Counterfeit or mismatched template":
           veto_score = min(raw_authenticity_score, 0.25)
           reason = "CRITICAL VETO: Certificate visual structure contradicts registered university master template."
           return veto_score, True, reason

   # VETO 2: Ground-Truth Match -> Boost to AUTHENTIC
   if tier_result.tier == TierStatus.TIER_1_VERIFIED:
       veto_score = max(raw_authenticity_score, 0.95)
       reason = "CONFIRMATION VETO: Exact student record match verified in official university database."
       return veto_score, True, reason

   # No veto applied: Maintain statistical score
   return raw_authenticity_score, False, None
   ```

**Inputs:** Raw composite score, tier classification, record verification result.

**Outputs:** Final adjusted score $[0.0, 1.0]$, boolean `veto_applied`, string `veto_reason`.

**Testing:**
- Test Tier 3 name mismatch with 0.95 ML score -> forced down to $\le 0.15$ (TC-FUS-05).
- Test Tier 1 verified record with 0.70 ML score -> boosted to $\ge 0.95$ (TC-FUS-05).

**Acceptance Criteria:**
- Strictly overrides statistical predictions when institutional ground truth exists.

---

### CHIP FUS-06 — Verdict Classification & Confidence Rating Engine

**Objective:** Map the final Composite Authenticity Score into the three canonical project verdicts (`AUTHENTIC`, `SUSPICIOUS`, `MANIPULATED`) with calibrated confidence percentages (FR-FUS-04).

**Why:** End users (employers, university registrars) require a definitive categorical verdict alongside the numeric score.

**Dependencies:** CHIP FUS-05.

**Files to create:**
- `backend/app/modules/score_fusion/verdict_engine.py`

**Implementation:**
1. Define verdict thresholds:
   - **`AUTHENTIC`:** $\text{Score} \ge 0.85$ (High confidence genuine certificate; no evidence of manipulation).
   - **`SUSPICIOUS`:** $0.60 \le \text{Score} < 0.85$ (Inconclusive; minor typographical anomalies, unverified template, or low OCR confidence; requires manual human review).
   - **`MANIPULATED`:** $\text{Score} < 0.60$ (High confidence fraudulent certificate; detected tampering, clone, or database contradiction).
2. Calculate confidence percentage:
   - For `AUTHENTIC`: $\text{Confidence} = \frac{\text{Score} - 0.85}{0.15} \times 30\% + 70\% \in [70\%, 100\%]$.
   - For `MANIPULATED`: $\text{Confidence} = \frac{0.60 - \text{Score}}{0.60} \times 30\% + 70\% \in [70\%, 100\%]$.
   - For `SUSPICIOUS`: Confidence reflects uncertainty (e.g. $50\% - 65\%$).
3. Generate concise human-readable summary rationale explaining the verdict.

**Acceptance Criteria:**
- Accurately maps scores to the three canonical verdict tiers with human-readable rationale (TC-FUS-04).

---

### CHIP FUS-07 — Multimodal Model Evaluation & Benchmark Verification

**Objective:** Benchmark all fusion approaches (Early, Late, Stacking) on the held-out test set and verify that the best multimodal model satisfies the contractual project target of Accuracy $\ge 92\%$ and F1-Score $\ge 0.92$ (FR-FUS-06, NFR-01).

**Why:** Proves that multimodal fusion outperforms both the standalone ML baseline (85%) and the standalone Visual CNN (90%), achieving peak project accuracy.

**Dependencies:** CHIP FUS-02, CHIP FUS-03, CHIP FUS-04.

**Files to create:**
- `ml/scripts/evaluate_multimodal.py`

**Implementation:**
1. Evaluate on test set for all 3 fusion methods:
   - Method 1: Early Fusion MLP
   - Method 2: Late Fusion Weighted Blender
   - Method 3: Stacking Meta-Classifier
2. Compute metrics for each: Accuracy, Precision, Recall, F1-Score, ROC-AUC.
3. Compare against single-branch baselines:
   - Baseline Tabular Model: ~86% F1
   - Visual CNN Model: ~90% F1
   - Multimodal Fused Model: Target $\ge 92\%$ F1
4. Check contractual assertion:
   ```python
   assert best_f1 >= 0.92, f"Multimodal F1 {best_f1} below 0.92 specification"
   assert best_accuracy >= 0.92, (
       f"Multimodal accuracy {best_accuracy} below 0.92 specification"
   )
   ```
5. Save evaluation comparison charts and JSON report to `ml/reports/multimodal_metrics.json`.

**Acceptance Criteria:**
- Best multimodal fusion model achieves Accuracy $\ge 92\%$ and F1-Score $\ge 0.92$ (TC-FUS-03).

---

### CHIP FUS-08 — Production Score Fusion Service Orchestrator

**Objective:** Implement the production `ScoreFusionService` that coordinates feature concatenation, model inference, late fusion blending, veto evaluation, and verdict generation.

**Why:** Serves as the central decision brain of the entire verification pipeline.

**Dependencies:** CHIP FUS-01 through CHIP FUS-07.

**Files to create:**
- `backend/app/modules/score_fusion/service.py`

**Implementation:**
1. Implement `ScoreFusionService`:
   ```python
   class ScoreFusionService:
       def __init__(self, meta_model_path: Path, config: FusionConfig):
           self.meta_model = joblib.load(meta_model_path)
           self.config = config

       def fuse_and_decide(
           self,
           certificate_id: UUID,
           visual_result: VisualPredictionResult,
           tabular_result: PredictionResult,
           text_result: TextConsistencyResult,
           forensic_result: ForensicAnalysisResult,
           template_result: TemplateMatchResult,
           tier_result: TierClassification,
           record_result: RecordVerificationResult
       ) -> FinalVerificationDecision:
           # 1. Compute statistical authenticity probability using Meta-Classifier
           # 2. Compute Late Fusion score for explainability breakdown
           # 3. Apply Institutional Veto Rules
           # 4. Map final score to Verdict (AUTHENTIC, SUSPICIOUS, MANIPULATED)
           # 5. Persist decision to database
           # 6. Return FinalVerificationDecision
   ```
2. Wrap execution with timing guard ($< 100$ms).

**Acceptance Criteria:**
- Executes complete multimodal fusion and verdict determination in $< 50$ms.

---

### CHIP FUS-09 — Database Entity for Verification Decisions

**Objective:** Map final verification decisions into the `verification_report` table according to the Design Documents schema.

**Why:** Stores the overall authenticity score, individual sub-scores, verdict tier, and veto rationale for permanent audit logs and report generation.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/models/report.py`
- Alembic migration script

**Implementation:**
1. Map `VerificationReportModel(Base)` matching Design Docs:
   - `id: UUID` (Primary Key)
   - `certificate_id: UUID` (Foreign Key -> `certificate.id`, indexed)
   - `overall_score: Float`
   - `verdict: String` (`AUTHENTIC`, `SUSPICIOUS`, `MANIPULATED`)
   - `confidence_score: Float`
   - `sub_scores_json: JSON` (visual, tabular, text, forensic, template scores)
   - `veto_applied: Boolean`
   - `veto_reason: Text`
   - `created_at: DateTime`

**Acceptance Criteria:**
- Database entity matches Design Documents schema specification.

---

### CHIP FUS-10 — Fusion CLI Diagnostics & Simulation Script

**Objective:** Build a CLI utility to simulate score fusion and test veto logic on arbitrary combinations of sub-scores without running full image pipelines.

**Dependencies:** CHIP FUS-08.

**Files to create:**
- `backend/scripts/simulate_fusion.py`

**Acceptance Criteria:**
- Accepts CLI arguments (`--visual-score`, `--forensic-score`, `--tier`) and prints fused score and verdict.

---

### CHIP FUS-11 — Unit Tests: Early and Late Fusion Calculations

**Objective:** Test 534D feature concatenation, Early Fusion MLP forward pass, and Late Fusion weighted score calculation (TC-FUS-01, TC-FUS-02).

**Dependencies:** CHIP FUS-01, CHIP FUS-02, CHIP FUS-03.

**Files to create:**
- `backend/tests/unit/test_early_fusion.py`
- `backend/tests/unit/test_late_fusion.py`

**Implementation:**
1. Test `test_feature_concatenation_534d()`: Verify shape `(534,)` (TC-FUS-01).
2. Test `test_early_fusion_mlp_output()`: Forward pass returns probability bounded in $[0.0, 1.0]$.
3. Test `test_late_fusion_weighted_calculation()`: Verify mathematical weighted blend formula (TC-FUS-02).

**Acceptance Criteria:**
- 100% test pass rate on early and late fusion modules.

---

### CHIP FUS-12 — Unit Tests: Meta-Classifier, Verdicts & Veto Overrides

**Objective:** Test stacking meta-classifier evaluation, 3-tier verdict classification, and institutional veto rule enforcement (TC-FUS-03, TC-FUS-04, TC-FUS-05).

**Dependencies:** CHIP FUS-04, CHIP FUS-05, CHIP FUS-06.

**Files to create:**
- `backend/tests/unit/test_meta_classifier.py`
- `backend/tests/unit/test_veto_rules.py`
- `backend/tests/unit/test_verdict_engine.py`

**Implementation:**
1. Test `test_multimodal_evaluation_meets_92_percent()`: Verify test set F1 $\ge 0.92$ and Accuracy $\ge 0.92$ (TC-FUS-03, NFR-01).
2. Test `test_verdict_tier_mapping()`: Verify score $\ge 0.85$ maps to `AUTHENTIC`, $0.60–0.84$ to `SUSPICIOUS`, and $< 0.60$ to `MANIPULATED` (TC-FUS-04).
3. Test `test_tier_3_veto_overrides_high_ml_score()`: Verify Tier 3 mismatch forces verdict to `MANIPULATED` (TC-FUS-05).
4. Test `test_tier_1_veto_boosts_score()`: Verify Tier 1 verified record boosts score to $\ge 0.95$ (TC-FUS-05).

**Acceptance Criteria:**
- All tests pass with full verification of verdict boundaries and veto overrides.

---

## 9. Implementation Order and Dependencies

```
CHIP FUS-01 (534D Multimodal Representation)
    ↓
CHIP FUS-02 (Early Fusion MLP) ──────────┐
    ↓                                    │
CHIP FUS-03 (Late Fusion Weighted Blender)
    ↓                                    │
CHIP FUS-04 (Stacking Meta-Classifier) ◄─┘
    ↓
CHIP FUS-05 (Institutional Veto Overrides)
    ↓
CHIP FUS-06 (Verdict & Confidence Engine)
    ↓
CHIP FUS-07 (Multimodal Evaluation Benchmark)
    ↓
CHIP FUS-08 (Score Fusion Production Service)
    ↓
CHIP FUS-09 (Database Model) & CHIP FUS-10 (Simulation CLI)
    ↓
CHIP FUS-11 & CHIP FUS-12 (Unit Tests)
```

---

## 10. Phase Completion Checklist

- [ ] 512D visual embeddings and 22D tabular features concatenated into 534D multimodal representation.
- [ ] Early fusion MLP trained with residual connections and dropout.
- [ ] Late fusion weighted blender provides explainable sub-score contribution breakdown.
- [ ] Stacking meta-classifier trained on out-of-fold branch predictions.
- [ ] Multimodal fusion achieves test Accuracy $\ge 92\%$ and F1-Score $\ge 0.92$ (FR-FUS-06, NFR-01).
- [ ] Institutional veto rules strictly override statistical ML scores when database ground truth exists.
- [ ] Verdict engine maps scores into `AUTHENTIC`, `SUSPICIOUS`, and `MANIPULATED` with calibrated confidence.
- [ ] Production service executes complete fusion and decision generation in $< 50$ms.
- [ ] Final decisions persisted to `verification_report` database table.
- [ ] Test cases TC-FUS-01 through TC-FUS-05 passing with 100% success rate.
