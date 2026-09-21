# Phase 04 — Image Preprocessing

## 1. Purpose

Implement the computer vision image preprocessing pipeline that conditions incoming certificate images for optimal optical character recognition (OCR), visual forensic analysis, and machine learning feature extraction. The pipeline performs noise reduction, illumination normalization, deskewing, perspective correction, adaptive binarization, and maintains an immutable audit trail of both raw and processed image states.

## 2. Why This Phase Exists

Real-world certificate scans and photographs suffer from diverse capture artifacts:
- Uneven lighting, shadows, and color casts from smartphone cameras.
- Angular skew and rotational misalignment from desktop flatbed scanners.
- Perspective distortion (trapezoidal warping) when photographed at non-perpendicular angles.
- High-frequency sensor noise, paper grain, and background watermarks that interfere with OCR.
- Low local contrast between text characters and textured certificate backgrounds.

Without rigorous preprocessing, downstream OCR error rates spike dramatically, and template alignment fails. Preprocessing transforms heterogeneous inputs into standardized, deskewed, contrast-normalized images while strictly preserving the untouched original image for forensic pixel analysis.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-PRE-01** | Grayscale conversion and noise reduction (Gaussian / median filtering) | OpenCV grayscale converter, selective Gaussian & median filters |
| **FR-PRE-02** | Binarization and adaptive thresholding (Otsu's / adaptive Gaussian) for OCR | Dual thresholding module tuned for text separation |
| **FR-PRE-03** | Skew detection and correction (Hough transform / minimum area rect, +/- 45°) | Projection profile and contour-based deskewer |
| **FR-PRE-04** | Perspective correction and boundary cropping (document corner detection, 4-point warp) | Document contour detection, convex hull, 4-point perspective transform |
| **FR-PRE-05** | Contrast enhancement (CLAHE — Contrast Limited Adaptive Histogram Equalization) | Tile-based CLAHE on luminance channel (LAB color space) |
| **FR-PRE-06** | Store both original and preprocessed images with audit tracking | Storage manager linking raw and preprocessed artifacts in database |
| **NFR-03** | Performance (< 5 seconds total preprocessing time) | Vectorized NumPy/OpenCV routines, memory-efficient pipeline |
| **NFR-08** | Modular pipeline architecture | Abstract pipeline step interface with independent stages |
| **TC-PRE-01** | Skew correction test (+/- 15° rotation) | Chip PRE-13 |
| **TC-PRE-02** | Perspective distortion correction test | Chip PRE-13 |
| **TC-PRE-03** | Low-contrast enhancement test | Chip PRE-13 |
| **TC-PRE-04** | Binarization clarity test | Chip PRE-14 |
| **TC-PRE-05** | Original and preprocessed image preservation test | Chip PRE-14 |

## 4. Inputs

- Validated working image path from Phase 03 (`storage/uploads/{uuid}.png`).
- Configuration parameters (CLAHE clip limit, tile grid size, deskew angle thresholds, target DPI/dimensions).

## 5. Outputs

- Deskewed, contrast-enhanced RGB image for visual inspection and template matching (`storage/preprocessed/{uuid}_enhanced.png`).
- High-contrast binarized grayscale image for OCR engine ingestion (`storage/preprocessed/{uuid}_binarized.png`).
- Transformation metadata (detected skew angle, perspective warp matrix, contrast metrics) stored in database and pipeline context.
- Unaltered raw image remains in `storage/uploads/` linked via foreign key.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 03 (Document Ingestion).
- **Libraries:** `opencv-python-headless` (cv2), `numpy`, `scikit-image`, `Pillow`, `pytest`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── preprocessing/
│   │       ├── __init__.py
│   │       ├── pipeline.py            # Orchestrator: PreprocessingPipeline
│   │       ├── base_step.py           # Abstract Base Class for pipeline steps
│   │       ├── color_conversion.py    # Grayscale, LAB, and color space transforms
│   │       ├── noise_reduction.py     # Bilateral, Gaussian, and median filtering
│   │       ├── contrast_enhancer.py   # CLAHE and illumination normalization
│   │       ├── deskewer.py            # Hough line & min-area rect skew detection and correction
│   │       ├── perspective_warper.py  # 4-point contour detection and homography warp
│   │       ├── binarizer.py           # Otsu's and adaptive thresholding for OCR
│   │       └── result.py              # PreprocessingResult dataclass/schema
│   └── schemas/
│       └── preprocessing.py           # Pydantic schemas for API and persistence
└── tests/
    └── unit/
        ├── test_deskewer.py
        ├── test_perspective_warper.py
        ├── test_contrast_enhancer.py
        ├── test_binarizer.py
        └── test_preprocessing_pipeline.py
```

---

## 8. Implementation Chips

---

### CHIP PRE-01 — Preprocessing Pipeline Architecture & Base Step Interface

**Objective:** Define the abstract base interface for preprocessing steps and create a modular, sequential pipeline executor that tracks timings, input/output shapes, and step-level failures.

**Why:** Enforces NFR-08 (modular architecture). Each transformation (contrast, deskew, perspective) must be independently testable, configurable, re-orderable, and toggleable without modifying surrounding code.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/preprocessing/base_step.py`
- `backend/app/modules/preprocessing/pipeline.py`
- `backend/app/modules/preprocessing/result.py`

**Implementation:**
1. Create `BasePreprocessingStep(ABC)`:
   ```python
   class BasePreprocessingStep(ABC):
       @property
       @abstractmethod
       def name(self) -> str:
           pass

       @abstractmethod
       def process(self, image: np.ndarray, context: dict) -> Tuple[np.ndarray, dict]:
           pass
   ```
2. Create `PreprocessingResult` dataclass:
   - `enhanced_image: np.ndarray` (RGB, deskewed, contrast-enhanced)
   - `binarized_image: np.ndarray` (Grayscale/binary, optimized for OCR)
   - `applied_skew_angle: float`
   - `perspective_corrected: bool`
   - `step_metrics: Dict[str, float]` (execution time per step in milliseconds)
   - `enhanced_image_path: Optional[Path]`
   - `binarized_image_path: Optional[Path]`
3. Implement `PreprocessingPipeline`:
   - Maintains registered list of `BasePreprocessingStep` instances.
   - Executes steps sequentially, catching step errors and recording execution duration per step.
   - Logs warnings if any step duration exceeds 1000ms.

**Inputs:** Raw image NumPy array (BGR/RGB).

**Outputs:** Completed `PreprocessingResult`.

**Testing:** Unit tests verifying step execution order, timing recording, and error propagation.

**Acceptance Criteria:**
- Steps can be added, removed, or bypassed dynamically via configuration.
- Total pipeline execution time and per-step metrics are recorded accurately.

---

### CHIP PRE-02 — Color Space Conversion & Grayscale Normalization

**Objective:** Implement standard color space conversion routines (RGB to Grayscale, RGB to LAB) with channel preservation for forensic and visual models.

**Why:** OCR and geometric algorithms operate on single-channel luminance arrays. Separating luminance (L) from chrominance (A, B) allows enhancing text readability without distorting security badge colors.

**Dependencies:** CHIP PRE-01.

**Files to create:**
- `backend/app/modules/preprocessing/color_conversion.py`

**Implementation:**
1. Implement `to_grayscale(image: np.ndarray) -> np.ndarray`:
   - If image has 4 channels (RGBA), convert to BGR using `cv2.COLOR_BGRA2BGR` before grayscale.
   - Convert using `cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)`.
2. Implement `to_lab(image: np.ndarray) -> np.ndarray`:
   - Convert to CIE LAB color space using `cv2.cvtColor(image, cv2.COLOR_BGR2LAB)`.
3. Implement `ensure_3channel(image: np.ndarray) -> np.ndarray`:
   - If input is 2D grayscale, convert to 3-channel BGR using `cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)`.

**Inputs:** 2D or 3D NumPy image array.

**Outputs:** Normalized grayscale or LAB image array.

**Edge Cases:**
- Input already grayscale (2D array) -> passes through without redundant conversions.
- Input has Alpha transparency channel -> properly composited over white background before grayscale conversion.

**Testing:** Unit test converting RGBA, RGB, and Grayscale inputs.

**Acceptance Criteria:**
- Correct channel transformations without shape mismatches or memory leaks.

---

### CHIP PRE-03 — Edge-Preserving Noise Reduction Filtering

**Objective:** Implement selective noise reduction using Bilateral Filtering and Median Filtering to eliminate high-frequency paper grain and scanner artifacts while preserving crisp text edges.

**Why:** Standard Gaussian blur blurs text edges, harming character recognition. Bilateral filtering smooths flat background texture while strictly preserving sharp text boundaries.

**Dependencies:** CHIP PRE-02.

**Files to create:**
- `backend/app/modules/preprocessing/noise_reduction.py`

**Implementation:**
1. Implement `BilateralNoiseFilter(BasePreprocessingStep)`:
   - Parameters: `d=9` (diameter of pixel neighborhood), `sigma_color=75`, `sigma_space=75`.
   - Call `cv2.bilateralFilter(gray_image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)`.
2. Implement fallback `MedianFilter`:
   - Useful for salt-and-pepper noise from photocopy scans.
   - Kernel size `ksize=3`.
3. Allow configuration via pipeline settings: `filter_type: Literal["bilateral", "median", "none"] = "bilateral"`.

**Inputs:** Single-channel grayscale image array.

**Outputs:** Denoised grayscale image array.

**Testing:** Measure edge sharpness metric (Laplacian variance) before and after filtering to verify edges are preserved.

**Acceptance Criteria:**
- Smooths background variation without reducing text edge contrast.

---

### CHIP PRE-04 — Contrast Limited Adaptive Histogram Equalization (CLAHE)

**Objective:** Normalize non-uniform lighting and enhance subtle text and watermark contrast using CLAHE applied to the luminance channel.

**Why:** Mobile phone photos of certificates frequently have strong vignetting, room shadows, or flash reflections. Global histogram equalization washes out details; CLAHE enhances contrast locally across grid tiles while clipping noise amplification.

**Dependencies:** CHIP PRE-02.

**Files to create:**
- `backend/app/modules/preprocessing/contrast_enhancer.py`

**Implementation:**
1. Implement `CLAHEEnhancer(BasePreprocessingStep)`:
   - Configurable parameters: `clip_limit=2.0`, `tile_grid_size=(8, 8)`.
2. For 3-channel color certificates:
   - Convert BGR to LAB color space.
   - Split into `L`, `A`, `B` channels.
   - Apply CLAHE to `L` channel:
     ```python
     clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
     enhanced_l = clahe.apply(l_channel)
     ```
   - Merge `enhanced_l`, `A`, and `B` channels back together.
   - Convert back to BGR.
3. For grayscale certificates:
   - Apply CLAHE directly to the grayscale array.
4. Calculate and log contrast improvement ratio (standard deviation of pixel intensity before vs. after).

**Inputs:** RGB/BGR or Grayscale image array.

**Outputs:** Contrast-enhanced image array with uniform illumination.

**Testing:**
- Test on deliberately shadowed synthetic certificate image (TC-PRE-03).
- Verify dark areas become readable while bright areas do not saturate to pure white.

**Acceptance Criteria:**
- Significantly improves character legibility in shadowy regions without introducing block artifacts.

---

### CHIP PRE-05 — Skew Detection and Rotational Correction

**Objective:** Detect document orientation tilt within [-45°, +45°] and rotate the image to perfect horizontal alignment.

**Why:** Certificates scanned or photographed at an angle degrade OCR accuracy by up to 40% and cause bounding box misalignments. Straightening the document is required for structured field extraction.

**Dependencies:** CHIP PRE-02, CHIP PRE-03.

**Files to create:**
- `backend/app/modules/preprocessing/deskewer.py`

**Implementation:**
1. Implement dual-method deskewing:
   - **Method A (Primary — Text Line Min-Area Rect):**
     1. Threshold image to isolate text pixels.
     2. Find coordinates of all non-zero pixels: `pts = np.column_stack(np.where(thresh > 0))`.
     3. Compute minimum bounding rectangle: `angle = cv2.minAreaRect(pts)[-1]`.
     4. Normalize angle to [-45°, 45°] range:
        - If `angle < -45`: `angle = -(90 + angle)`
        - Else: `angle = -angle`
   - **Method B (Secondary — Hough Transform for Underlines/Borders):**
     1. Run Canny edge detector: `edges = cv2.Canny(gray, 50, 150, apertureSize=3)`.
     2. Detect line segments via `cv2.HoughLinesP`.
     3. Compute median slope of near-horizontal lines (|angle| < 30°).
2. If estimated angle magnitude `|angle| > 0.3°`:
   - Compute rotation matrix around image center: `M = cv2.getRotationMatrix2D(center, angle, 1.0)`.
   - Calculate new bounding box dimensions to prevent corner clipping:
     ```python
     cos = np.abs(M[0, 0])
     sin = np.abs(M[0, 1])
     new_w = int((h * sin) + (w * cos))
     new_h = int((h * cos) + (w * sin))
     M[0, 2] += (new_w / 2) - center[0]
     M[1, 2] += (new_h / 2) - center[1]
     ```
   - Warp image: `cv2.warpAffine(image, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))`.
3. Record `detected_skew_angle` in pipeline context.

**Inputs:** Image array (RGB and Grayscale).

**Outputs:** Rotated, deskewed image array; applied angle float.

**Edge Cases:**
- Document already straight (|angle| < 0.2°) -> skip rotation to preserve pixel sharpness.
- Image rotated 90°, 180°, or 270° -> detect primary text orientation via OCR OSD (Orientation and Script Detection) in Phase 05 if needed.

**Testing:**
- Test synthetic certificate rotated by +5°, +15°, -10°, -25° (TC-PRE-01).
- Verify residual angle after correction is < 0.5°.

**Acceptance Criteria:**
- Corrects tilt within +/- 45° range with residual error < 0.5°.
- White background padding prevents black border artifacts.

---

### CHIP PRE-06 — Document Boundary Detection and Perspective Correction

**Objective:** Detect the 4 corners of a certificate document within a photographic background and apply a 4-point homography transform to crop and un-warp the document into a clean rectangular plane.

**Why:** Photos taken on desks or tables contain distracting background surfaces (wood grain, papers) and severe trapezoidal perspective distortion. Rectifying the document to flat orthogonal coordinates isolates the certificate area.

**Dependencies:** CHIP PRE-02, CHIP PRE-03.

**Files to create:**
- `backend/app/modules/preprocessing/perspective_warper.py`

**Implementation:**
1. Implement `DocumentBoundaryDetector`:
   - Downscale image to width=800 for fast contour detection while preserving aspect ratio.
   - Apply Gaussian blur (`ksize=(5, 5)`) and Canny edge detection (`low=75, high=200`).
   - Find external contours using `cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)`.
   - Sort contours by area in descending order.
   - Iterate top contours and approximate polygon curves:
     ```python
     peri = cv2.arcLength(c, True)
     approx = cv2.approxPolyDP(c, 0.02 * peri, True)
     if len(approx) == 4 and cv2.isContourConvex(approx):
         # Found 4-corner document boundary
     ```
   - If document area < 30% of total image area, fallback to full image (avoids cropping inner text boxes).
2. Implement `order_points(pts: np.ndarray) -> np.ndarray`:
   - Order points: top-left, top-right, bottom-right, bottom-left based on sum `(x+y)` and difference `(y-x)`.
3. Implement `four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray`:
   - Compute maximum width and height from Euclidean distances between corner pairs.
   - Define destination coordinates: `[[0, 0], [max_w - 1, 0], [max_w - 1, max_h - 1], [0, max_h - 1]]`.
   - Compute perspective transform matrix: `M = cv2.getPerspectiveTransform(pts, dst)`.
   - Apply warp: `cv2.warpPerspective(image, M, (max_w, max_h), flags=cv2.INTER_CUBIC)`.

**Inputs:** Raw photographed image array.

**Outputs:** Rectified, cropped certificate image array; boolean `perspective_applied`.

**Edge Cases:**
- Flatbed scan (document already fills entire frame, corners touching edge) -> detector recognizes full frame, perspective transform skipped gracefully.
- Low-contrast background (white certificate on white table) -> contour approximation fails; fallback to unwarped image without exception.

**Testing:**
- Test perspective-warped test images taken at 30° angle (TC-PRE-02).
- Verify cropped output aspect ratio matches standard A4 (1.414 +/- 0.08).

**Acceptance Criteria:**
- Accurately detects and rectifies 4-corner document boundaries when contrast between certificate and background is >= 20%.
- Gracefully falls back to original frame if no 4-corner polygon is detected.

---

### CHIP PRE-07 — Adaptive Binarization for OCR Enhancement

**Objective:** Generate a clean, high-contrast two-tone (black text on pure white background) image using adaptive thresholding, specifically tuned for downstream OCR ingestion.

**Why:** OCR engines achieve their highest character recognition accuracy on crisp binarized images where paper texture, watermarks, colored borders, and faint stains are suppressed.

**Dependencies:** CHIP PRE-02, CHIP PRE-04.

**Files to create:**
- `backend/app/modules/preprocessing/binarizer.py`

**Implementation:**
1. Implement `AdaptiveBinarizer(BasePreprocessingStep)`:
   - Provide two selectable thresholding algorithms:
     - **Algorithm 1 (Otsu's Thresholding):**
       - Optimal for scans with uniform background illumination.
       - `cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)`.
     - **Algorithm 2 (Adaptive Gaussian Thresholding — Default):**
       - Optimal for photos with localized lighting gradients.
       - `cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=21, C=11)`.
2. Apply light morphological opening (`kernel=np.ones((2,2), np.uint8)`) if background salt noise is detected to clean isolated pixel specks without eroding thin font strokes.
3. Invert polarity check:
   - Ensure text is black (0) and background is white (255). If mean pixel value < 127, invert binary image: `cv2.bitwise_not(binary)`.

**Inputs:** Denoised, contrast-enhanced grayscale image.

**Outputs:** Single-channel uint8 binary image array (0 and 255).

**Testing:**
- Test binarization on high-contrast scan vs degraded photocopy (TC-PRE-04).
- Confirm character stroke connectivity is maintained (no broken characters).

**Acceptance Criteria:**
- Produces clean binary image with black text on pure white background.
- Background noise removed while delicate characters remain intact.

---

### CHIP PRE-08 — Resolution Normalization and Aspect Ratio Guard

**Objective:** Standardize preprocessed image dimensions to a consistent resolution range (between 1600x1200 and 3500x2500 pixels) while strictly maintaining the original aspect ratio.

**Why:** Extremely large images (e.g. 80MP camera scans) cause out-of-memory errors in OCR and CNN models. Standardizing dimensions ensures predictable memory and execution profiles across all subsequent phases.

**Dependencies:** CHIP PRE-01.

**Files to create:**
- `backend/app/modules/preprocessing/resizer.py`

**Implementation:**
1. Define bounding bounds: `MAX_LONG_EDGE = 3200`, `MIN_LONG_EDGE = 1200`.
2. If `max(w, h) > MAX_LONG_EDGE`:
   - Compute scale factor: `scale = MAX_LONG_EDGE / max(w, h)`.
   - Resize using area interpolation: `cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)`.
3. If `max(w, h) < MIN_LONG_EDGE`:
   - Scale up using cubic interpolation: `cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)`.
4. Record scaling factor in metadata for mapping bounding box coordinates back to original image space.

**Acceptance Criteria:**
- Output dimensions strictly fall within target bounds.
- Aspect ratio is preserved with 0% distortion.

---

### CHIP PRE-09 — Preprocessing Artifact Storage and Audit Tracking

**Objective:** Save preprocessed image artifacts to the filesystem and maintain complete database tracking linking raw uploads to enhanced and binarized images (FR-PRE-06).

**Why:** Guarantees regulatory and legal compliance for verification audits. An investigator must always be able to inspect both the pristine original file and the exact transformed image fed to the ML and OCR models.

**Dependencies:** CHIP PRE-01, Phase 03 Storage Manager.

**Files to create:**
- `backend/app/modules/preprocessing/artifact_manager.py`

**Implementation:**
1. Implement `save_preprocessing_artifacts(certificate_id: UUID, result: PreprocessingResult) -> Tuple[Path, Path]`:
   - Target directories:
     - `storage/preprocessed/{certificate_id}_enhanced.png`
     - `storage/preprocessed/{certificate_id}_binarized.png`
   - Write images to disk using optimized PNG compression (`cv2.IMWRITE_PNG_COMPRESSION, 4`).
2. Update database record for certificate:
   - Set `certificate.preprocessed_image_path = str(enhanced_path)`.
   - Record transformation metrics (`skew_angle`, `perspective_applied`, `processing_time_ms`) in metadata column.

**Acceptance Criteria:**
- Both enhanced color image and binarized image are saved and indexed to the certificate ID.
- Original raw upload file remains completely untouched.

---

### CHIP PRE-10 — Complete Preprocessing Service Orchestrator

**Objective:** Wire all individual preprocessing steps into the production `PreprocessingService` called by the verification pipeline.

**Why:** Encapsulates the execution workflow, error recovery, file I/O, and metrics reporting into a clean, reusable service class.

**Dependencies:** CHIP PRE-01 through CHIP PRE-09.

**Files to create:**
- `backend/app/modules/preprocessing/service.py`

**Implementation:**
1. Implement `PreprocessingService`:
   ```python
   class PreprocessingService:
       def __init__(self, artifact_manager: ArtifactManager, config: PreprocessingConfig):
           self.artifact_manager = artifact_manager
           self.pipeline = self._build_pipeline(config)

       def preprocess(self, certificate_id: UUID, input_image_path: Path) -> PreprocessingResult:
           # 1. Load image from disk via cv2.imread
           # 2. Execute pipeline steps:
           #    - Perspective correction (if needed)
           #    - Grayscale & noise reduction
           #    - Skew detection & rotation
           #    - CLAHE contrast enhancement
           #    - Adaptive binarization
           #    - Resolution normalization
           # 3. Persist enhanced & binarized images to storage
           # 4. Return PreprocessingResult
   ```
2. Wrap with execution timeout (max 5.0 seconds).
3. If perspective correction or deskew throws an unexpected error, log warning and continue with unskewed image rather than crashing the verification.

**Acceptance Criteria:**
- Successfully transforms arbitrary input certificate into clean enhanced and binarized outputs in < 3.5s.

---

### CHIP PRE-11 — Preprocessing CLI Pipeline Tool

**Objective:** Build a command-line script to test and inspect preprocessing on single images or bulk directories with before/after visual comparison outputs.

**Why:** Allows ML engineers and developers to rapidly visually inspect preprocessing quality on hundreds of certificate samples without running the web server.

**Dependencies:** CHIP PRE-10.

**Files to create:**
- `backend/scripts/run_preprocessing.py`

**Implementation:**
1. Support arguments:
   - `--input`: Path to image or directory of images.
   - `--output-dir`: Destination folder for processed images.
   - `--save-comparison`: If True, generates a side-by-side comparison image `[Original | Enhanced | Binarized]`.
   - `--show-timings`: Print per-step execution timings.
2. Output summary report: Average execution time, average skew angle corrected, number of successful perspective warps.

**Acceptance Criteria:**
- Successfully processes directories of test certificates and generates side-by-side verification images.

---

### CHIP PRE-12 — Preprocessing Pipeline Diagnostics & Health

**Objective:** Add self-test diagnostic routines to verify OpenCV acceleration (SIMD / multithreading) and validate that image buffers process without memory leaks.

**Dependencies:** CHIP PRE-01.

**Files to create:**
- `backend/app/modules/preprocessing/diagnostics.py`

**Implementation:**
1. Implement `run_preprocessing_diagnostics() -> dict`:
   - Check `cv2.useOptimized()` and `cv2.getNumThreads()`.
   - Run benchmark on 2000x3000 test canvas to ensure complete pipeline executes in < 2500ms.
   - Return status dictionary.

**Acceptance Criteria:**
- Verifies OpenCV optimization is active and confirms processing meets performance thresholds.

---

### CHIP PRE-13 — Unit Tests: Skew, Perspective, and Contrast

**Objective:** Implement automated unit tests for deskewing, perspective correction, and contrast enhancement using synthetic ground-truth test images.

**Dependencies:** CHIP PRE-04, CHIP PRE-05, CHIP PRE-06.

**Files to create:**
- `backend/tests/unit/test_deskewer.py`
- `backend/tests/unit/test_perspective_warper.py`
- `backend/tests/unit/test_contrast_enhancer.py`

**Implementation:**
1. Test `test_deskew_positive_15_degrees()`: Apply 15° rotation to synthetic certificate, verify corrected angle is 15.0° +/- 0.5° (TC-PRE-01).
2. Test `test_deskew_negative_10_degrees()`: Apply -10° rotation, verify correction.
3. Test `test_perspective_warp_rectification()`: Apply homography transform to test image, verify 4-point warper recovers rectangular aspect ratio (TC-PRE-02).
4. Test `test_clahe_contrast_enhancement()`: Verify standard deviation of pixel values increases in low-contrast test image (TC-PRE-03).

**Acceptance Criteria:**
- All tests pass with quantitative tolerances.

---

### CHIP PRE-14 — Unit Tests: Binarization and Audit Preservation

**Objective:** Implement automated tests for adaptive binarization quality and verify the untouched preservation of original raw images.

**Dependencies:** CHIP PRE-07, CHIP PRE-09, CHIP PRE-10.

**Files to create:**
- `backend/tests/unit/test_binarizer.py`
- `backend/tests/unit/test_preprocessing_pipeline.py`

**Implementation:**
1. Test `test_adaptive_binarization_polarity()`: Confirm black text on white background (TC-PRE-04).
2. Test `test_original_file_immutability()`: Compute SHA-256 of raw file before and after preprocessing; verify hashes are strictly identical (TC-PRE-05).
3. Test `test_end_to_end_preprocessing_under_5s()`: Benchmark full pipeline on 3000x2000 image; verify elapsed time < 5.0 seconds (NFR-03).

**Acceptance Criteria:**
- Verifies image binarization, raw file immutability, and execution time < 5.0s.

---

## 9. Implementation Order and Dependencies

```
CHIP PRE-01 (Base Step & Pipeline Architecture)
    ↓
CHIP PRE-02 (Color Space & Grayscale)
    ↓
CHIP PRE-03 (Noise Reduction) ──────┐
    ↓                               │
CHIP PRE-04 (CLAHE Contrast)        │
    ↓                               │
CHIP PRE-05 (Deskewing)             │
    ↓                               │
CHIP PRE-06 (Perspective Warp) ◄────┘
    ↓
CHIP PRE-07 (Adaptive Binarization)
    ↓
CHIP PRE-08 (Resolution Normalization)
    ↓
CHIP PRE-09 (Artifact Storage & Audit)
    ↓
CHIP PRE-10 (Service Orchestrator)
    ↓
CHIP PRE-11 (CLI Tool) & CHIP PRE-12 (Diagnostics)
    ↓
CHIP PRE-13 & CHIP PRE-14 (Unit & Integration Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Pipeline step interface allows modular addition and re-ordering of transformation stages.
- [ ] Color conversions properly handle RGBA, RGB, Grayscale, and LAB color spaces.
- [ ] Bilateral filter smooths paper background while preserving sharp character edges.
- [ ] CLAHE normalizes illumination across unevenly shadowed certificate photos.
- [ ] Skew detection corrects rotation within [-45°, +45°] with residual tilt < 0.5°.
- [ ] Perspective warper rectifies photographed certificates to orthogonal rectangles.
- [ ] Adaptive binarizer outputs high-contrast binary images optimized for OCR.
- [ ] Resolution is normalized within [1200, 3200] px bounding box without distorting aspect ratio.
- [ ] Both raw upload and preprocessed artifacts are stored with full database audit tracking.
- [ ] Total preprocessing pipeline executes in under 5.0 seconds per certificate.
- [ ] Test cases TC-PRE-01 through TC-PRE-05 pass with 100% success rate.
