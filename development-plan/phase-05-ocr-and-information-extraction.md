# Phase 05 — OCR & Information Extraction

## 1. Purpose

Implement the optical character recognition (OCR) and structured information extraction engine. This subsystem uses PaddleOCR as the primary offline OCR engine to detect text regions, recognize character sequences, extract precise polygon bounding boxes, compute per-field confidence scores, and parse key academic certificate entities (Student Name, Roll Number, Degree Program, Institution Name, Issue Date, Grade/CGPA, Certificate Serial Number) using specialized regex, spatial heuristics, and Named Entity Recognition (NER).

## 2. Why This Phase Exists

Academic certificate verification requires semantic understanding of the document's textual content. Without accurate OCR:
- Cross-database student record verification is impossible because the system cannot read the roll number or student name.
- Text consistency checks (date chronology, grade calculations, font consistency) cannot execute without recognized text and character bounding boxes.
- Forgery often occurs at the text level (altering a grade "B" to "A", modifying a name or registration number, changing graduation years).
- The multimodal ML classifier needs textual embeddings and confidence scores to evaluate authenticity.

PaddleOCR was chosen in the Master Development Plan as the single primary OCR engine because it is lightweight, fully local (no external API costs or data privacy concerns), supports multi-lingual and angle detection out of the box, and provides character-level and word-level bounding boxes and confidence scores.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-OCR-01** | Extract text from preprocessed images using PaddleOCR (detection, recognition, bounding boxes, confidence) | PaddleOCR wrapper service with angle classification |
| **FR-OCR-02** | Structured field extraction: Student Name, Roll/Reg Number, Degree/Program, Institution, Issue Date, Grade/CGPA, Certificate ID | Rule-based regex parsers, spatial geometry heuristics, fuzzy field matchers |
| **FR-OCR-03** | Provide confidence score for each extracted text field | Weighted mean of word/character confidence scores per field |
| **FR-OCR-04** | Flag fields with confidence score below threshold (< 0.70) for manual review | Low-confidence detection and flagging logic |
| **NFR-01** | OCR Accuracy (Word accuracy >= 95% on high-res, >= 85% on degraded scans) | Preprocessed binarized input pipeline with fallback recognition |
| **NFR-03** | Performance (< 10s OCR execution) | PaddleOCR CPU multi-threading, image resolution scaling |
| **TC-OCR-01** | Clean certificate OCR extraction (word accuracy >= 95%) | Chip OCR-13 |
| **TC-OCR-02** | Degraded certificate OCR extraction (word accuracy >= 85%) | Chip OCR-13 |
| **TC-OCR-03** | Field extraction accuracy (Name, Roll No, Degree, Date, Institution) | Chip OCR-14 |
| **TC-OCR-04** | Confidence score calculation and < 0.70 flagging | Chip OCR-14 |
| **TC-OCR-05** | Bounding box accuracy and coordinate mapping | Chip OCR-14 |

## 4. Inputs

- Preprocessed image files from Phase 04 (`storage/preprocessed/{uuid}_enhanced.png` and `storage/preprocessed/{uuid}_binarized.png`).
- Configuration parameters (OCR language, confidence threshold `0.70`, use_angle_cls `True`).

## 5. Outputs

- Raw OCR token list containing detected text strings, 4-point polygon bounding boxes, and confidence scores `[0.0, 1.0]`.
- Structured `ExtractedCertificateFields` Pydantic model with parsed academic fields and per-field confidence scores.
- List of flagged low-confidence fields (`confidence < 0.70`).
- OCR visualization overlay image with highlighted text bounding boxes.
- Database records populated in `ocr_field` table.

## 6. Dependencies

- **Previous phases:** Phase 01 (Foundation), Phase 03 (Ingestion), Phase 04 (Preprocessing).
- **Libraries:** `paddlepaddle` / `paddleocr`, `numpy`, `opencv-python-headless`, `pydantic`, `rapidfuzz` (fuzzy matching), `python-dateutil`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── ocr/
│   │       ├── __init__.py
│   │       ├── engine.py              # PaddleOCR wrapper and initialization
│   │       ├── token_builder.py       # Raw OCR token and bounding box data structures
│   │       ├── spatial_analyzer.py    # Spatial layout analysis (reading order, lines, blocks)
│   │       ├── field_extractors/
│   │       │   ├── __init__.py
│   │       │   ├── base_extractor.py  # Abstract field extractor interface
│   │       │   ├── name_extractor.py  # Student name extraction heuristics
│   │       │   ├── roll_no_extractor.py # Roll / Registration / USN number extractor
│   │       │   ├── degree_extractor.py # Degree, program, branch extractor
│   │       │   ├── institution_extractor.py # University / College name extractor
│   │       │   ├── date_extractor.py  # Issue date, convocation date extractor
│   │       │   ├── grade_extractor.py # CGPA, percentage, division extractor
│   │       │   └── cert_id_extractor.py # Certificate serial / QR text extractor
│   │       ├── confidence_evaluator.py # Field-level confidence aggregator and flagging
│   │       ├── visualizer.py          # Bounding box rendering on certificate image
│   │       └── service.py             # Orchestrator: OCRService
│   └── schemas/
│       └── ocr.py                     # Pydantic schemas: OCRField, ExtractedFieldsResponse
└── tests/
    └── unit/
        ├── test_ocr_engine.py
        ├── test_field_extractors.py
        ├── test_confidence_evaluator.py
        └── test_ocr_service.py
```

---

## 8. Implementation Chips

---

### CHIP OCR-01 — PaddleOCR Engine Initialization and Lifecycle Management

**Objective:** Implement a thread-safe singleton wrapper around PaddleOCR that initializes the detection (DBNet), recognition (SVTR/CRNN), and direction classifier models once at application startup.

**Why:** Initializing OCR models on every request takes 3–5 seconds and causes severe memory churn. A singleton pattern keeps model weights resident in memory, cutting per-request OCR latency to 1–2 seconds.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/ocr/engine.py`

**Implementation:**
1. Implement `PaddleOCREngine` singleton:
   ```python
   class PaddleOCREngine:
       _instance = None

       def __new__(cls, *args, **kwargs):
           if cls._instance is None:
               cls._instance = super().__new__(cls)
               cls._instance._initialized = False
           return cls._instance

       def initialize(self, use_gpu: bool = False, lang: str = "en"):
           if self._initialized:
               return
           from paddleocr import PaddleOCR

           self.ocr = PaddleOCR(
               use_angle_cls=True,
               lang=lang,
               use_gpu=use_gpu,
               show_log=False,
               enable_mkldnn=True,  # CPU acceleration
               ocr_version="PP-OCRv4",  # Latest lightweight version
           )
           self._initialized = True
   ```
2. Implement warm-up routine: Run OCR on a 100x50 blank canvas during startup to pre-allocate inference tensors.
3. Expose thread-safe `predict(image_path_or_array)` method returning raw PaddleOCR results format:
   `[[[ [x1, y1], [x2, y2], [x3, y3], [x4, y4] ], (text, confidence)]]`.

**Inputs:** Image file path or NumPy array.

**Outputs:** Raw PaddleOCR detection and recognition results.

**Error Handling:** Catch PaddleOCR inference errors, log diagnostic details, and raise `OCRExecutionError`.

**Testing:** Unit test verifying singleton behavior (calling initialize twice returns same instance) and warm-up execution.

**Acceptance Criteria:**
- PaddleOCR loads PP-OCRv4 models with CPU MKL-DNN acceleration.
- Singleton pattern prevents redundant weight re-loading.

---

### CHIP OCR-02 — OCR Token & Bounding Box Geometric Data Structures

**Objective:** Define clean, typed dataclasses for OCR tokens, bounding boxes, text lines, and spatial coordinates.

**Why:** Raw PaddleOCR output is a nested list of coordinates and tuples. Converting them into immutable, typed objects enables geometric operations (distance, alignment, containment, intersection).

**Dependencies:** CHIP OCR-01.

**Files to create:**
- `backend/app/modules/ocr/token_builder.py`

**Implementation:**
1. Define `Point(NamedTuple)`: `x: float`, `y: float`.
2. Define `BoundingBox`:
   - `polygon: List[Point]` (4 points: top-left, top-right, bottom-right, bottom-left)
   - `x_min: float`, `y_min: float`, `x_max: float`, `y_max: float`
   - `width: float`, `height: float`
   - `center: Point`
   - Methods: `contains(point)`, `intersects(other)`, `horizontal_distance(other)`, `vertical_distance(other)`.
3. Define `OCRToken`:
   - `text: str`
   - `cleaned_text: str` (stripped of non-alphanumeric noise)
   - `bbox: BoundingBox`
   - `confidence: float` (0.0 to 1.0)
   - `line_number: Optional[int] = None`
4. Implement `TokenBuilder.from_paddle_output(raw_output) -> List[OCRToken]`:
   - Filter out empty or whitespace-only tokens.
   - Clamp bounding box coordinates to image dimensions.

**Inputs:** Raw PaddleOCR output list.

**Outputs:** List of validated `OCRToken` instances.

**Acceptance Criteria:**
- Correctly parses polygon points, computes bounding box bounds, and filters noise.

---

### CHIP OCR-03 — Spatial Reading-Order & Line Segmentation

**Objective:** Group detected OCR tokens into horizontal text lines and sort them into top-to-bottom, left-to-right reading order based on geometric proximity.

**Why:** OCR engines return tokens in arbitrary detection order. Reconstructing lines and paragraphs is required for regex matching (e.g. finding "Roll No:" and reading the token directly to its right).

**Dependencies:** CHIP OCR-02.

**Files to create:**
- `backend/app/modules/ocr/spatial_analyzer.py`

**Implementation:**
1. Implement `group_tokens_into_lines(tokens: List[OCRToken], y_threshold_ratio: float = 0.5) -> List[TextLine]`:
   - Sort tokens primarily by vertical center (`center.y`).
   - Group tokens whose vertical overlap exceeds 50% of the line height.
   - Sort tokens within each line by horizontal position (`center.x`) from left to right.
2. Define `TextLine`:
   - `tokens: List[OCRToken]`
   - `text: str` (tokens joined by single space)
   - `bbox: BoundingBox` (union of all token bounding boxes)
   - `mean_confidence: float`
   - `y_center: float`
3. Implement spatial query helpers:
   - `find_token_to_right(anchor_token, max_x_dist, max_y_drift) -> Optional[OCRToken]`
   - `find_line_below(anchor_line, max_y_dist) -> Optional[TextLine]`

**Inputs:** List of `OCRToken` objects.

**Outputs:** Sorted list of `TextLine` objects representing structured reading order.

**Testing:** Test on synthetic certificate text layout with 3 columns and multiple header lines.

**Acceptance Criteria:**
- Reconstructs continuous lines accurately.
- Associates key-value pairs (e.g. "Name:" followed by "JOHN DOE") into coherent line structures.

---

### CHIP OCR-04 — Base Extractor Interface & Parsing Utilities

**Objective:** Create the abstract base class and shared string matching utilities for all field extractors, including fuzzy label matching and text sanitization.

**Why:** Certificate formats vary widely across universities. Different certificates use labels like "Candidate Name", "Name of Student", "Student:", "This is to certify that [Name]". Shared fuzzy matching handles OCR typos in labels.

**Dependencies:** CHIP OCR-03.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/base_extractor.py`

**Implementation:**
1. Define `BaseFieldExtractor(ABC)`:
   ```python
   class BaseFieldExtractor(ABC):
       @property
       @abstractmethod
       def field_name(self) -> str:
           pass

       @abstractmethod
       def extract(
           self, lines: List[TextLine], all_tokens: List[OCRToken]
       ) -> Optional[ExtractedField]:
           pass
   ```
2. Define `ExtractedField`:
   - `field_name: str`
   - `value: str`
   - `raw_text: str`
   - `confidence: float`
   - `bounding_box: BoundingBox`
   - `source_tokens: List[OCRToken]`
   - `is_flagged: bool` (True if confidence < 0.70)
3. Implement `find_label_match(line: TextLine, target_labels: List[str], threshold: int = 80) -> Optional[Tuple[str, int]]`:
   - Use `rapidfuzz.fuzz.partial_ratio` to detect labels even if OCR had minor typos (e.g. "Regislration No" -> "Registration No").

**Acceptance Criteria:**
- Provides standard interface and robust fuzzy matching for all specific field extractors.

---

### CHIP OCR-05 — Student Name Field Extractor

**Objective:** Extract the student's full name from certificate text lines using anchor keywords, grammar patterns, and name capitalization heuristics.

**Why:** Student name is a primary verification entity. It typically follows phrases like "certify that", "admitted to the degree of", or is displayed in prominent uppercase font.

**Dependencies:** CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/name_extractor.py`

**Implementation:**
1. Define common name anchor patterns:
   - Prefix anchors: `r"(?:this is to certify that|certify that|presented to|conferred upon|awarded to)\s+([A-Z\s\.\,\'\-]+?)(?:\s+(?:having|son of|daughter of|bearing|who has|of the))"`
   - Label anchors: `r"(?:student name|name of candidate|candidate name|name)\s*[:\-]?\s*([A-Z\s\.\'\-]+)"`
2. Implement extraction strategies:
   - **Strategy 1 (Regex on joined lines):** Search full-text corpus using prefix anchors.
   - **Strategy 2 (Key-Value Line Search):** Find lines containing label anchors and extract the trailing text or the line immediately below.
   - **Strategy 3 (Dominant Typography):** If anchor fails, locate standalone uppercase lines with 2–4 words not matching university names or degree titles.
3. Clean extracted name:
   - Strip prefixes (Mr., Ms., Mrs., Sri).
   - Strip punctuation noise, normalize internal whitespace.
   - Verify length: 2 to 60 characters; reject if contains digits.
4. Calculate confidence: Average confidence of all constituent name tokens.

**Testing:** Test with 10 variations of certificate name presentations (single line, labeled, uppercase, mixed case).

**Acceptance Criteria:**
- Accurately extracts student name from test certificates with word accuracy >= 95%.

---

### CHIP OCR-06 — Roll / Registration / USN Number Extractor

**Objective:** Extract alphanumeric identification numbers (Roll Number, Registration Number, Enrollment Number, USN) using strict regex patterns and fuzzy label searches.

**Why:** The registration/roll number is the primary key used to verify student authenticity against institutional records.

**Dependencies:** CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/roll_no_extractor.py`

**Implementation:**
1. Define label triggers: `["roll no", "roll number", "reg no", "registration no", "enrollment no", "usn", "prn", "hall ticket no", "student id"]`.
2. Define identification regex patterns:
   - Indian USN: `r"\b[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}\b"` (e.g. `1MS20CS001`)
   - Standard alphanumeric enrollment: `r"\b[A-Z0-9]{6,16}\b"`
   - Pure numeric roll: `r"\b\d{6,12}\b"`
3. Implement extraction logic:
   - Search lines for label triggers.
   - If trigger found, inspect right-hand tokens on the same line.
   - If right-hand is empty, inspect the line immediately below.
   - Match against ID regex patterns.
4. Validate format: Ensure ID contains no illegal punctuation; strip OCR confusions (e.g. `O` vs `0` based on pattern structure).

**Testing:** Test USN, Roll No, and Enrollment formats.

**Acceptance Criteria:**
- Extracts alphanumeric IDs accurately and computes token-level confidence.

---

### CHIP OCR-07 — Degree and Program Field Extractor

**Objective:** Extract the academic qualification (Degree: Bachelor of Technology, Master of Science, Ph.D.) and specialization / branch (Computer Science, Mechanical Engineering).

**Why:** Forgers frequently alter degree programs (e.g. elevating a "Diploma" to a "Bachelor of Engineering").

**Dependencies:** CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/degree_extractor.py`

**Implementation:**
1. Build dictionary of standard degrees:
   - `B.Tech`, `Bachelor of Technology`, `B.E.`, `Bachelor of Engineering`, `B.Sc`, `Bachelor of Science`, `B.Com`, `B.A.`, `M.Tech`, `M.S.`, `Ph.D.`, `Doctor of Philosophy`, `MBA`.
2. Build dictionary of disciplines / branches:
   - `Computer Science and Engineering`, `Information Science`, `Electronics and Communication`, `Mechanical Engineering`, `Civil Engineering`, `Artificial Intelligence`, `Business Administration`.
3. Implement matching:
   - Search text lines for degree dictionary occurrences using `rapidfuzz` token set ratio.
   - Identify associated specialization following keywords ("in", "branch of", "discipline of", "specialization in").
4. Return standardized degree and specialization string.

**Acceptance Criteria:**
- Extracts degree title and specialization accurately.

---

### CHIP OCR-08 — Institution and University Name Extractor

**Objective:** Identify the issuing institution, university, or college name from the header region of the certificate.

**Why:** Required to identify the issuing authority and look up university templates in the database for template comparison (Phase 08).

**Dependencies:** CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/institution_extractor.py`

**Implementation:**
1. Restrict search region to the top 35% of the certificate image (`bbox.y_max < 0.35 * image_height`).
2. Search for institutional keywords: `["university", "institute of technology", "college of engineering", "vidyapeeth", "deemed university", "academy of higher education"]`.
3. Fuzzy match against registered `institution` database records (Phase 14 integration).
4. Combine tokens across the prominent header line to form the full institution name.

**Acceptance Criteria:**
- Extracts institution name from header tokens with high confidence.

---

### CHIP OCR-09 — Issue Date and Convocation Date Extractor

**Objective:** Extract and normalize dates appearing on the certificate (Date of Issue, Convocation Date, Examination Passing Date) into ISO 8601 (`YYYY-MM-DD`).

**Why:** Date extraction enables chronological consistency checks in Phase 06 (e.g. issue date cannot be prior to graduation year or in the future).

**Dependencies:** CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/date_extractor.py`

**Implementation:**
1. Compile comprehensive date regex patterns:
   - Numeric: `r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b"` (e.g. `15/06/2023`)
   - Textual: `r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})\b"` (e.g. `15th June, 2023`)
   - Month-Year: `r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b"`
2. Detect date context label:
   - Identify if date is associated with "Dated", "Date of Issue", "Given under our hand", or "Passing Year".
3. Normalize to `datetime.date` using `python-dateutil.parser`.

**Acceptance Criteria:**
- Detects various date formats and normalizes them into ISO standard date format.

---

### CHIP OCR-10 — Grade, CGPA, and Percentage Extractor

**Objective:** Extract academic performance metrics (CGPA on 4.0 or 10.0 scale, Percentage, Division / Class) from the certificate text.

**Why:** Academic scores are among the most frequently forged fields on certificates.

**Dependencies:** CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/grade_extractor.py`

**Implementation:**
1. Define regex patterns:
   - CGPA: `r"(?:cgpa|gpa|cumulative grade point average)\s*[:\-]?\s*([0-9]\.[0-9]{1,2})\b"`
   - Percentage: `r"([0-9]{2}(?:\.[0-9]{1,2})?)\s*%"\b`
   - Division: `r"(?:first class with distinction|first class|second class|pass class|distinction)\b"`
2. Validate numeric ranges:
   - CGPA must be within `0.0 <= val <= 10.0` (or `4.0` depending on scale).
   - Percentage must be within `30.0 <= val <= 100.0`.
3. If value is out of bounds, flag as suspicious field.

**Acceptance Criteria:**
- Accurately captures CGPA, percentage, and division strings.

---

### CHIP OCR-11 — Certificate Serial Number & Barcode/QR Text Extractor

**Objective:** Extract unique printed certificate serial numbers, folio numbers, and decoded QR/barcode data.

**Why:** Provides secondary unique identifier used for anti-counterfeiting tracking and verification against institution databases.

**Dependencies:** CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/field_extractors/cert_id_extractor.py`

**Implementation:**
1. Define serial number label triggers: `["certificate no", "sl no", "serial no", "folio no", "sr no", "cert no"]`.
2. Extract adjacent alphanumeric strings.
3. Integrate OpenCV `cv2.QRCodeDetector()` to detect and read embedded QR codes on the certificate canvas.
4. Compare QR payload text with extracted OCR text (cross-validation).

**Acceptance Criteria:**
- Extracts serial numbers and decoded QR code payload string.

---

### CHIP OCR-12 — Confidence Aggregator, Threshold Flagging & Visualizer

**Objective:** Aggregate token-level confidence scores into field-level scores, flag any field with confidence < 0.70 (FR-OCR-04), and generate an annotated verification image with color-coded bounding boxes.

**Why:** Satisfies FR-OCR-03, FR-OCR-04, and gives users an immediate visual explanation of OCR detection quality (green = high confidence >= 0.70, red/amber = flagged < 0.70).

**Dependencies:** CHIP OCR-02, CHIP OCR-04.

**Files to create:**
- `backend/app/modules/ocr/confidence_evaluator.py`
- `backend/app/modules/ocr/visualizer.py`

**Implementation:**
1. Implement `evaluate_field_confidence(field: ExtractedField, threshold: float = 0.70) -> ExtractedField`:
   - Compute geometric weighted confidence: `sum(tok.confidence * len(tok.text) for tok in tokens) / total_chars`.
   - Set `field.is_flagged = field.confidence < threshold`.
2. Implement `render_ocr_overlay(image: np.ndarray, fields: List[ExtractedField], output_path: Path) -> Path`:
   - Draw polygon bounding box on image canvas using `cv2.polylines`.
   - Green bounding box (`#00E676`) for `confidence >= 0.70`.
   - Red/Orange bounding box (`#FF1744`) for `confidence < 0.70`.
   - Render semi-transparent label tag showing field name and confidence percentage.
   - Save annotated image to `storage/reports/{uuid}_ocr_overlay.png`.

**Acceptance Criteria:**
- Fields with confidence < 0.70 are flagged with `is_flagged=True`.
- Generates clean, high-resolution annotated overlay image.

---

### CHIP OCR-13 — Unit Tests: OCR Recognition Accuracy on Clean and Degraded Scans

**Objective:** Benchmark OCR word recognition accuracy against ground truth on both pristine certificates (>= 95% target) and degraded/noisy scans (>= 85% target) (TC-OCR-01, TC-OCR-02, NFR-01).

**Dependencies:** CHIP OCR-01, CHIP OCR-02.

**Files to create:**
- `backend/tests/unit/test_ocr_engine.py`

**Implementation:**
1. Load synthetic clean certificate fixture with known ground truth text (TC-OCR-01).
2. Run OCR, compute Word Error Rate (WER) and Character Error Rate (CER) using Levenshtein distance.
3. Verify clean word accuracy `(1 - WER) >= 0.95`.
4. Load synthetic degraded certificate fixture (with blur, noise, shadow) (TC-OCR-02).
5. Verify degraded word accuracy `(1 - WER) >= 0.85`.

**Acceptance Criteria:**
- Meets or exceeds 95% word accuracy on clean scans and 85% on degraded scans.

---

### CHIP OCR-14 — Unit Tests: Structured Field Extraction & Low-Confidence Flagging

**Objective:** Test automated extraction of student name, roll number, degree, date, and institution, and verify that fields with confidence < 0.70 are flagged (TC-OCR-03, TC-OCR-04, TC-OCR-05).

**Dependencies:** CHIP OCR-05 through CHIP OCR-12.

**Files to create:**
- `backend/tests/unit/test_field_extractors.py`
- `backend/tests/unit/test_confidence_evaluator.py`

**Implementation:**
1. Test name extractor on 5 synthetic certificates (TC-OCR-03).
2. Test roll number extractor with USN and numeric formats.
3. Test degree and institution extractors.
4. Test low-confidence flagging: create token with confidence 0.65; verify `is_flagged == True` (TC-OCR-04).
5. Test bounding box coordinate mapping (TC-OCR-05).

**Acceptance Criteria:**
- All field extraction test cases pass and low-confidence flagging behaves correctly.

---

## 9. Implementation Order and Dependencies

```
CHIP OCR-01 (PaddleOCR Engine Singleton)
    ↓
CHIP OCR-02 (Token & Bounding Box Dataclasses)
    ↓
CHIP OCR-03 (Spatial Line & Reading Order Analyzer)
    ↓
CHIP OCR-04 (Base Field Extractor Interface)
    ↓
├── CHIP OCR-05 (Student Name Extractor)
├── CHIP OCR-06 (Roll Number Extractor)
├── CHIP OCR-07 (Degree Extractor)
├── CHIP OCR-08 (Institution Extractor)
├── CHIP OCR-09 (Date Extractor)
├── CHIP OCR-10 (Grade Extractor)
└── CHIP OCR-11 (Serial / QR Extractor)
    ↓
CHIP OCR-12 (Confidence Evaluator & Visualizer)
    ↓
CHIP OCR-13 & CHIP OCR-14 (Unit Tests & Accuracy Benchmarks)
```

---

## 10. Phase Completion Checklist

- [ ] PaddleOCR singleton initializes once with CPU MKL-DNN acceleration.
- [ ] OCR tokens include text, 4-point polygon bounding boxes, and confidence scores.
- [ ] Tokens are sorted into reading order and grouped into coherent text lines.
- [ ] Student name extractor identifies names across uppercase, labeled, and cursive patterns.
- [ ] Roll number / USN extractor identifies registration IDs with format validation.
- [ ] Degree, institution, date, grade, and serial numbers are parsed and normalized.
- [ ] Any field with confidence score < 0.70 is flagged for human review.
- [ ] Annotated visual overlay image generated with color-coded bounding boxes.
- [ ] Clean scan OCR achieves >= 95% word recognition accuracy.
- [ ] Degraded scan OCR achieves >= 85% word recognition accuracy.
- [ ] Test cases TC-OCR-01 through TC-OCR-05 passing with 100% success rate.
