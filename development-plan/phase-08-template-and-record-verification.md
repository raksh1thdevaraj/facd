# Phase 08 — Template & Record Verification

## 1. Purpose

Implement the template matching and institutional record verification engine. This subsystem performs dual-track verification:
1. **Visual Template Matching:** Compares the uploaded certificate against registered institutional certificate templates using Structural Similarity Index (SSIM), feature alignment, and seal/logo bounding box verification.
2. **Database Record Cross-Verification:** Queries registered institution databases (`institution_record` table) using OCR-extracted student particulars (Roll Number, Name, Degree, Passing Year, CGPA) to confirm authentic issuance.
3. **Three-Tier Classification:** Classifies the certificate into **Tier 1 (Verified)**, **Tier 2 (Consistent)**, or **Tier 3 (Unverified / Inconsistent)** according to FR-TMP-03.

## 2. Why This Phase Exists

While AI and computer vision models detect subtle tampering, the gold standard of certificate verification is comparing against the issuing university's official records and template layout:
- If a student's roll number and degree match an authorized institutional record in the database, authenticity is confirmed with 100% ground-truth certainty (Tier 1).
- When institutional records are not available (e.g. historical archives or non-integrated universities), template matching verifies that the certificate follows the exact geometric layout, borders, seal placement, and typography of known genuine certificates issued by that institution (Tier 2).
- If the student's name on the certificate contradicts the name registered under that roll number in the university database, or if the layout deviates radically from the university's authentic template, the certificate is immediately flagged as fraudulent (Tier 3).

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-TMP-01** | Template matching against registered templates (SSIM, feature matching, seal/logo placement) | Template alignment pipeline, SSIM evaluator, seal ROI detector |
| **FR-TMP-02** | Student record cross-verification against institutional database | Fuzzy database matcher comparing Name, Roll No, Degree, Year, Marks |
| **FR-TMP-03** | Three-tier match status: Tier 1 (Verified), Tier 2 (Consistent), Tier 3 (Unverified/Inconsistent) | Three-tier decision engine with confidence scoring |
| **FR-TMP-04** | Manual template registration for new institutions | Template registration service with anchor point and ROI definition |
| **NFR-01** | Accurate record matching with typo tolerance | Levenshtein distance and token sort fuzzy matching |
| **NFR-03** | Performance (Template match < 3s, record query < 500ms) | Pre-computed template feature descriptors, indexed DB lookups |
| **TC-TMP-01** | Valid template matching test (SSIM >= 0.85) | Chip TMP-12 |
| **TC-TMP-02** | Counterfeit template matching test (SSIM < 0.60) | Chip TMP-12 |
| **TC-TMP-03** | Exact student record match test -> Tier 1 Verified | Chip TMP-13 |
| **TC-TMP-04** | Mismatched student record test -> Tier 3 Inconsistent | Chip TMP-13 |
| **TC-TMP-05** | Missing student record test -> Tier 2 Consistent | Chip TMP-13 |
| **TC-TMP-06** | Template registration and storage test | Chip TMP-13 |

## 4. Inputs

- Preprocessed enhanced image from Phase 04.
- Extracted certificate fields from Phase 05 (`ExtractedCertificateFields`: Name, Roll No, Degree, Year, Institution, CGPA).
- Registered template records from `institution_template` table.
- Registered student records from `institution_record` table.

## 5. Outputs

- `TemplateMatchResult` containing:
  - `template_id`: Optional[UUID]
  - `ssim_score`: float [0.0, 1.0]
  - `feature_similarity_score`: float [0.0, 1.0]
  - `seal_match_score`: float [0.0, 1.0]
  - `overall_template_score`: float [0.0, 1.0]
- `RecordVerificationResult` containing:
  - `record_found`: bool
  - `matched_record_id`: Optional[UUID]
  - `name_match_score`: float [0.0, 1.0]
  - `roll_no_match`: bool
  - `degree_match`: bool
  - `passing_year_match`: bool
  - `cgpa_match`: bool
  - `discrepancies`: List[str]
- `TierStatus`: `TIER_1_VERIFIED`, `TIER_2_CONSISTENT`, or `TIER_3_UNVERIFIED`.
- Populated database records in `template_match_result` table.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 04 (Preprocessing), Phase 05 (OCR).
- **Libraries:** `opencv-python-headless`, `scikit-image` (`metrics.structural_similarity`), `numpy`, `rapidfuzz`, `sqlalchemy`, `pydantic`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── template_matching/
│   │       ├── __init__.py
│   │       ├── aligner.py             # Feature-based homography alignment (ORB/ECC)
│   │       ├── ssim_evaluator.py      # Structural Similarity Index calculation
│   │       ├── seal_matcher.py        # Seal, emblem, and logo ROI verification
│   │       ├── layout_comparator.py   # Text block spatial layout comparison
│   │       ├── record_verifier.py     # Database cross-referencing and fuzzy field matching
│   │       ├── tier_classifier.py     # Three-Tier decision engine (Tier 1/2/3)
│   │       ├── registration_service.py # Template registration and anchor specification
│   │       └── service.py             # Orchestrator: VerificationEngine
│   └── schemas/
│       └── template_matching.py       # Pydantic schemas: TemplateResult, RecordResult, TierStatus
└── tests/
    └── unit/
        ├── test_template_aligner.py
        ├── test_ssim_evaluator.py
        ├── test_seal_matcher.py
        ├── test_record_verifier.py
        ├── test_tier_classifier.py
        └── test_template_registration.py
```

---

## 8. Implementation Chips

---

### CHIP TMP-01 — Template Feature Alignment & Homography Warping

**Objective:** Align the uploaded certificate image to the reference institutional template using ORB feature detection, RANSAC homography, and sub-pixel Enhanced Correlation Coefficient (ECC) alignment (FR-TMP-01).

**Why:** Pixel-level comparison (SSIM, seal matching) requires sub-pixel spatial registration between the uploaded document and the master template. Alignment compensates for minor residual scaling and cropping differences.

**Dependencies:** Phase 04 Preprocessing.

**Files to create:**
- `backend/app/modules/template_matching/aligner.py`

**Implementation:**
1. Implement `align_to_template(query_img: np.ndarray, template_img: np.ndarray) -> Tuple[np.ndarray, float, bool]`:
   - Convert both images to grayscale and resize query image to match template dimensions.
   - Detect ORB features:
     ```python
     orb = cv2.ORB_create(nfeatures=2000)
     kp1, des1 = orb.detectAndCompute(query_img, None)
     kp2, des2 = orb.detectAndCompute(template_img, None)
     ```
   - Match descriptors using `cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)`.
   - Sort matches by distance; retain top 15% best matches.
   - Estimate homography matrix using RANSAC:
     ```python
     H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
     ```
   - If inlier ratio < 0.20, alignment failed (images are fundamentally different templates).
   - Warp query image to template coordinate space:
     `aligned_img = cv2.warpPerspective(query_img, H, (template_img.shape[1], template_img.shape[0]))`.
2. Refine alignment using ECC (Enhanced Correlation Coefficient) optimization for sub-pixel accuracy.
3. Return `aligned_image`, `inlier_ratio`, and `alignment_success`.

**Inputs:** Query certificate image, reference template image.

**Outputs:** Aligned query image array, feature alignment score float [0.0, 1.0].

**Acceptance Criteria:**
- Successfully aligns valid certificate to master template with sub-pixel registration.
- Returns `alignment_success=False` if query image does not match template layout.

---

### CHIP TMP-02 — Structural Similarity Index (SSIM) Evaluator

**Objective:** Compute the global and regional Structural Similarity Index (SSIM) between the aligned certificate and the master template, masking out variable student text (FR-TMP-01).

**Why:** SSIM measures structural, luminance, and contrast consistency. Genuine certificates share the exact structural border, background guilloche patterns, watermark positioning, and header layout as the master template.

**Dependencies:** CHIP TMP-01.

**Files to create:**
- `backend/app/modules/template_matching/ssim_evaluator.py`

**Implementation:**
1. Implement `compute_template_ssim(aligned_img: np.ndarray, template_img: np.ndarray, variable_mask: Optional[np.ndarray] = None) -> Tuple[float, np.ndarray]`:
   - If `variable_mask` is provided: Mask out variable text areas (Student Name, Roll No, Date) so individual student details do not penalize template score.
   - Compute full structural similarity map using `skimage.metrics.structural_similarity`:
     ```python
     score, ssim_diff_map = structural_similarity(
         template_gray, aligned_gray,
         multichannel=False,
         full=True,
         gaussian_weights=True,
         sigma=1.5
     )
     ```
   - If variable mask exists, compute masked mean: `masked_score = float(np.mean(ssim_diff_map[variable_mask == 0]))`.
2. Evaluate thresholds:
   - Genuine template match: $\text{SSIM} \ge 0.85$ (TC-TMP-01).
   - Suspicious / modified template: $0.60 \le \text{SSIM} < 0.85$.
   - Mismatched / counterfeit template: $\text{SSIM} < 0.60$ (TC-TMP-02).
3. Return `ssim_score` and normalized `ssim_diff_map` (for visual reporting).

**Acceptance Criteria:**
- Genuine certificates achieve $\text{SSIM} \ge 0.85$.
- Fake or altered layouts yield $\text{SSIM} < 0.60$.

---

### CHIP TMP-03 — Institutional Seal, Logo & Emblem Verifier

**Objective:** Extract the university seal / emblem Region of Interest (ROI) from the query certificate and compare it against the master template seal using multi-scale template matching and color histogram correlation (FR-TMP-01).

**Why:** Counterfeit certificates frequently substitute a low-resolution web logo or incorrect university emblem. Inspecting the seal ROI ensures the emblem geometry, embossed texture, and color profile match authentic standards.

**Dependencies:** CHIP TMP-01.

**Files to create:**
- `backend/app/modules/template_matching/seal_matcher.py`

**Implementation:**
1. Define seal ROI coordinates `(x, y, w, h)` from template metadata.
2. Crop seal from aligned query image and template image.
3. Multi-scale template matching:
   - Run `cv2.matchTemplate(query_seal, template_seal, cv2.TM_CCOEFF_NORMED)`.
   - Calculate maximum correlation coefficient `r_max`.
4. Color histogram comparison:
   - Convert seals to HSV color space.
   - Calculate 2D Hue-Saturation histograms.
   - Compute Bhattacharyya distance / correlation using `cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)`.
5. Compute composite `seal_match_score = 0.65 * r_max + 0.35 * hist_corr`.
6. Flag if seal is missing, distorted, or significantly miscolored.

**Acceptance Criteria:**
- Accurately validates presence and authenticity of institutional seals.
- Flags missing or replaced logos with score < 0.50.

---

### CHIP TMP-04 — Database Student Record Cross-Referencing Service

**Objective:** Query the `institution_record` database table to find matching student records and verify extracted OCR fields against official university database entries (FR-TMP-02).

**Why:** Direct verification against institutional records provides absolute ground truth. If the roll number exists in the university database and matches the student name, degree, and passing year, the certificate is verified at the highest tier (Tier 1).

**Dependencies:** Phase 01 Foundation, Phase 05 (Extracted fields).

**Files to create:**
- `backend/app/modules/template_matching/record_verifier.py`

**Implementation:**
1. Query strategy:
   - Primary lookup: Query `institution_record` by exact `roll_number` and `institution_id`.
   - Fallback lookup: If exact roll number fails, query by normalized `student_name` and `degree_program`.
2. Field comparison and fuzzy matching:
   - **Student Name Match:**
     - Normalize strings (uppercase, strip punctuation, honorifics).
     - Calculate Levenshtein similarity: `ratio = rapidfuzz.fuzz.token_sort_ratio(extracted_name, db_record.student_name)`.
     - `name_match = ratio >= 85` (tolerates minor OCR character misrecognitions).
   - **Roll Number Match:**
     - Exact alphanumeric match (case-insensitive).
   - **Degree Match:**
     - Fuzzy match against `db_record.degree_name` (`ratio >= 80`).
   - **Passing Year Match:**
     - Strict numeric equality: `extracted_year == db_record.passing_year`.
   - **CGPA / Marks Match:**
     - Numeric tolerance: `abs(extracted_cgpa - db_record.cgpa) <= 0.05`.
3. Discrepancy reporting:
   - If record found but name differs (e.g. ratio < 60), generate explicit discrepancy: `"Name on certificate ('{extracted}') does not match university record ('{db_name}') for roll number {roll_no}."`
   - If CGPA differs, generate discrepancy: `"CGPA on certificate ({extracted}) contradicts institutional record ({db_cgpa})."`

**Inputs:** `ExtractedCertificateFields` model, database session.

**Outputs:** `RecordVerificationResult` containing match flags, fuzzy scores, and discrepancy list.

**Acceptance Criteria:**
- Verifies records in database within 300ms using indexed lookups.
- Correctly identifies exact matches, minor OCR typos (fuzzy match), and blatant discrepancies.

---

### CHIP TMP-05 — Three-Tier Match Status Decision Engine

**Objective:** Implement the definitive three-tier verification status decision engine according to FR-TMP-03 specifications.

**Why:** Translates complex mathematical scores and database lookups into actionable, industry-standard verification tiers for academic institutions and employers:
- **Tier 1 (Verified):** Exact or high-confidence student record match in official database.
- **Tier 2 (Consistent):** No database record found, but template match score $\ge 0.80$, text layout consistent, and no forensic anomalies.
- **Tier 3 (Unverified / Inconsistent):** Database record mismatch (name/marks contradiction), unknown institution, or template match score $< 0.60$.

**Dependencies:** CHIP TMP-02, CHIP TMP-03, CHIP TMP-04.

**Files to create:**
- `backend/app/modules/template_matching/tier_classifier.py`

**Implementation:**
1. Implement `classify_tier(record_result: RecordVerificationResult, template_result: TemplateMatchResult, forensic_score: float, text_score: float) -> TierClassification`:
   ```python
   # Rule 1: Definitive Inconsistency -> Tier 3
   if record_result.record_found:
       if not record_result.name_match or not record_result.degree_match or not record_result.cgpa_match:
           return TierClassification(tier=TierStatus.TIER_3_INCONSISTENT, reason="Database record mismatch")

   if template_result.overall_template_score < 0.60:
       return TierClassification(tier=TierStatus.TIER_3_INCONSISTENT, reason="Counterfeit or mismatched template")

   # Rule 2: Ground-Truth Match -> Tier 1
   if record_result.record_found and record_result.name_match and record_result.roll_no_match:
       return TierClassification(tier=TierStatus.TIER_1_VERIFIED, reason="Authentic record verified in university database")

   # Rule 3: Visual & Typographic Consistency -> Tier 2
   if template_result.overall_template_score >= 0.80 and forensic_score >= 0.70 and text_score >= 0.70:
       return TierClassification(tier=TierStatus.TIER_2_CONSISTENT, reason="Layout consistent with registered template; record not in database")

   # Fallback -> Tier 3
   return TierClassification(tier=TierStatus.TIER_3_UNVERIFIED, reason="Insufficient verification evidence or record not found")
   ```

**Inputs:** Record verification result, template match result, forensic score, text score.

**Outputs:** `TierClassification` (`tier: TierStatus`, `confidence: float`, `primary_reason: str`).

**Testing:**
- Test exact DB match -> Tier 1 (TC-TMP-03).
- Test mismatched name -> Tier 3 (TC-TMP-04).
- Test no record found + high template score -> Tier 2 (TC-TMP-05).
- Test low template score -> Tier 3 (TC-TMP-05).

**Acceptance Criteria:**
- Strictly implements FR-TMP-03 logic.
- Returns transparent, human-readable justification for the assigned tier.

---

### CHIP TMP-06 — Institutional Template Registration Service

**Objective:** Implement service and API endpoints to allow administrators and partner universities to register official certificate templates, define variable text regions, and upload emblem masks (FR-TMP-04).

**Why:** Enables the system to scale to new universities and degrees over time by onboarding their master templates into the verification database.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/template_matching/registration_service.py`
- `backend/app/api/v1/endpoints/templates.py`

**Implementation:**
1. Implement `register_institution_template(...)`:
   - Store high-resolution master template image in `storage/templates/{institution_id}_{template_id}.png`.
   - Pre-compute and serialize ORB/SIFT feature descriptors to disk (`.npz` format) for fast matching.
   - Record metadata in `institution_template` database table:
     - `institution_id`, `template_name`, `degree_program`, `effective_year_start`, `effective_year_end`
     - `seal_roi_json` (`[x, y, width, height]`)
     - `variable_regions_json` (bounding boxes for student name, roll number, date to mask during SSIM)
2. Expose `POST /api/v1/institutions/{id}/templates` endpoint with validation.

**Acceptance Criteria:**
- Stores master template, pre-computes feature descriptors, and indexes in database (TC-TMP-06).

---

### CHIP TMP-07 — Student Record Ingestion & Bulk CSV Import Service

**Objective:** Implement CSV/Excel bulk import service allowing university registrars to populate the `institution_record` table with authorized student graduation data.

**Why:** Populates the database required for Tier 1 record verification.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/template_matching/record_importer.py`
- `backend/app/api/v1/endpoints/records.py`

**Implementation:**
1. Support CSV upload with columns: `student_name`, `roll_number`, `degree_name`, `passing_year`, `cgpa_or_marks`, `issue_date`.
2. Validate data types and check for duplicate roll numbers.
3. Bulk insert into `institution_record` table with hashed indices for fast retrieval.

**Acceptance Criteria:**
- Imports 5,000 student records in < 2.0 seconds.

---

### CHIP TMP-08 — Template & Record Verification Orchestrator Service

**Objective:** Integrate template alignment, SSIM evaluation, seal verification, database record matching, and three-tier classification into the unified `VerificationEngineService`.

**Dependencies:** CHIP TMP-01 through CHIP TMP-07.

**Files to create:**
- `backend/app/modules/template_matching/service.py`

**Implementation:**
1. Implement `VerificationEngineService`:
   ```python
   class VerificationEngineService:
       def verify(self, preprocessed_image: np.ndarray, extracted_fields: ExtractedCertificateFields, forensic_score: float, text_score: float, db: Session) -> VerificationEngineResult:
           # 1. Look up institution by name or ID
           # 2. If institution has registered template, run template alignment + SSIM + seal match
           # 3. Query student records in database
           # 4. Classify into Tier 1, 2, or 3
           # 5. Save results to template_match_result table
           # 6. Return composite result
   ```

**Acceptance Criteria:**
- Executes complete template and record verification within 3.0 seconds total.

---

### CHIP TMP-09 — Database Entities for Templates and Records

**Objective:** Define SQLAlchemy models for `institution_template`, `institution_record`, and `template_match_result` matching the Design Documents schema.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/models/template.py`
- `backend/app/models/record.py`
- Alembic migration script

**Implementation:**
1. Model `InstitutionTemplate`:
   - `id: UUID`, `institution_id: UUID`, `template_name: String`, `image_path: String`, `feature_data_path: String`, `seal_roi: JSON`, `variable_mask_path: String`.
2. Model `InstitutionRecord`:
   - `id: UUID`, `institution_id: UUID`, `student_name: String`, `roll_number: String` (indexed), `degree_name: String`, `passing_year: Integer`, `cgpa: Float`.
3. Model `TemplateMatchResult`:
   - `id: UUID`, `certificate_id: UUID`, `template_id: Optional[UUID]`, `ssim_score: Float`, `seal_score: Float`, `tier_status: String`, `discrepancy_notes: Text`.

**Acceptance Criteria:**
- Database schema matches Design Documents Part E.

---

### CHIP TMP-10 — Template Match Visual Diff Generator

**Objective:** Generate a visual side-by-side comparison and SSIM difference heatmap showing layout discrepancies between the query certificate and the authentic master template.

**Why:** Allows verification officers to visually inspect layout differences (e.g. shifted signature block or altered border pattern).

**Dependencies:** CHIP TMP-02.

**Files to create:**
- `backend/app/modules/template_matching/visual_diff.py`

**Implementation:**
1. Generate false-color difference map from SSIM:
   - Identical areas appear green/gray; differing areas appear bright red.
2. Render side-by-side composite: `[ Master Template | Query Certificate | SSIM Difference Heatmap ]`.
3. Save to `storage/reports/{uuid}_template_diff.png`.

**Acceptance Criteria:**
- Visual diff clearly highlights layout modifications and border changes.

---

### CHIP TMP-11 — Verification Engine Diagnostics & Index Benchmarks

**Objective:** Implement health checks verifying template storage availability, descriptor cache integrity, and database query response times (< 500ms benchmark).

**Dependencies:** CHIP TMP-08.

**Files to create:**
- `backend/app/modules/template_matching/diagnostics.py`

**Acceptance Criteria:**
- Verifies sub-500ms database index query performance.

---

### CHIP TMP-12 — Unit Tests: Template Alignment and SSIM Evaluation

**Objective:** Test template matching accuracy on genuine and counterfeit certificate layouts (TC-TMP-01, TC-TMP-02).

**Dependencies:** CHIP TMP-01, CHIP TMP-02.

**Files to create:**
- `backend/tests/unit/test_ssim_evaluator.py`

**Implementation:**
1. Test `test_genuine_template_yields_high_ssim()`: Aligned genuine certificate achieves SSIM >= 0.85 (TC-TMP-01).
2. Test `test_counterfeit_template_yields_low_ssim()`: Mismatched template produces SSIM < 0.60 (TC-TMP-02).
3. Test `test_seal_verification_detects_altered_logo()`: Mismatched seal produces seal score < 0.50.

**Acceptance Criteria:**
- Accurately discriminates genuine from counterfeit layouts based on SSIM.

---

### CHIP TMP-13 — Unit Tests: Record Cross-Verification and Three-Tier Status

**Objective:** Test student record verification across exact match, mismatched records, missing records, and verify template registration (TC-TMP-03, TC-TMP-04, TC-TMP-05, TC-TMP-06).

**Dependencies:** CHIP TMP-04, CHIP TMP-05, CHIP TMP-06.

**Files to create:**
- `backend/tests/unit/test_record_verifier.py`
- `backend/tests/unit/test_tier_classifier.py`
- `backend/tests/unit/test_template_registration.py`

**Implementation:**
1. Test exact database match -> Tier 1 Verified (TC-TMP-03).
2. Test mismatched name or CGPA -> Tier 3 Inconsistent (TC-TMP-04).
3. Test unlisted student with matching template -> Tier 2 Consistent (TC-TMP-05).
4. Test unlisted student with mismatched template -> Tier 3 Unverified (TC-TMP-05).
5. Test template registration endpoint and feature persistence (TC-TMP-06).

**Acceptance Criteria:**
- 100% test pass rate across all three verification tiers.

---

## 9. Implementation Order and Dependencies

```
CHIP TMP-01 (Feature Alignment & Homography)
    ↓
CHIP TMP-02 (SSIM Evaluator) ────────┐
    ↓                                │
CHIP TMP-03 (Seal & Logo Matcher)    │
    ↓                                │
CHIP TMP-04 (Database Record Match)  │
    ↓                                │
CHIP TMP-05 (Three-Tier Classifier) ◄┘
    ↓
CHIP TMP-06 (Template Registration) & CHIP TMP-07 (Record Bulk Import)
    ↓
CHIP TMP-08 (Verification Engine Service)
    ↓
CHIP TMP-09 (Database Models) & CHIP TMP-10 (Visual Diff)
    ↓
CHIP TMP-11 (Diagnostics)
    ↓
CHIP TMP-12 & CHIP TMP-13 (Unit Tests)
```

---

## 10. Phase Completion Checklist

- [x] Template feature alignment warps query certificate to master template with sub-pixel registration.
- [x] SSIM evaluator computes masked structural similarity, distinguishing genuine (>= 0.85) from fake (< 0.60).
- [x] University seal matcher validates emblem presence, geometry, and color profile.
- [x] Database record verifier queries official student records with fuzzy typo tolerance.
- [x] Three-tier classification strictly assigns Tier 1 (Verified), Tier 2 (Consistent), or Tier 3 (Unverified/Inconsistent).
- [x] Discrepancy details are explicitly reported when certificate text contradicts university records.
- [x] Template registration service enables onboarding new university master templates.
- [x] CSV bulk importer allows uploading institutional student records.
- [x] Side-by-side visual diff image generated highlighting structural differences.
- [x] Test cases TC-TMP-01 through TC-TMP-06 passing with 100% success rate.
