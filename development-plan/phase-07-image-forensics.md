# Phase 07 — Image Forensics

## 1. Purpose

Implement the classical digital image forensics subsystem to expose pixel-level and compression-level tampering on academic certificates. This module executes Error Level Analysis (ELA) to reveal JPEG re-compression artifacts, Copy-Move (clone) detection using SIFT/ORB keypoint clustering, and local noise variance analysis to identify spliced regions from foreign document sources. It produces an explainable composite forensic score [0.0, 1.0] and a spatial forensic anomaly heatmap.

## 2. Why This Phase Exists

Fraudulent certificates are frequently produced by digital image editing:
- Splicing an official university seal, gold medallion, or signature from one document onto another.
- Copying a genuine high-grade character (e.g. an "A+" or "9") and pasting it over a lower grade ("C" or "5") within the same certificate (Copy-Move forgery).
- Modifying text or background in Photoshop, which alters the local JPEG 8x8 block discrete cosine transform (DCT) quantization error rate relative to the untouched regions.
- Pasting a photo or graphic captured by a different camera/scanner, which introduces a distinct sensor noise pattern and grain variance.

These physical tampering operations alter image statistics even if the forgery appears visually seamless to the human eye. Image forensics detects these invisible mathematical artifacts without requiring any prior template or database match.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-FOR-01** | Error Level Analysis (ELA) to detect JPEG compression inconsistencies | Re-compression difference analysis with scale amplification and thresholding |
| **FR-FOR-02** | Copy-Move / clone detection using keypoint matching (SIFT / ORB) | SIFT/ORB feature extraction, FLANN matcher, DBSCAN spatial clustering |
| **FR-FOR-03** | Noise analysis / noise variance inconsistency detection across image regions | High-pass wavelet / Laplacian residual filtering and block variance map |
| **FR-FOR-04** | Generate forensic anomaly map and composite forensic score [0.0, 1.0] | Multi-channel heatmap synthesis, score fusion, and database persistence |
| **NFR-01** | High detection sensitivity on spliced and cloned regions | Calibrated thresholding to minimize false positives on clean scans |
| **NFR-03** | Performance (< 5 seconds execution time) | Multi-core OpenCV acceleration and downscaled feature matching |
| **TC-FOR-01** | ELA detection on modified/spliced region test | Chip FOR-12 |
| **TC-FOR-02** | Copy-move detection using keypoint matching test | Chip FOR-12 |
| **TC-FOR-03** | Noise variance inconsistency detection test | Chip FOR-13 |
| **TC-FOR-04** | Forensic composite score calculation test | Chip FOR-13 |
| **TC-FOR-05** | Forensic anomaly map generation test | Chip FOR-13 |

## 4. Inputs

- Untouched raw original image from Phase 03 (`storage/uploads/{uuid}.{ext}`). (Crucial: Forensics must operate on the pristine raw upload, NOT on the preprocessed/binarized image, because preprocessing erases compression and sensor noise signatures).
- Preprocessed image from Phase 04 (for spatial coordinate alignment).
- Configuration parameters (ELA quality levels [90, 95], ELA scale factor [10–20], SIFT match threshold, noise block size [32x32]).

## 5. Outputs

- `ForensicAnalysisResult` Pydantic model containing:
  - `overall_forensic_score`: float [0.0, 1.0] (1.0 = pristine/untampered, 0.0 = heavily manipulated)
  - `ela_score`: float [0.0, 1.0]
  - `copy_move_score`: float [0.0, 1.0]
  - `noise_inconsistency_score`: float [0.0, 1.0]
  - `detected_clones`: List[CloneMatch] (matched keypoint coordinate pairs, polygon regions)
  - `tampered_bounding_boxes`: List[BoundingBox] (suspicious localized regions)
- High-contrast visual forensic heatmap image (`storage/reports/{uuid}_forensics_heatmap.png`).
- Populated database records in `forensic_finding` table.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 03 (Document Ingestion).
- **Libraries:** `opencv-python-headless`, `numpy`, `scipy`, `scikit-image`, `Pillow`, `pydantic`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── forensics/
│   │       ├── __init__.py
│   │       ├── ela_analyzer.py        # Error Level Analysis (JPEG recompression)
│   │       ├── copy_move_detector.py  # SIFT / ORB keypoint matching and spatial clustering
│   │       ├── noise_analyzer.py      # Local noise variance and wavelet residual analysis
│   │       ├── heatmap_generator.py   # Multi-detector spatial heatmap fusion
│   │       ├── score_calculator.py    # Forensic score aggregation and penalty models
│   │       └── service.py             # Orchestrator: ForensicService
│   └── schemas/
│       └── forensics.py               # Pydantic schemas: ForensicResult, CloneRegion
└── tests/
    └── unit/
        ├── test_ela_analyzer.py
        ├── test_copy_move_detector.py
        ├── test_noise_analyzer.py
        ├── test_heatmap_generator.py
        └── test_forensic_service.py
```

---

## 8. Implementation Chips

---

### CHIP FOR-01 — Error Level Analysis (ELA) Core Engine

**Objective:** Implement Error Level Analysis by re-compressing the image at a known JPEG quality level (90% and 95%), subtracting the recompressed image from the original, and amplifying the pixel delta to expose compression discrepancies (FR-FOR-01).

**Why:** When an image is modified (e.g. a stamp pasted in Photoshop and saved), the modified area is compressed for the first time while the surrounding image is compressed for the second or third time. Regions with higher error levels stand out as bright white or colored halos against the darker, uniform background.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/forensics/ela_analyzer.py`

**Implementation:**
1. Implement `compute_ela(image_path: Path, quality: int = 90, scale: int = 15) -> Tuple[np.ndarray, float]`:
   - Load original image via `PIL.Image.open(image_path).convert("RGB")`.
   - Save temporary re-compressed copy in memory using `io.BytesIO` at specified `quality` (default 90).
   - Load re-compressed image back into PIL.
   - Calculate absolute pixel difference:
     ```python
     diff = ImageChops.difference(original, recompressed)
     ```
   - Find maximum extrema difference across channels: `extrema = diff.getextrema()`.
   - Compute dynamic scale factor: `max_diff = max([ex[1] for ex in extrema])`; `scale = 255.0 / max_diff if max_diff > 0 else 1.0`.
   - Amplify difference: `ela_image = ImageEnhance.Brightness(diff).enhance(scale)`.
   - Convert to NumPy array for numerical analysis.
2. Quantify ELA anomaly score:
   - Convert ELA image to grayscale.
   - Divide image into $32 \times 32$ pixel grid blocks.
   - Calculate mean error level per block: $\mu_b$.
   - Compute variance of block error levels: $\sigma^2_{\text{blocks}}$.
   - A high variance indicates that some localized regions have drastically different compression levels than the rest of the document.
   - Compute `ela_score = exp(-variance / 450.0)`, normalized to $[0.0, 1.0]$.
3. Locate suspicious regions:
   - Threshold the block map at $\mu_{\text{global}} + 2.8 \cdot \sigma_{\text{global}}$.
   - Return bounding boxes of high-error clusters as candidate spliced areas.

**Inputs:** Raw certificate image file path.

**Outputs:** Amplified ELA visualization image array (RGB), normalized ELA score float [0.0, 1.0], list of candidate tampered bounding boxes.

**Testing:** Test on synthetic certificate with a spliced signature box saved at different JPEG quality (TC-FOR-01).

**Acceptance Criteria:**
- Generates high-contrast ELA difference map.
- Spliced region exhibits distinct high-intensity error halo compared to background.

---

### CHIP FOR-02 — Multi-Quality ELA Differential Analysis

**Objective:** Run ELA across multiple JPEG quality levels (e.g. 75, 85, 90, 95) to construct an error-rate curve that detects the estimated original JPEG quality factor of the document.

**Why:** A single ELA pass at quality 90 can miss tampering if the original document was also saved at exactly 90%. Comparing the rate of change of error across multiple quality levels reveals the exact quantization inflection point.

**Dependencies:** CHIP FOR-01.

**Files to modify:**
- `backend/app/modules/forensics/ela_analyzer.py`

**Implementation:**
1. Implement `multi_quality_ela_curve(image_path: Path, qualities: List[int] = [75, 85, 90, 95]) -> dict`:
   - Compute mean absolute difference for each quality level.
   - Plot/interpolate the inflection point to estimate original compression quality.
   - If localized sub-regions have different inflection points (e.g. seal is quality 95, page is quality 80), flag as multi-source composite document.

**Acceptance Criteria:**
- Accurately estimates original document quality factor and flags multi-compression signatures.

---

### CHIP FOR-03 — SIFT Keypoint Extraction for Copy-Move Forgery

**Objective:** Extract Scale-Invariant Feature Transform (SIFT) keypoints and 128-dimensional descriptor vectors from the certificate image to detect duplicate or cloned visual elements (FR-FOR-02).

**Why:** Copy-move tampering involves duplicating genuine visual components (signatures, university stamps, serial numbers, high grades). SIFT features are invariant to scaling, rotation, and minor illumination changes.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/forensics/copy_move_detector.py`

**Implementation:**
1. Implement `extract_keypoints(gray_image: np.ndarray, max_features: int = 5000) -> Tuple[List[cv2.KeyPoint], np.ndarray]`:
   - Initialize SIFT detector:
     ```python
     sift = cv2.SIFT_create(nfeatures=max_features, contrastThreshold=0.03, edgeThreshold=10)
     keypoints, descriptors = sift.detectAndCompute(gray_image, None)
     ```
   - Fallback to ORB detector if SIFT is computationally constrained on low-resource environments.
   - Filter out keypoints located on standard repeating background patterns (e.g. fine micro-text border or hatched paper texture) using spatial density thresholds.

**Inputs:** Grayscale certificate image array.

**Outputs:** List of `cv2.KeyPoint` objects and `np.ndarray` of feature descriptors.

**Acceptance Criteria:**
- Extracts 1000–5000 robust keypoints across text, stamps, and signatures.

---

### CHIP FOR-04 — Fast Keypoint Matching and Geometric Filtering

**Objective:** Match feature descriptors against themselves using FLANN (Fast Library for Approximate Nearest Neighbors) with distance ratio testing and Euclidean distance pruning.

**Why:** In copy-move detection, we must match an image against itself to find distinct, non-identical regions that share identical visual descriptors.

**Dependencies:** CHIP FOR-03.

**Files to modify:**
- `backend/app/modules/forensics/copy_move_detector.py`

**Implementation:**
1. Implement `find_similar_descriptor_pairs(keypoints, descriptors, ratio_thresh: float = 0.65, min_distance: float = 50.0)`:
   - Build FLANN kd-tree index:
     ```python
     index_params = dict(algorithm=1, trees=5) # KDTREE
     search_params = dict(checks=50)
     flann = cv2.FlannBasedMatcher(index_params, search_params)
     matches = flann.knnMatch(descriptors, descriptors, k=3)
     ```
   - For each match:
     - Match 0 is self-match ($d=0$) -> discard.
     - Match 1 is the most similar other keypoint; Match 2 is the second most similar.
     - Apply Lowe's ratio test: `m1.distance < ratio_thresh * m2.distance`.
   - Apply Euclidean spatial distance threshold:
     - Reject pairs where $\|p_1 - p_2\| < \text{min\_distance}$ (prevents matching neighboring keypoints within the same word or character).
2. Return candidate paired keypoints `(pt1, pt2)` representing potential clone matches.

**Inputs:** Keypoints and descriptors.

**Outputs:** List of matched coordinate pairs `[(Point, Point)]`.

**Acceptance Criteria:**
- Filters out trivial self-matches and neighboring intra-character keypoints.

---

### CHIP FOR-05 — Spatial Clustering & RANSAC Affine Verification for Clones

**Objective:** Cluster matched keypoint pairs using DBSCAN and verify geometric transformation consistency via RANSAC to eliminate random false-positive matches (FR-FOR-02).

**Why:** Natural text contains identical letters (e.g. repeated letter "e" or "o") that produce similar SIFT descriptors. A true copy-move forgery involves an entire patch or region copied, meaning multiple nearby keypoints share the exact same spatial translation and rotation vector.

**Dependencies:** CHIP FOR-04.

**Files to modify:**
- `backend/app/modules/forensics/copy_move_detector.py`

**Implementation:**
1. Implement spatial clustering using DBSCAN:
   - Compute displacement vectors $\vec{v}_i = p_{2, i} - p_{1, i} = (\Delta x_i, \Delta y_i)$.
   - Cluster displacement vectors in $(\Delta x, \Delta y)$ space using `sklearn.cluster.DBSCAN(eps=15.0, min_samples=6)`.
   - Discard clusters with fewer than 6 supporting keypoint pairs.
2. RANSAC affine transformation test:
   - For each remaining cluster, fit an affine matrix:
     `M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=5.0)`.
   - If number of inliers $\ge 5$, confirm verified copy-move forgery region.
3. Compute bounding polygons around source region and destination cloned region.
4. Calculate `copy_move_score`:
   - If confirmed clone found: `copy_move_score = max(0.0, 1.0 - 0.25 * num_cloned_regions)`.
   - If no clones found: `copy_move_score = 1.0`.

**Inputs:** Candidate matched keypoint pairs.

**Outputs:** List of `CloneMatch` objects with source/target bounding boxes, inlier count, and `copy_move_score`.

**Testing:** Test on synthetic certificate where university seal or signature was cloned from bottom-left to bottom-right (TC-FOR-02).

**Acceptance Criteria:**
- Accurately detects cloned signatures and seals.
- Eliminates false positives from naturally repeated alphabet letters.

---

### CHIP FOR-06 — Local Noise Variance & Residual Inconsistency Analysis

**Objective:** Extract high-frequency sensor noise residuals using median/wavelet filtering and compute local noise variance across image tiles to identify spliced foreign elements (FR-FOR-03).

**Why:** Every camera sensor, flatbed scanner, and digital graphics editor has a unique noise signature (Photo-Response Non-Uniformity / PRNU and grain variance). Splicing an element from another document creates a localized noise discontinuity.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/forensics/noise_analyzer.py`

**Implementation:**
1. Extract noise residual map $R(x, y)$:
   - Convert image to grayscale float32.
   - Apply edge-preserving median filter to obtain smoothed estimate: $I_{\text{smooth}} = \text{cv2.medianBlur}(I, 3)$.
   - Subtract smooth image from original: $R(x, y) = I(x, y) - I_{\text{smooth}}(x, y)$.
2. Compute local noise variance map:
   - Divide $R(x, y)$ into $32 \times 32$ pixel non-overlapping blocks.
   - Calculate sample variance $\sigma_k^2$ for each block $k$.
   - Normalize the block variance map into $[0, 255]$ range.
3. Inconsistency detection:
   - Compute global median variance $\sigma_{\text{med}}^2$ and median absolute deviation (MAD).
   - Flag blocks whose noise variance deviates from global median:
     $|\sigma_k^2 - \sigma_{\text{med}}^2| > 3.0 \cdot \text{MAD}$.
   - Group contiguous flagged blocks using morphological dilation.
4. Compute `noise_inconsistency_score = exp(-anomalous_block_ratio * 8.0)`.

**Inputs:** Grayscale certificate image.

**Outputs:** Noise variance map array, `noise_inconsistency_score` [0.0, 1.0], list of noise anomaly bounding boxes.

**Testing:** Test on synthetic certificate containing a high-noise mobile phone photo patch spliced into a clean flatbed scan (TC-FOR-03).

**Acceptance Criteria:**
- Flags localized patches whose noise variance deviates significantly from the document average.

---

### CHIP FOR-07 — Forensic Anomaly Heatmap Generator

**Objective:** Synthesize Error Level Analysis, Copy-Move keypoint clusters, and Noise Variance maps into a single unified RGB forensic heatmap overlay (FR-FOR-04).

**Why:** Verification officers need an intuitive visual summary of tampering evidence. A single multi-channel heatmap highlights all suspicious regions in bright thermal colors (blue = untouched, red = high probability of tampering).

**Dependencies:** CHIP FOR-01, CHIP FOR-05, CHIP FOR-06.

**Files to create:**
- `backend/app/modules/forensics/heatmap_generator.py`

**Implementation:**
1. Implement `generate_composite_heatmap(raw_image: np.ndarray, ela_map: np.ndarray, clone_matches: List[CloneMatch], noise_map: np.ndarray, output_path: Path) -> Path`:
   - Normalize ELA map to $[0.0, 1.0]$.
   - Normalize noise anomaly map to $[0.0, 1.0]$.
   - Create clone binary mask: draw filled polygons over confirmed clone source and destination regions (value = 1.0).
   - Compute combined anomaly intensity:
     $$A(x, y) = 0.40 \cdot \text{ELA}(x, y) + 0.35 \cdot \text{Clone}(x, y) + 0.25 \cdot \text{Noise}(x, y)$$
   - Apply Gaussian blur ($\sigma = 5$) to create smooth thermal gradients.
   - Apply OpenCV colormap: `heatmap_color = cv2.applyColorMap(np.uint8(255 * A), cv2.COLORMAP_JET)`.
   - Blend heatmap with original certificate image:
     ```python
     blended = cv2.addWeighted(raw_image, 0.65, heatmap_color, 0.35, 0)
     ```
   - Draw bright cyan connection lines between confirmed cloned pairs.
   - Save annotated heatmap image to `storage/reports/{uuid}_forensics_heatmap.png`.

**Acceptance Criteria:**
- Generates high-resolution, color-coded thermal heatmap highlighting all tampered zones (TC-FOR-05).

---

### CHIP FOR-08 — Forensic Score Aggregator and Authenticity Categorization

**Objective:** Combine ELA, copy-move, and noise consistency scores into a calibrated `overall_forensic_score` [0.0, 1.0] with confidence ratings (FR-FOR-04).

**Why:** Feeds a single normalized feature into the multimodal ML classifier and provides clear verdict tiers for human reviewers.

**Dependencies:** CHIP FOR-01, CHIP FOR-05, CHIP FOR-06.

**Files to create:**
- `backend/app/modules/forensics/score_calculator.py`

**Implementation:**
1. Formula:
   $$\text{Score}_{\text{raw}} = 0.35 \cdot S_{\text{ELA}} + 0.40 \cdot S_{\text{CopyMove}} + 0.25 \cdot S_{\text{Noise}}$$
2. Veto rule:
   - If confirmed copy-move clone has $\ge 8$ RANSAC inliers, cap the `overall_forensic_score` at a maximum of `0.30` (definite forgery).
   - If severe ELA discrepancy is localized over text or seal areas, cap at `0.45`.
3. Categorization:
   - `0.85 - 1.00`: Authentic / Pristine (No pixel-level tampering detected)
   - `0.60 - 0.84`: Inconclusive / Minor Anomalies (Possible re-compression or scan artifact)
   - `0.00 - 0.59`: Manipulated / Tampered (Strong mathematical evidence of forgery)

**Acceptance Criteria:**
- Produces balanced score [0.0, 1.0] that accurately reflects tampering severity (TC-FOR-04).

---

### CHIP FOR-09 — Forensic Service Orchestrator

**Objective:** Encapsulate ELA, copy-move detection, noise analysis, heatmap generation, and database recording into the production `ForensicService`.

**Why:** Single entry point for pipeline execution, handles execution timeouts, and safely manages scratch memory.

**Dependencies:** CHIP FOR-01 through CHIP FOR-08.

**Files to create:**
- `backend/app/modules/forensics/service.py`

**Implementation:**
1. Implement `ForensicService`:
   ```python
   class ForensicService:
       def analyze(self, raw_image_path: Path, certificate_id: UUID) -> ForensicAnalysisResult:
           # 1. Run ELA analyzer
           # 2. Run Copy-Move SIFT detector
           # 3. Run Noise variance analyzer
           # 4. Synthesize composite heatmap overlay
           # 5. Calculate overall forensic score
           # 6. Return ForensicAnalysisResult
   ```
2. Timeout guard: Execution capped at 5.0 seconds (NFR-03). If keypoint count exceeds 8000, dynamically downscale keypoint budget.

**Acceptance Criteria:**
- Executes complete forensic suite within 5.0 seconds per certificate.

---

### CHIP FOR-10 — Database Entity & Migration for Forensic Findings

**Objective:** Map forensic results into the `forensic_finding` table defined in the Design Documents schema.

**Why:** Persists detected tampering bounding boxes, anomaly types, and scores for permanent record keeping and audit trails.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/models/forensic.py`
- Alembic migration script

**Implementation:**
1. Map `ForensicFindingModel(Base)` matching Design Docs:
   - `id: UUID` (Primary Key)
   - `certificate_id: UUID` (Foreign Key -> `certificate.id`, indexed)
   - `finding_type: String` (e.g. "ELA_ANOMALY", "COPY_MOVE_CLONE", "NOISE_INCONSISTENCY")
   - `confidence_score: Float`
   - `bounding_box_json: JSON`
   - `description: Text`
   - `heatmap_image_path: String`
   - `created_at: DateTime`

**Acceptance Criteria:**
- ORM model matches schema specification and persists findings.

---

### CHIP FOR-11 — Forensic Analysis CLI Tool

**Objective:** Create a command-line utility to run forensics on any image file and display/save the ELA, copy-move, and noise heatmaps.

**Why:** Enables rapid offline experimentation and tuning of thresholds by ML engineers without spinning up the backend server.

**Dependencies:** CHIP FOR-09.

**Files to create:**
- `backend/scripts/run_forensics.py`

**Acceptance Criteria:**
- Accepts `--image <path>` and generates standalone heatmap and JSON score report.

---

### CHIP FOR-12 — Unit Tests: ELA and Copy-Move Detection

**Objective:** Verify automated detection of JPEG ELA compression differences and copy-move duplicated regions on synthetic tampered fixtures (TC-FOR-01, TC-FOR-02).

**Dependencies:** CHIP FOR-01, CHIP FOR-05.

**Files to create:**
- `backend/tests/unit/test_ela_analyzer.py`
- `backend/tests/unit/test_copy_move_detector.py`

**Implementation:**
1. Test `test_detects_spliced_jpeg_box()`: Load image with spliced JPEG block (TC-FOR-01). Verify ELA score < 0.60 and tampered bounding box correctly identifies coordinates.
2. Test `test_pristine_image_high_ela_score()`: Pristine image produces ELA score >= 0.90.
3. Test `test_detects_cloned_signature_or_seal()`: Load image with cloned seal (TC-FOR-02). Verify copy-move detector finds >= 6 inlier pairs and flags clone regions.

**Acceptance Criteria:**
- Correctly detects spliced JPEG patches and cloned stamps/signatures.

---

### CHIP FOR-13 — Unit Tests: Noise Analysis, Composite Scoring & Heatmap

**Objective:** Test noise variance inconsistency detection, composite score calculation, and heatmap image generation (TC-FOR-03, TC-FOR-04, TC-FOR-05).

**Dependencies:** CHIP FOR-06, CHIP FOR-07, CHIP FOR-08.

**Files to create:**
- `backend/tests/unit/test_noise_analyzer.py`
- `backend/tests/unit/test_heatmap_generator.py`
- `backend/tests/unit/test_forensic_service.py`

**Implementation:**
1. Test `test_detects_noise_variance_inconsistency()`: Patch with artificial Gaussian noise produces noise anomaly (TC-FOR-03).
2. Test `test_forensic_composite_score_bounds()`: Verify score is bounded in [0.0, 1.0] (TC-FOR-04).
3. Test `test_heatmap_file_generation()`: Verify valid PNG heatmap file is generated with matching image dimensions (TC-FOR-05).

**Acceptance Criteria:**
- 100% test pass rate across forensic test cases.

---

## 9. Implementation Order and Dependencies

```
CHIP FOR-01 (ELA Core Engine)
    ↓
CHIP FOR-02 (Multi-Quality ELA Curve)
    ↓
CHIP FOR-03 (SIFT Keypoint Extraction)
    ↓
CHIP FOR-04 (Keypoint Matching & Ratio Test)
    ↓
CHIP FOR-05 (DBSCAN Clustering & RANSAC) ──┐
    ↓                                      │
CHIP FOR-06 (Local Noise Variance)         │
    ↓                                      │
CHIP FOR-07 (Composite Heatmap) ◄──────────┘
    ↓
CHIP FOR-08 (Score Aggregator)
    ↓
CHIP FOR-09 (Service Orchestrator)
    ↓
CHIP FOR-10 (Database Model) & CHIP FOR-11 (CLI Tool)
    ↓
CHIP FOR-12 & CHIP FOR-13 (Unit Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Error Level Analysis (ELA) isolates JPEG compression discrepancies at 90% and 95% quality.
- [ ] SIFT/ORB keypoint matcher detects duplicate visual elements.
- [ ] DBSCAN clustering and RANSAC affine verification eliminate repeated font letter false positives.
- [ ] Local noise variance residual analysis flags spliced patches with distinct sensor noise.
- [ ] Composite forensic thermal heatmap generated blending ELA, clones, and noise into RGB image.
- [ ] Overall forensic score [0.0, 1.0] computed with clear authenticity categorizations.
- [ ] Analysis executes directly on pristine raw upload, preserving untouched image statistics.
- [ ] Complete forensic analysis executes in under 5.0 seconds per certificate.
- [ ] Test cases TC-FOR-01 through TC-FOR-05 passing with 100% success rate.
