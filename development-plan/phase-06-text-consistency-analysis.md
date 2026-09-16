# Phase 06 — Text Consistency Analysis

## 1. Purpose

Implement the text consistency and typographical forensics analysis module. This subsystem inspects the OCR-extracted text tokens and character bounding boxes to detect typographic anomalies introduced during digital certificate manipulation — including mismatched font families, inconsistent stroke weights or font sizes across parallel fields, baseline misalignment, abnormal character spacing (kerning), and date or grade logical contradictions. It generates an explainable text consistency score [0.0, 1.0] and pinpoints anomalous text regions.

## 2. Why This Phase Exists

When fraudsters manipulate academic certificates (e.g. replacing a student's name, changing a "Second Class" to "First Class with Distinction", or modifying graduation years), they rarely have access to the exact original digital typesetting templates or font files. Consequently:
- Inserted or edited text often uses a slightly different font family (e.g. Arial vs. Helvetica, or Times New Roman vs. Georgia).
- The bounding box height (font size) or stroke thickness (weight) of edited words deviates from the surrounding original text on the same line.
- Inserted text frequently exhibits baseline drift (characters sit a few pixels above or below the baseline of the pre-printed template).
- Kerning and inter-character spacing are irregular compared to professional typeset certificates.
- Logical contradictions occur (e.g. degree completion year is earlier than enrollment year, or issue date is in the future).

Detecting these micro-typographical discrepancies provides definitive forensic evidence of text-level certificate tampering.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-TXT-01** | Font consistency analysis (detect font size, style, weight, family variations across same-level text) | Bounding box aspect ratio analysis, stroke width transform (SWT), connected component analysis |
| **FR-TXT-02** | Character spacing and alignment analysis (baseline alignment, kerning, line spacing anomalies) | Linear regression baseline fitting, inter-token horizontal gap distribution |
| **FR-TXT-03** | Text formatting anomalies (mixed casing, irregular punctuation, unusual characters, date logic) | Grammatical, chronological, and score logic validators |
| **FR-TXT-04** | Generate text consistency score [0.0, 1.0] and highlight anomalous text regions | Weighted penalty score fusion and visual heatmap overlay generation |
| **NFR-01** | High forgery detection sensitivity on text-level manipulations | Multi-factor heuristic scoring with low false positive rate on legitimate certificates |
| **NFR-03** | Performance (< 2 seconds execution time) | Vectorized bounding box statistics and fast NumPy calculations |
| **TC-TXT-01** | Inconsistent font size detection test | Chip TXT-11 |
| **TC-TXT-02** | Misaligned text insertion / baseline drift detection test | Chip TXT-11 |
| **TC-TXT-03** | Character spacing / kerning irregularity detection test | Chip TXT-12 |
| **TC-TXT-04** | Text consistency composite score calculation test | Chip TXT-12 |

## 4. Inputs

- OCR tokens and structured lines from Phase 05 (`List[OCRToken]`, `List[TextLine]`).
- Preprocessed binarized image and grayscale image from Phase 04.
- Configuration parameters (baseline tolerance threshold in pixels, font size variation z-score threshold).

## 5. Outputs

- `TextConsistencyResult` Pydantic model containing:
  - `overall_text_consistency_score`: float [0.0, 1.0] (1.0 = completely consistent, 0.0 = highly anomalous)
  - `baseline_alignment_score`: float [0.0, 1.0]
  - `font_size_consistency_score`: float [0.0, 1.0]
  - `stroke_weight_consistency_score`: float [0.0, 1.0]
  - `spacing_consistency_score`: float [0.0, 1.0]
  - `logical_consistency_score`: float [0.0, 1.0]
  - `anomalous_regions`: List[AnomalousRegion] (bounding boxes, anomaly type, severity, description)
- Annotated visualization image highlighting suspicious text regions (`storage/reports/{uuid}_text_anomalies.png`).
- Populated database records in `text_consistency_result` table.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 04 (Preprocessing), Phase 05 (OCR).
- **Libraries:** `numpy`, `scipy` (statistical tests, linear regression), `opencv-python-headless`, `pydantic`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── text_consistency/
│   │       ├── __init__.py
│   │       ├── baseline_checker.py    # Baseline alignment and drift detection
│   │       ├── font_size_analyzer.py  # Font size and bounding box height distribution
│   │       ├── stroke_width_analyzer.py # Stroke Width Transform (SWT) & weight consistency
│   │       ├── spacing_analyzer.py    # Kerning and inter-character spacing analysis
│   │       ├── logical_validator.py   # Chronological and score logical consistency
│   │       ├── score_aggregator.py    # Composite score computation and penalty models
│   │       ├── visualizer.py          # Suspicious region highlighter rendering
│   │       └── service.py             # Orchestrator: TextConsistencyService
│   └── schemas/
│       └── text_consistency.py        # Pydantic schemas: TextConsistencyResult, Anomaly
└── tests/
    └── unit/
        ├── test_baseline_checker.py
        ├── test_font_size_analyzer.py
        ├── test_stroke_width_analyzer.py
        ├── test_spacing_analyzer.py
        ├── test_logical_validator.py
        └── test_text_consistency_service.py
```

---

## 8. Implementation Chips

---

### CHIP TXT-01 — Baseline Alignment and Text Drift Detector

**Objective:** Fit horizontal baselines across tokens within each text line and detect tokens whose vertical position deviates significantly from the expected baseline (FR-TXT-02).

**Why:** When text is digitally spliced into a certificate without sub-pixel alignment, the inserted characters often float 2–8 pixels above or below the baseline of the pre-existing text.

**Dependencies:** Phase 05 (OCR spatial reading order and tokens).

**Files to create:**
- `backend/app/modules/text_consistency/baseline_checker.py`

**Implementation:**
1. Implement `BaselineAlignmentAnalyzer`:
   - Iterate through each `TextLine` with at least 3 tokens.
   - Extract the bottom coordinate (`y_max`) of each token's bounding box.
   - Fit a robust linear baseline using RANSAC or Theil-Sen regression (resistant to outliers):
     `y_baseline = slope * x + intercept`.
   - Calculate the vertical residual distance `residual_i = |y_token_bottom - y_baseline(x)|` for every token.
2. Anomaly detection:
   - Calculate line-level standard deviation `sigma_baseline`.
   - A token is flagged as an alignment anomaly if its residual `residual_i > max(4.0, 2.5 * sigma_baseline)`.
3. Scoring:
   - Line alignment score: `exp(-mean_residual / 3.0)`.
   - Document baseline score: Average alignment score across all analyzed lines.
4. Record flagged tokens as `AnomalousRegion(type="baseline_drift", severity=float, bbox=token.bbox)`.

**Inputs:** List of `TextLine` objects containing constituent `OCRToken` bounding boxes.

**Outputs:** Baseline score float [0.0, 1.0], list of anomalous baseline drift regions.

**Testing:** Unit test on synthetic line with 4 aligned words and 1 word raised by 6 pixels (TC-TXT-02).

**Acceptance Criteria:**
- Detects baseline drift of >= 4 pixels on lines with >= 3 tokens.
- Ignores descenders (characters like 'g', 'y', 'p', 'q') using letter-level filtering.

---

### CHIP TXT-02 — Font Size & Height Distribution Analyzer

**Objective:** Measure token bounding box heights across lines and categories to detect anomalous words that are unusually larger or smaller than expected (FR-TXT-01).

**Why:** Spliced words (e.g. an altered name or grade) frequently suffer from scale mismatches — e.g. replacing a 12pt word with a 14pt word that doesn't fit the line's natural font metrics.

**Dependencies:** Phase 05 (OCR tokens).

**Files to create:**
- `backend/app/modules/text_consistency/font_size_analyzer.py`

**Implementation:**
1. Implement `FontSizeAnalyzer`:
   - For each line, compute the median token height: `median_h = np.median([t.bbox.height for t in line.tokens])`.
   - For every token on that line (excluding single-character tokens and punctuation):
     - Compute ratio: `height_ratio = token.bbox.height / median_h`.
     - If `height_ratio > 1.35` or `height_ratio < 0.72`, mark as candidate anomaly.
2. Group lines into typographic tiers:
   - Header tier (University name, large title: ~24–36pt)
   - Certificate declaration tier ("has been awarded...", ~14–18pt)
   - Student particulars tier (Name, Roll No, Branch: ~12–14pt)
   - Fine print / Footer tier (Signatures, dates, serial no: ~9–11pt)
3. Compute intra-tier height variance:
   - Flag any word whose height deviates by > 2.5 standard deviations from its tier median.
4. Compute `font_size_consistency_score`: `1.0 - min(1.0, 0.25 * num_anomalous_tokens)`.

**Inputs:** List of `TextLine` and `OCRToken` objects.

**Outputs:** Font size consistency score [0.0, 1.0], list of size anomaly regions.

**Testing:** Test on synthetic certificate where student name has 18px height while surrounding line text is 12px (TC-TXT-01).

**Acceptance Criteria:**
- Correctly identifies font size discrepancies exceeding 30% on the same text line.

---

### CHIP TXT-03 — Stroke Width Transform (SWT) & Weight Consistency Analyzer

**Objective:** Compute the Stroke Width Transform (SWT) across character regions to detect variations in font stroke thickness (boldness / weight) indicative of text insertion or manipulation (FR-TXT-01).

**Why:** Two fonts may have the same height, but an inserted word may be regular weight while the template used semi-bold, or vice-versa. SWT measures the distance between parallel character edges to calculate physical stroke width.

**Dependencies:** Phase 04 (Grayscale image), Phase 05 (OCR bounding boxes).

**Files to create:**
- `backend/app/modules/text_consistency/stroke_width_analyzer.py`

**Implementation:**
1. Implement Stroke Width Transform algorithm:
   - Compute image gradients $G_x, G_y$ using Sobel filters.
   - Detect edges using Canny edge detector: `edges = cv2.Canny(gray, 50, 150)`.
   - For each edge pixel $p$, shoot a ray in the gradient direction until reaching an opposite edge pixel $q$.
   - If gradient at $q$ points in opposite direction ($\nabla p \approx -\nabla q$), record Euclidean distance $\|p - q\|$ along the ray.
   - Assign the minimum stroke width value along the ray path.
2. Extract token-level stroke width statistics:
   - For each OCR token bounding box, crop the corresponding SWT map.
   - Calculate `mean_stroke_width` and `std_stroke_width` for the token.
3. Compare token stroke width against line median stroke width:
   - If `|token_stroke - median_stroke| / median_stroke > 0.40`:
     - Flag as `stroke_weight_anomaly`.
4. Compute `stroke_weight_consistency_score`: `1.0 - min(1.0, 0.2 * count_anomalous_strokes)`.

**Inputs:** Grayscale certificate image, list of `OCRToken` bounding boxes.

**Outputs:** Stroke weight consistency score [0.0, 1.0], list of stroke weight anomaly regions.

**Testing:** Test on certificate with one word artificially rendered in bold font within a regular text sentence.

**Acceptance Criteria:**
- Accurately detects bold/thin font weight discrepancies across characters on the same line.

---

### CHIP TXT-04 — Character Spacing & Kerning Irregularity Analyzer

**Objective:** Measure inter-token horizontal gaps and inter-character spacing consistency along each text line to identify abnormal character crowding or stretched tracking (FR-TXT-02).

**Why:** Forgers inserting words of different lengths into a constrained space (e.g. fitting a longer name into a pre-existing blank space) often artificially compress or expand character kerning, creating visible spacing anomalies.

**Dependencies:** Phase 05 (OCR tokens).

**Files to create:**
- `backend/app/modules/text_consistency/spacing_analyzer.py`

**Implementation:**
1. Implement `CharacterSpacingAnalyzer`:
   - For each line with $\ge 3$ tokens:
     - Compute horizontal gaps between adjacent tokens: `gap_i = token[i+1].bbox.x_min - token[i].bbox.x_max`.
     - Filter out negative gaps (overlapping tokens) or excessively wide margins (> 100px).
     - Calculate median gap and standard deviation of gaps along the line.
2. Detect spacing anomalies:
   - Negative gap: tokens visually overlap (`gap < 0`), indicating text collision during forgery.
   - Micro gap: `gap < 0.2 * median_gap`, indicating compressed text.
   - Macro gap: `gap > 2.5 * median_gap` in continuous text sentences.
3. Compute line spacing regularity (vertical distance between successive lines):
   - Measure $y$-distance between line baselines.
   - Flag any line with irregular leading (vertical line spacing discrepancy > 40%).
4. Compute `spacing_consistency_score`: `exp(-anomaly_penalty)`.

**Inputs:** List of `TextLine` objects.

**Outputs:** Spacing consistency score [0.0, 1.0], list of spacing anomaly regions.

**Testing:** Test on synthetic certificate with artificially compressed character spacing in the registration number (TC-TXT-03).

**Acceptance Criteria:**
- Detects overlapping characters, unnatural kerning gaps, and irregular line leading.

---

### CHIP TXT-05 — Text Formatting & Punctuation Anomaly Validator

**Objective:** Inspect extracted text for formatting irregularities including erratic capitalization, mixed character scripts (e.g. Cyrillic homoglyphs in Latin text), and ungrammatical punctuation patterns (FR-TXT-03).

**Why:** Counterfeiters occasionally use homoglyph substitution (e.g. replacing Latin 'a' with Cyrillic 'а') or introduce punctuation artifacts (double periods, mismatched quotes) during digital text replacement.

**Dependencies:** Phase 05 (OCR tokens).

**Files to create:**
- `backend/app/modules/text_consistency/format_checker.py`

**Implementation:**
1. Homoglyph and Unicode script check:
   - Inspect Unicode code points of all characters.
   - Flag mixed scripts within a single word (e.g. Cyrillic characters embedded in an English certificate).
2. Capitalization consistency check:
   - Academic certificates follow strict capitalization: Title Case or UPPERCASE.
   - Flag erratic mid-word capitalization: e.g. `cOMPUTER sCIENCE` or `JoHn dOE`.
3. Punctuation checks:
   - Flag unclosed parentheses, orphan commas, or misplaced hyphens in names and dates.
4. Calculate format penalty score: Subtract 0.1 for each critical formatting violation.

**Acceptance Criteria:**
- Catches homoglyph character substitutions and erratic capitalization.

---

### CHIP TXT-06 — Chronological & Logical Consistency Validator

**Objective:** Verify the temporal and numeric logic of extracted certificate fields to detect chronological impossibilities and invalid grade scales (FR-TXT-03).

**Why:** Even if an altered certificate looks visually clean, fraudsters frequently overlook real-world logical constraints:
- Issue date is in the future.
- Graduation year is earlier than institution founding year or enrollment year.
- CGPA is 10.5 on a 10.0 scale.
- Percentage is 105%.
- Examination date is on a Sunday or official national holiday.

**Dependencies:** Phase 05 (Extracted fields).

**Files to create:**
- `backend/app/modules/text_consistency/logical_validator.py`

**Implementation:**
1. Implement `LogicalConsistencyValidator`:
   - Receive `ExtractedCertificateFields` from Phase 05.
2. Temporal rules:
   - `issue_date <= current_date` (Issue date cannot be in the future).
   - `passing_year >= 1950` and `passing_year <= current_year`.
   - If enrollment year and passing year are both extracted: `3 <= (passing_year - enrollment_year) <= 6` (for standard 3–4 year degrees).
3. Numeric rules:
   - If CGPA extracted: `0.0 <= cgpa <= 10.0` (or `4.0` if US scale).
   - If percentage extracted: `35.0 <= percentage <= 100.0`.
   - Division consistency: If percentage < 60%, division cannot be "First Class with Distinction".
4. Penalty assignment:
   - Future issue date -> Critical failure (score reduced by 0.50).
   - Impossible grade -> Critical failure (score reduced by 0.40).
   - Invalid year sequence -> Major failure (score reduced by 0.35).

**Inputs:** `ExtractedCertificateFields` Pydantic model.

**Outputs:** Logical score [0.0, 1.0], list of logical contradiction errors.

**Testing:** Test with certificate dated 2035; verify logical score drops significantly and error is flagged.

**Acceptance Criteria:**
- Catches chronological errors, future dates, and impossible academic scores.

---

### CHIP TXT-07 — Composite Text Consistency Score Aggregator

**Objective:** Combine baseline alignment, font size, stroke weight, character spacing, formatting, and logical consistency scores into a unified, explainable `overall_text_consistency_score` [0.0, 1.0] (FR-TXT-04).

**Why:** Provides a single normalized feature for the downstream ML classifier and a clear, interpretable authenticity metric for verification reports.

**Dependencies:** CHIP TXT-01 through CHIP TXT-06.

**Files to create:**
- `backend/app/modules/text_consistency/score_aggregator.py`

**Implementation:**
1. Define weight configuration:
   - Baseline alignment: $w_{\text{baseline}} = 0.25$
   - Font size consistency: $w_{\text{size}} = 0.20$
   - Stroke weight (SWT): $w_{\text{stroke}} = 0.20$
   - Character spacing: $w_{\text{spacing}} = 0.15$
   - Logical consistency: $w_{\text{logic}} = 0.20$
2. Compute raw weighted composite score:
   $$S_{\text{raw}} = \sum w_i \cdot s_i$$
3. Apply critical veto penalty:
   - If any critical logical contradiction exists (e.g. future date or CGPA > 10.0), cap the overall score at a maximum of `0.40`.
   - If more than 3 distinct text anomaly regions are detected with high severity, apply exponential decay penalty.
4. Clamp final score strictly to $[0.0, 1.0]$.
5. Classify score into authenticity bands:
   - `0.85 - 1.00`: Consistent (No significant text anomalies)
   - `0.65 - 0.84`: Suspicious (Minor typographical or spacing irregularities)
   - `0.00 - 0.64`: Highly Anomalous (Strong evidence of text manipulation or splicing)

**Inputs:** Individual sub-scores and detected anomaly lists.

**Outputs:** Final composite score float and summary classification.

**Acceptance Criteria:**
- Produces balanced, normalized score [0.0, 1.0] reflecting overall text authenticity.

---

### CHIP TXT-08 — Text Anomaly Visualizer & Heatmap Overlay Generator

**Objective:** Generate an annotated visual image marking all detected text anomalies with color-coded bounding boxes and descriptive callouts (FR-TXT-04).

**Why:** Explaining why text was flagged is critical for user trust. Visual highlights allow university registrars and recruiters to instantly see which words or characters were flagged and why.

**Dependencies:** CHIP TXT-07.

**Files to create:**
- `backend/app/modules/text_consistency/visualizer.py`

**Implementation:**
1. Implement `render_text_anomaly_overlay(image: np.ndarray, anomalies: List[AnomalousRegion], output_path: Path) -> Path`:
   - Copy enhanced preprocessed certificate image.
   - For each anomaly in `anomalies`:
     - Select color based on anomaly type:
       - Baseline drift: Cyan (`#00E5FF`)
       - Font size mismatch: Yellow (`#FFD600`)
       - Stroke weight discrepancy: Magenta (`#E040FB`)
       - Spacing / kerning irregularity: Orange (`#FF6D00`)
       - Logical error: Red (`#D50000`)
     - Draw semi-transparent bounding box fill (alpha = 0.3) and solid border (thickness = 2px).
     - Render small text tag above box displaying anomaly type and severity percentage.
   - Save annotated image to `storage/reports/{uuid}_text_anomalies.png`.

**Acceptance Criteria:**
- Renders legible, high-contrast overlay highlighting all suspicious text locations.

---

### CHIP TXT-09 — Text Consistency Service Orchestrator

**Objective:** Wrap baseline, font size, stroke width, spacing, format, and logical analysis into a single unified `TextConsistencyService`.

**Why:** Provides a single entry point for pipeline execution, handles error recovery, and formats results for database storage.

**Dependencies:** CHIP TXT-01 through CHIP TXT-08.

**Files to create:**
- `backend/app/modules/text_consistency/service.py`

**Implementation:**
1. Implement `TextConsistencyService`:
   ```python
   class TextConsistencyService:
       def analyze(self, preprocessed_image: np.ndarray, ocr_tokens: List[OCRToken], text_lines: List[TextLine], extracted_fields: ExtractedCertificateFields, certificate_id: UUID) -> TextConsistencyResult:
           # 1. Run baseline alignment checker
           # 2. Run font size analyzer
           # 3. Run stroke width transform analyzer
           # 4. Run character spacing analyzer
           # 5. Run formatting & logical validator
           # 6. Compute composite score
           # 7. Render visualization overlay image
           # 8. Return TextConsistencyResult
   ```
2. Execution guard: Total execution time strictly monitored; timeout capped at 2.0 seconds (NFR-03).

**Acceptance Criteria:**
- Completes full text consistency analysis in < 2.0s per certificate.

---

### CHIP TXT-10 — Database Entity & Migration for Text Consistency Results

**Objective:** Create the SQLAlchemy model and Alembic migration for the `text_consistency_result` table (identified in Master Plan Supporting Requirements).

**Why:** The original Design Docs schema lacked a dedicated table for text consistency results. Storing these metrics in a dedicated table ensures traceability and fast querying for audit logs.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/models/text_consistency.py`
- Alembic migration script

**Implementation:**
1. Define `TextConsistencyModel(Base)`:
   - `id: UUID` (Primary Key)
   - `certificate_id: UUID` (Foreign Key -> `certificate.id`, indexed)
   - `overall_score: Float`
   - `baseline_score: Float`
   - `font_size_score: Float`
   - `stroke_weight_score: Float`
   - `spacing_score: Float`
   - `logical_score: Float`
   - `anomalous_regions_json: JSON`
   - `visualization_image_path: String`
   - `created_at: DateTime`
2. Create Alembic migration script and apply to database schema.

**Acceptance Criteria:**
- Database table created with foreign key indexing.

---

### CHIP TXT-11 — Unit Tests: Font Size and Baseline Drift Detection

**Objective:** Test automated detection of inconsistent font sizes and baseline alignment drift using synthetic test certificate lines (TC-TXT-01, TC-TXT-02).

**Dependencies:** CHIP TXT-01, CHIP TXT-02.

**Files to create:**
- `backend/tests/unit/test_baseline_checker.py`
- `backend/tests/unit/test_font_size_analyzer.py`

**Implementation:**
1. Test `test_detects_raised_word_on_baseline()`: Create line with 5 tokens, displace 3rd token by +6px. Verify baseline checker flags token with severity > 0.70 (TC-TXT-02).
2. Test `test_aligned_baseline_produces_high_score()`: Verify score >= 0.95 on perfectly straight text line.
3. Test `test_detects_oversized_font()`: Create line with 12px tokens and one 18px token. Verify font size analyzer flags anomaly (TC-TXT-01).

**Acceptance Criteria:**
- 100% test pass rate on synthetic font size and baseline drift test cases.

---

### CHIP TXT-12 — Unit Tests: Kerning, Composite Scoring & Logic

**Objective:** Test character spacing analysis, chronological logic validation, and composite score computation (TC-TXT-03, TC-TXT-04).

**Dependencies:** CHIP TXT-04, CHIP TXT-06, CHIP TXT-07.

**Files to create:**
- `backend/tests/unit/test_spacing_analyzer.py`
- `backend/tests/unit/test_logical_validator.py`
- `backend/tests/unit/test_text_consistency_service.py`

**Implementation:**
1. Test `test_detects_overlapping_tokens()`: Gap < 0 flags collision anomaly (TC-TXT-03).
2. Test `test_future_issue_date_triggers_penalty()`: Future date drops logical score < 0.50.
3. Test `test_composite_score_calculation()`: Verify weighted fusion formula and bounds [0.0, 1.0] (TC-TXT-04).

**Acceptance Criteria:**
- Verifies kerning anomaly detection, logical validation, and composite scoring.

---

## 9. Implementation Order and Dependencies

```
CHIP TXT-01 (Baseline Alignment)
    ↓
CHIP TXT-02 (Font Size Analyzer)
    ↓
CHIP TXT-03 (Stroke Width Transform) ──┐
    ↓                                  │
CHIP TXT-04 (Character Spacing)        │
    ↓                                  │
CHIP TXT-05 (Format & Script Check)    │
    ↓                                  │
CHIP TXT-06 (Logical Validator) ◄──────┘
    ↓
CHIP TXT-07 (Score Aggregator)
    ↓
CHIP TXT-08 (Visualizer & Heatmap)
    ↓
CHIP TXT-09 (Service Orchestrator)
    ↓
CHIP TXT-10 (Database Model & Migration)
    ↓
CHIP TXT-11 & CHIP TXT-12 (Unit Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Baseline alignment analyzer detects vertical drift of >= 4 pixels on text lines.
- [ ] Font size analyzer identifies words with bounding box heights deviating > 30% from line median.
- [ ] Stroke Width Transform detects bold/thin stroke weight inconsistencies.
- [ ] Character spacing analyzer flags token collisions, compressed kerning, and irregular line leading.
- [ ] Formatting validator catches mixed Unicode scripts (homoglyphs) and erratic capitalization.
- [ ] Logical validator flags future dates, invalid year sequences, and out-of-bound academic scores.
- [ ] Composite score aggregator produces explainable [0.0, 1.0] consistency score.
- [ ] Annotated overlay image generated highlighting anomaly locations with color-coded boxes.
- [ ] Full text consistency analysis completes in under 2.0 seconds per certificate.
- [ ] Test cases TC-TXT-01 through TC-TXT-04 passing with 100% success rate.
