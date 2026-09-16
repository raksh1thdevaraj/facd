# Phase 12 — Explainability & Suspicious Regions

## 1. Purpose

Implement the comprehensive explainability and suspicious region localization subsystem. This module transforms complex AI predictions (Grad-CAM heatmaps, SHAP feature attributions, forensic pixel maps, and typographical anomalies) into clear, transparent, human-readable explanations. It maps all detected anomalies back to the original document's coordinate space, generates a unified multi-layer visual overlay, and synthesizes natural-language bullet points justifying the verification verdict for university registrars, HR recruiters, and forensic examiners.

## 2. Why This Phase Exists

AI-based fraud detection cannot be a "black box":
- Academic and legal decisions carry profound consequences. A student falsely accused of submitting a forged certificate must have the right to transparent evidence; similarly, an employer rejecting a candidate must have clear documentation.
- Institutional users do not understand raw neural network weights or eigenvalues. They need plain-language explanations: *"The student's name exhibits a 4-pixel vertical baseline misalignment, and the university seal shares 12 identical cloned feature points with another document region."*
- Different analytical engines produce different spatial artifacts: Phase 06 produces character bounding boxes; Phase 07 produces pixel heatmaps and SIFT clone lines; Phase 10 produces Grad-CAM thermal maps.
- This phase unifies these disparate visual and textual findings into a single, intuitive evidence dossier.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-EXP-01** | Visual explainability: Grad-CAM heatmaps and forensic bounding boxes | PyTorch Grad-CAM integration and composite anomaly bounding box renderer |
| **FR-EXP-02** | Textual explainability: Highlight anomalous text regions (font, spacing, alignment) | OCR coordinate mapper highlighting typography flaws |
| **FR-EXP-03** | Feature attribution explainability: Tabular feature contributions using SHAP / TreeExplainer | SHAP TreeExplainer integration computing local feature attribution values |
| **FR-EXP-04** | Natural language explanation generation: Human-readable bullet points | Template-driven and rule-based NLG engine summarizing findings |
| **FR-EXP-05** | Unified spatial coordinate mapping onto original document resolution | Inverse homography/scale transformer mapping preprocessed boxes to raw image |
| **NFR-01** | Explainable, non-black-box AI system | Transparent multi-factor evidence presentation |
| **NFR-03** | Performance (< 2 seconds execution time) | Optimized SHAP TreeExplainer and fast coordinate transformations |
| **TC-EXP-01** | SHAP / TreeExplainer local feature attribution test | Chip EXP-11 |
| **TC-EXP-02** | Grad-CAM heatmap visual overlay test | Chip EXP-11 |
| **TC-EXP-03** | Text anomaly coordinate mapping test | Chip EXP-12 |
| **TC-EXP-04** | Natural language explanation synthesis test | Chip EXP-12 |
| **TC-EXP-05** | Unified multi-layer spatial overlay test | Chip EXP-12 |

## 4. Inputs

- Final verification decision and sub-scores from Phase 11 (`FinalVerificationDecision`).
- 22-dimensional tabular feature vector from Phase 09.
- Trained Random Forest model from Phase 09.
- Grad-CAM heatmap array from Phase 10.
- Forensic findings and clone matches from Phase 07.
- Text consistency anomalies from Phase 06.
- Database record verification discrepancies from Phase 08.
- Raw original certificate image and preprocessed coordinate scaling factors.

## 5. Outputs

- `ExplainabilityReport` Pydantic model containing:
  - `primary_verdict_rationale`: str (Executive summary paragraph)
  - `key_findings`: List[FindingBullet] (Severity, category, title, detailed description)
  - `top_contributing_features`: List[FeatureAttribution] (Feature name, value, SHAP impact)
  - `spatial_anomalies`: List[UnifiedAnomalyBox] (Category, label, coordinates on raw image)
- High-resolution unified visual evidence image (`storage/reports/{uuid}_unified_evidence.png`).
- Populated explainability JSON stored in `verification_report` table.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 05 (OCR), Phases 06–11 (All analytical modules).
- **Libraries:** `shap`, `numpy`, `opencv-python-headless`, `Pillow`, `pydantic`, `matplotlib`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── explainability/
│   │       ├── __init__.py
│   │       ├── coordinate_mapper.py   # Maps bounding boxes between raw and processed images
│   │       ├── shap_explainer.py      # SHAP TreeExplainer for tabular feature attribution
│   │       ├── nlg_generator.py       # Natural Language Generation for human explanations
│   │       ├── unified_overlay.py     # Multi-layer visual evidence renderer
│   │       └── service.py             # Orchestrator: ExplainabilityService
│   └── schemas/
│       └── explainability.py          # Pydantic schemas: ExplainabilityReport, FindingBullet
└── tests/
    └── unit/
        ├── test_coordinate_mapper.py
        ├── test_shap_explainer.py
        ├── test_nlg_generator.py
        ├── test_unified_overlay.py
        └── test_explainability_service.py
```

---

## 8. Implementation Chips

---

### CHIP EXP-01 — Spatial Coordinate Mapping & Rescaling Engine

**Objective:** Map bounding boxes, keypoints, and polygon coordinates from preprocessed / downscaled image spaces back to the exact pixel coordinates of the original uploaded document (FR-EXP-05).

**Why:** Preprocessing scales, rotates, and unwarps certificates. If an anomaly is detected at $(x', y')$ in a $512 \times 512$ or deskewed image, highlighting that region on the high-resolution original document requires applying the exact inverse transformation matrix.

**Dependencies:** Phase 04 Preprocessing.

**Files to create:**
- `backend/app/modules/explainability/coordinate_mapper.py`

**Implementation:**
1. Implement `CoordinateMapper`:
   - Store transformation metadata: `scale_factor_x`, `scale_factor_y`, `rotation_matrix_inv`, `perspective_matrix_inv`.
2. Implement `map_box_to_original(box: BoundingBox) -> BoundingBox`:
   - If perspective was corrected: Apply `cv2.perspectiveTransform(pts, H_inv)`.
   - If deskewed: Apply inverse rotation matrix around image center.
   - Scale coordinates by `(orig_width / proc_width, orig_height / proc_height)`.
   - Clamp coordinates strictly to `[0, orig_width - 1]` and `[0, orig_height - 1]`.
3. Support batch mapping for list of bounding boxes and polygon point arrays.

**Inputs:** Bounding box coordinates in processed space, transformation parameters.

**Outputs:** Bounding box coordinates in original raw image space.

**Acceptance Criteria:**
- Accurately maps coordinates back to original image space within $\pm 2$ pixels.

---

### CHIP EXP-02 — SHAP Local Feature Attribution for Tabular Model

**Objective:** Integrate SHAP (SHapley Additive exPlanations) using `shap.TreeExplainer` on the Random Forest baseline model to compute local feature contributions for the specific certificate being analyzed (FR-EXP-03).

**Why:** Explains *why* the tabular ML model classified the document as fake. SHAP values mathematically allocate the exact percentage contribution of each feature (e.g. *"ELA score increased fake probability by +32%; Baseline drift increased it by +18%; Clear OCR decreased it by -8%"*).

**Dependencies:** Phase 09 ML Baseline.

**Files to create:**
- `backend/app/modules/explainability/shap_explainer.py`

**Implementation:**
1. Implement `SHAPTabularExplainer`:
   - Pre-initialize `shap.TreeExplainer(model)` at server startup to eliminate per-request overhead.
   - Expose `explain_instance(feature_vector: np.ndarray, feature_names: List[str]) -> List[FeatureAttribution]`:
     ```python
     shap_values = self.explainer.shap_values(feature_vector.reshape(1, -1))
     # For binary classification, take SHAP values for class 1 (Manipulated)
     values = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]
     ```
2. Sort features by absolute SHAP value descending.
3. Extract top 5 positive contributors (factors pushing towards `MANIPULATED`) and top 3 negative contributors (factors pushing towards `AUTHENTIC`).
4. Generate waterfall / bar summary plot if requested -> `storage/reports/{uuid}_shap_waterfall.png`.

**Acceptance Criteria:**
- Computes local SHAP attributions in $< 80$ms using pre-initialized TreeExplainer (TC-EXP-01).

---

### CHIP EXP-03 — Natural Language Explanation (NLG) Engine

**Objective:** Implement a rule-based Natural Language Generation (NLG) engine that synthesizes raw forensic scores, OCR findings, and database lookups into fluent, professional bullet points for human reviewers (FR-EXP-04).

**Why:** Verification officers require concise, plain-English explanations rather than raw float numbers or matrices.

**Dependencies:** Phase 05 (OCR), Phase 06 (Text), Phase 07 (Forensics), Phase 08 (Records), Phase 11 (Decision).

**Files to create:**
- `backend/app/modules/explainability/nlg_generator.py`

**Implementation:**
1. Implement `NLGExplanationGenerator`:
   - Generate **Executive Summary Paragraph**:
     - E.g.: *"Certificate verification completed with status **MANIPULATED** (Authenticity Score: 24%). Strong mathematical and visual evidence indicates digital tampering in the student degree classification and university seal regions."*
   - Generate **Key Findings Bullets** grouped by severity (`CRITICAL`, `MAJOR`, `WARNING`, `INFO`):
     - **Database Discrepancy:** *"Student name on certificate ('Johnathan Doe') does not match university records ('Jonathan M. Doe') registered under Roll Number 1MS20CS042."*
     - **Visual Clone / Stamp:** *"Confirmed Copy-Move duplication detected: the institutional seal matches another region with 14 verified SIFT keypoint clusters."*
     - **Typographical Anomaly:** *"Font baseline drift of 6.2 pixels detected in text line 'FIRST CLASS WITH DISTINCTION', indicating post-print digital insertion."*
     - **Compression Discrepancy:** *"Error Level Analysis (ELA) reveals severe JPEG recompression inconsistency (score: 0.32) concentrated around the grade block."*
     - **Chronological Logic:** *"Date of issue (15 August 2026) is in the future relative to the verification timestamp."*
     - **Pristine Findings (if Authentic):** *"Typography, font metrics, and inter-character spacing are uniform throughout. No compression or cloning artifacts detected. Document matches authentic university layout standards."*

**Acceptance Criteria:**
- Generates professional, grammatically correct explanations covering all detected anomaly categories (TC-EXP-04).

---

### CHIP EXP-04 — Multi-Layer Unified Spatial Overlay Renderer

**Objective:** Render a unified visual evidence image overlaying Grad-CAM heatmaps, SIFT clone lines, text anomaly boxes, and low-confidence OCR regions onto the high-resolution certificate canvas (FR-EXP-01, FR-EXP-02, FR-EXP-05).

**Why:** Provides an all-in-one visual summary document that an officer can print or attach to an official verification report.

**Dependencies:** CHIP EXP-01, Phase 06 (Text), Phase 07 (Forensics), Phase 10 (Grad-CAM).

**Files to create:**
- `backend/app/modules/explainability/unified_overlay.py`

**Implementation:**
1. Implement `UnifiedOverlayRenderer`:
   - Canvas: High-resolution original certificate image.
2. Layer 1: Semi-transparent Grad-CAM / ELA thermal heatmap (alpha = 0.25).
3. Layer 2: Copy-Move clone indicators:
   - Yellow solid polygons over source and destination cloned regions.
   - Dotted cyan connection lines between paired keypoints.
4. Layer 3: Text anomaly bounding boxes:
   - Red border (thickness = 3px) for baseline drift or font size mismatches.
   - Small label pill above box: e.g. `[Font Mismatch: +35% Size]`.
5. Layer 4: Low-confidence OCR fields:
   - Amber dashed box for OCR confidence $< 0.70$.
6. Legend banner: Render dark semi-transparent legend footer at bottom of image explaining color codes.
7. Save high-resolution composite to `storage/reports/{uuid}_unified_evidence.png`.

**Acceptance Criteria:**
- Generates composite multi-layer visualization clearly highlighting all visual and textual anomalies (TC-EXP-02, TC-EXP-05).

---

### CHIP EXP-05 — Explainability Service Orchestrator

**Objective:** Wire coordinate mapping, SHAP attribution, NLG synthesis, and unified visual rendering into the production `ExplainabilityService`.

**Why:** Single entry point for pipeline execution, producing structured Pydantic models for frontend display and PDF report inclusion.

**Dependencies:** CHIP EXP-01 through CHIP EXP-04.

**Files to create:**
- `backend/app/modules/explainability/service.py`

**Implementation:**
1. Implement `ExplainabilityService`:
   ```python
   class ExplainabilityService:
       def generate_explanation(
           self,
           certificate_id: UUID,
           raw_image_path: Path,
           decision: FinalVerificationDecision,
           tabular_features: np.ndarray,
           text_result: TextConsistencyResult,
           forensic_result: ForensicAnalysisResult,
           tier_result: TierClassification,
           record_result: RecordVerificationResult,
           gradcam_path: Optional[Path]
       ) -> ExplainabilityReport:
           # 1. Map all anomaly coordinates back to original image space
           # 2. Compute local SHAP feature attributions
           # 3. Generate natural language summary and bullet points
           # 4. Render unified multi-layer visual evidence image
           # 5. Return ExplainabilityReport
   ```
2. Timing constraint: Complete execution in $< 2.0$ seconds (NFR-03).

**Acceptance Criteria:**
- Completes full explainability pipeline within 2.0 seconds per certificate.

---

### CHIP EXP-06 — Interactive Bounding Box JSON Exporter for Frontend

**Objective:** Export a structured, lightweight JSON payload containing normalized bounding box coordinates $[0.0, 1.0]$, tooltips, severity ratings, and category filters for interactive React frontend rendering.

**Why:** Allows the frontend user interface to draw interactive SVG/Canvas highlight overlays directly over the certificate image with hoverable tooltips.

**Dependencies:** CHIP EXP-01.

**Files to create:**
- `backend/app/schemas/interactive_overlay.py`

**Implementation:**
1. Structure:
   ```json
   {
     "certificate_id": "uuid",
     "image_dimensions": {"width": 2480, "height": 3508},
     "anomalies": [
       {
         "id": "anom_1",
         "category": "TEXT_ALIGNMENT",
         "severity": "CRITICAL",
         "box": {"x": 420, "y": 1250, "w": 380, "h": 45},
         "normalized_box": {"x": 0.169, "y": 0.356, "w": 0.153, "h": 0.012},
         "title": "Baseline Drift",
         "description": "Text sits 5.8px below expected baseline.",
         "color": "#D50000"
       }
     ]
   }
   ```

**Acceptance Criteria:**
- Provides normalized coordinates ready for client-side responsive SVG overlay rendering.

---

### CHIP EXP-07 — Explainability CLI Tool

**Objective:** Build a CLI tool to run explainability analysis on an analyzed certificate and print the natural language findings and SHAP attributions to the terminal.

**Dependencies:** CHIP EXP-05.

**Files to create:**
- `backend/scripts/run_explainability.py`

**Acceptance Criteria:**
- Prints formatted terminal report with ANSI colors displaying executive summary and findings.

---

### CHIP EXP-08 — Unit Tests: Coordinate Mapping and Invariant Bounds

**Objective:** Test inverse coordinate transformation from preprocessed space to original raw resolution across scaling, deskewing, and perspective warps (TC-EXP-03).

**Dependencies:** CHIP EXP-01.

**Files to create:**
- `backend/tests/unit/test_coordinate_mapper.py`

**Implementation:**
1. Test `test_coordinate_scaling()`: Box at $(100, 100, 50, 20)$ in $500 \times 500$ maps to $(200, 200, 100, 40)$ in $1000 \times 1000$ canvas.
2. Test `test_boundary_clamping()`: Coordinates never exceed original image bounds.
3. Test `test_deskew_coordinate_inversion()`: Verify rotated box maps back to original unrotated canvas (TC-EXP-03).

**Acceptance Criteria:**
- 100% test pass rate on coordinate mapping routines.

---

### CHIP EXP-09 — Unit Tests: SHAP Attribution & Feature Ranking

**Objective:** Test SHAP TreeExplainer local attribution calculation and verify top contributing features are properly extracted and ranked (TC-EXP-01).

**Dependencies:** CHIP EXP-02.

**Files to create:**
- `backend/tests/unit/test_shap_explainer.py`

**Implementation:**
1. Test `test_shap_attribution_computation()`: Assert SHAP values sum to model prediction minus base expected value (TC-EXP-01).
2. Test `test_top_features_sorted()`: Verify returned feature list is sorted by absolute impact descending.

**Acceptance Criteria:**
- Verifies mathematical consistency of SHAP values.

---

### CHIP EXP-10 — Unit Tests: NLG Synthesis and Unified Visual Overlay

**Objective:** Test natural language explanation synthesis and verify generation of unified visual evidence overlay image (TC-EXP-02, TC-EXP-04, TC-EXP-05).

**Dependencies:** CHIP EXP-03, CHIP EXP-04, CHIP EXP-05.

**Files to create:**
- `backend/tests/unit/test_nlg_generator.py`
- `backend/tests/unit/test_unified_overlay.py`
- `backend/tests/unit/test_explainability_service.py`

**Implementation:**
1. Test `test_nlg_generates_correct_verdict_summary()`: Verify executive summary matches verdict (TC-EXP-04).
2. Test `test_unified_overlay_generates_valid_image()`: Verify multi-layer overlay produces valid PNG file with legend (TC-EXP-02, TC-EXP-05).
3. Test `test_explainability_latency_under_2s()`: Benchmark end-to-end explainability generation time (NFR-03).

**Acceptance Criteria:**
- All explainability unit tests pass within performance thresholds.

---

## 9. Implementation Order and Dependencies

```
CHIP EXP-01 (Spatial Coordinate Mapping)
    ↓
CHIP EXP-02 (SHAP Feature Attribution) ──┐
    ↓                                    │
CHIP EXP-03 (NLG Explanation Generator) │
    ↓                                    │
CHIP EXP-04 (Unified Multi-Layer Overlay)◄┘
    ↓
CHIP EXP-05 (Explainability Service Orchestrator)
    ↓
CHIP EXP-06 (Interactive JSON Exporter) & CHIP EXP-07 (CLI Tool)
    ↓
CHIP EXP-08, EXP-09, EXP-10 (Unit Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Spatial coordinate mapper accurately transforms bounding boxes from preprocessed space back to original raw image resolution.
- [ ] SHAP TreeExplainer computes local feature attributions, explaining the exact positive and negative drivers of the prediction.
- [ ] Natural Language Generation engine synthesizes clear, human-readable bullet points covering all detected anomalies.
- [ ] Multi-layer unified visual evidence image generated with Grad-CAM heatmaps, clone lines, and text anomaly boxes.
- [ ] Normalized JSON payload exported for interactive SVG/Canvas bounding box rendering in frontend.
- [ ] Full explainability pipeline executes in under 2.0 seconds per certificate.
- [ ] Test cases TC-EXP-01 through TC-EXP-05 passing with 100% success rate.
