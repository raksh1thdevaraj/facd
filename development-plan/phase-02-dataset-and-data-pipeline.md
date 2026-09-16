# Phase 02 — Dataset and Data Pipeline

## 1. Purpose

Create a controlled, labeled dataset of genuine and synthetically manipulated academic certificate images for training, validating, and testing the ML/DL classification model. Establish the data pipeline for dataset generation, labeling, splitting, validation, and versioning.

## 2. Why This Phase Exists

The entire ML pipeline (Phases 09–11) depends on a well-structured, labeled dataset. Without controlled data:
- The ML model cannot be trained
- Evaluation metrics are meaningless
- Ablation studies cannot be conducted

The ML/Data Documents (Part A) explicitly require:
- Synthetic manipulation generation from genuine templates
- Labeled metadata including manipulation type, region, and image quality
- Privacy-safe synthetic/anonymized identities
- Train/validation/test splits with leakage prevention

This phase produces the dataset BEFORE any model training begins.

## 3. Requirements Covered

| Requirement | How |
|---|---|
| FR-ML-01 | Dataset enables training the ML/DL classification model |
| FR-ML-03 | Dataset versioning supports model retraining |
| SRD §6.2 | Training/evaluation data: genuine + synthetically manipulated samples |
| ML/Data Docs A.2–A.7 | All dataset specifications |
| PRD §8 Assumption 1 | Labeled dataset available or constructable |
| **Supporting Requirement** | Dataset pipeline tooling not explicitly in SRD but required to produce the dataset |

## 4. Inputs

- Certificate template images (created or sourced)
- Synthetic student data (names, register numbers, courses, marks, dates)
- Manipulation scripts (to be created)
- ML/Data Docs Part A specifications

## 5. Outputs

- `ml/data/genuine/` — genuine certificate images
- `ml/data/manipulated/` — manipulated certificate images
- `ml/data/metadata.csv` — complete label file with all metadata
- `ml/data/splits/` — train/validation/test split files
- `ml/scripts/generate_dataset.py` — dataset generation script
- `ml/scripts/validate_dataset.py` — dataset validation script
- `ml/data/README.md` — dataset documentation

## 6. Dependencies

- **Previous phases:** Phase 01 (project structure)
- **Libraries:** Pillow, OpenCV, NumPy, pandas, Faker (for synthetic names)
- **External:** Certificate template images (self-created or sourced)
- **Files:** `ml/` directory structure from Phase 01

## 7. Files and Folder Structure

```
ml/
├── data/
│   ├── README.md                      # Dataset documentation
│   ├── metadata.csv                   # Master label file
│   ├── genuine/                       # Genuine certificate images
│   │   ├── GEN_001.png
│   │   ├── GEN_002.png
│   │   └── ...
│   ├── manipulated/                   # Manipulated certificate images
│   │   ├── MAN_001_name_altered.png
│   │   ├── MAN_002_marks_altered.png
│   │   └── ...
│   ├── templates/                     # Base certificate templates
│   │   ├── template_A.png
│   │   └── template_B.png
│   └── splits/
│       ├── train.csv                  # Training split (70%)
│       ├── val.csv                    # Validation split (15%)
│       └── test.csv                   # Test split (15%)
│
├── scripts/
│   ├── generate_templates.py          # Create base certificate templates
│   ├── generate_genuine.py            # Populate templates with synthetic data
│   ├── generate_manipulated.py        # Apply manipulations to genuine samples
│   ├── generate_dataset.py            # Orchestrate full dataset generation
│   ├── validate_dataset.py            # Validate dataset integrity
│   ├── split_dataset.py               # Create train/val/test splits
│   └── dataset_stats.py              # Print dataset statistics
│
├── configs/
│   └── dataset_config.yaml            # Dataset generation parameters
│
└── notebooks/
    └── dataset_exploration.ipynb      # Visual exploration of dataset
```

### File Responsibilities

| File | Responsibility |
|---|---|
| `generate_templates.py` | Create base certificate template images with layout structure (fields, borders, logo areas, seal areas) |
| `generate_genuine.py` | Fill templates with synthetic student data using randomized but realistic field values |
| `generate_manipulated.py` | Apply specific manipulation types to genuine samples, record manipulation metadata |
| `generate_dataset.py` | Orchestrate the full pipeline: templates → genuine → manipulated → metadata → splits |
| `validate_dataset.py` | Check file existence, label consistency, balanced classes, no duplicates |
| `split_dataset.py` | Stratified split ensuring no data leakage (same base certificate in only one split) |
| `dataset_stats.py` | Print class distribution, manipulation type distribution, quality distribution |
| `dataset_config.yaml` | Configurable parameters: number of samples, manipulation ratios, quality settings |

---

## 8. Implementation Chips

---

### CHIP DAT-01 — Install Dataset Generation Dependencies

**Objective:** Install Python libraries needed for dataset generation.

**Why:** Dataset generation requires image manipulation, synthetic data generation, and data management libraries.

**Dependencies:** Phase 01 (Python virtual environment)

**Files to create:** None

**Files to modify:**
- `backend/requirements.txt` — add dataset generation dependencies

**Implementation:**

Add to `requirements.txt` (or a separate `ml/requirements.txt`):
```
Pillow>=10.0.0
opencv-python-headless>=4.8.0
numpy>=1.24.0
pandas>=2.0.0
Faker>=20.0.0
PyYAML>=6.0
```

Install: `pip install -r requirements.txt`

**Inputs:** None

**Outputs:** Libraries installed and importable

**Edge Cases:**
- `opencv-python-headless` vs `opencv-python` — use headless for server/CI (no GUI)
- Pillow version compatibility with Python 3.11+

**Error Handling:** Installation errors — check Python version compatibility.

**Logging:** N/A

**Security:** N/A

**Testing:** `python -c "import cv2, PIL, numpy, pandas, faker"` should succeed.

**Acceptance Criteria:**
- All libraries install without errors
- All libraries importable

**Definition of Done:** Dependencies installed and verified.

---

### CHIP DAT-02 — Create Dataset Configuration

**Objective:** Create a YAML configuration file defining dataset generation parameters.

**Why:** Configuration makes the dataset reproducible and easily adjustable. Parameters like sample counts, manipulation ratios, and quality settings should be configurable, not hardcoded.

**Dependencies:** CHIP DAT-01

**Files to create:**
- `ml/configs/dataset_config.yaml`

**Files to modify:** None

**Implementation:**

Create `ml/configs/dataset_config.yaml`:
```yaml
# Dataset Generation Configuration
dataset:
  name: "certificate_verification_v1"
  random_seed: 42
  
  # Sample counts
  total_genuine: 200          # Initial experiment value — scale up as needed
  total_manipulated: 200      # Match genuine count for balance
  
  # Template families
  templates:
    - name: "university_marksheet_A"
      file: "templates/template_A.png"
    - name: "university_degree_B"
      file: "templates/template_B.png"
  
  # Manipulation distribution (percentage of total_manipulated)
  manipulation_types:
    name_altered: 0.20
    marks_altered: 0.20
    date_altered: 0.15
    cert_number_altered: 0.10
    signature_altered: 0.10
    seal_altered: 0.10
    multiple: 0.15
  
  # Image quality simulation
  quality_distribution:
    high: 0.50               # Clean, well-scanned
    medium: 0.30             # Moderate noise/blur
    low: 0.20               # Phone photo, low-res, skewed
  
  # Data splits
  splits:
    train: 0.70
    val: 0.15
    test: 0.15
  
  # Image parameters
  image:
    width: 2480              # A4 at 300 DPI
    height: 3508
    dpi: 300
    format: "png"

# Synthetic data parameters
synthetic_data:
  locale: "en_IN"            # Indian names/institutions
  institutions:
    - "Visvesvaraya Technological University"
    - "Bangalore University"
    - "Anna University"
  courses:
    - "B.E. in Computer Science and Engineering"
    - "B.Tech in Information Technology"
    - "B.Sc in Mathematics"
  grading_scheme: "percentage"  # percentage or cgpa
  year_range: [2018, 2025]
```

**Inputs:** ML/Data Docs specifications

**Outputs:** Configuration file for dataset generation

**Data Structures:** YAML structure as shown above

**Edge Cases:**
- Manipulation percentages must sum to 1.0 (or close)
- Sample count changes should propagate to split sizes

**Error Handling:** Validate config at load time — check required fields, valid percentages.

**Logging:** Log loaded config at generation start.

**Security:** N/A

**Testing:** Load config and verify all required fields are present.

**Acceptance Criteria:**
- Config file is valid YAML
- All manipulation types from ML/Data Docs A.4 are represented
- Percentages sum to ~1.0
- All parameters documented with comments

**Definition of Done:** Config file created with all parameters documented.

---

### CHIP DAT-03 — Create Certificate Template Generator

**Objective:** Create a script that generates base certificate template images with a realistic layout structure.

**Why:** Templates provide the visual foundation for both genuine and manipulated samples. The layout must include defined regions for: institution name/logo, student name, register number, course, marks/grades, dates, certificate number, signature area, and seal area.

**Dependencies:** CHIP DAT-01, CHIP DAT-02

**Files to create:**
- `ml/scripts/generate_templates.py`

**Files to modify:** None

**Implementation:**

Create a script that uses Pillow to generate certificate template images:

1. Create a blank white canvas at A4 dimensions (2480×3508 at 300 DPI).
2. Add a decorative border (rectangle with border styling).
3. Add placeholder regions for each certificate field:
   - Header: institution name, logo area (top center)
   - Title: "MARKS CARD" / "DEGREE CERTIFICATE" (centered)
   - Student info fields: name, register number, course (left-aligned rows)
   - Marks/grades table area (structured table region)
   - Dates: issue date, exam date
   - Certificate number (top-right or bottom)
   - Signature area (bottom-left)
   - Seal area (bottom-right)
4. Use standard fonts (e.g., Times New Roman, Arial) — package free fonts or use PIL defaults.
5. Define field coordinates as a layout dictionary for later data population.
6. Save template images and a corresponding layout JSON defining field bounding boxes.

Output layout JSON:
```json
{
  "template_id": "template_A",
  "fields": {
    "institution_name": {"x": 400, "y": 200, "width": 1680, "height": 80, "font_size": 36},
    "title": {"x": 800, "y": 350, "width": 880, "height": 60, "font_size": 28},
    "student_name": {"x": 400, "y": 600, "width": 1200, "height": 50, "font_size": 22},
    "register_number": {"x": 400, "y": 700, "width": 800, "height": 50, "font_size": 22},
    "course": {"x": 400, "y": 800, "width": 1200, "height": 50, "font_size": 22},
    "marks": {"x": 400, "y": 1000, "width": 1680, "height": 800, "font_size": 18},
    "issue_date": {"x": 400, "y": 2000, "width": 600, "height": 50, "font_size": 18},
    "cert_number": {"x": 1600, "y": 150, "width": 600, "height": 40, "font_size": 16},
    "signature_area": {"x": 300, "y": 2800, "width": 500, "height": 300},
    "seal_area": {"x": 1700, "y": 2800, "width": 400, "height": 400}
  }
}
```

**Inputs:** Dataset configuration (template specifications)

**Outputs:**
- `ml/data/templates/template_A.png`
- `ml/data/templates/template_A_layout.json`
- `ml/data/templates/template_B.png`
- `ml/data/templates/template_B_layout.json`

**Edge Cases:**
- Font not available — use PIL default font with fallback
- Different certificate formats — create at least 2 template families

**Error Handling:** Validate canvas dimensions, raise error for invalid layout coordinates.

**Logging:** Log template creation with dimensions and field count.

**Security:** N/A

**Testing:**
- Verify generated template images have correct dimensions
- Verify layout JSON has all required fields
- Visually inspect at least one template

**Acceptance Criteria:**
- At least 2 certificate template families generated
- Each template has a corresponding layout JSON
- Layout JSON defines bounding boxes for all certificate fields
- Templates look realistic (borders, structured layout)

**Definition of Done:** Templates generated, layout files created, visually verified.

---

### CHIP DAT-04 — Create Synthetic Student Data Generator

**Objective:** Generate realistic but synthetic student data (no real PII) for populating certificate templates.

**Why:** Real student data cannot be used (privacy). Synthetic data must be realistic enough that OCR/text-consistency checks produce meaningful results. The ML/Data Docs (A.7) explicitly require synthetic/anonymized identities.

**Dependencies:** CHIP DAT-01 (Faker library)

**Files to create:**
- `ml/scripts/synthetic_data.py`

**Files to modify:** None

**Implementation:**

Create `ml/scripts/synthetic_data.py`:
```python
import random
from faker import Faker
from dataclasses import dataclass
from typing import List

fake = Faker('en_IN')

@dataclass
class StudentRecord:
    student_name: str
    register_number: str
    course: str
    institution: str
    marks: dict           # subject → mark
    total_marks: int
    percentage: float
    result: str           # "PASS" / "FAIL" / "DISTINCTION"
    exam_date: str
    issue_date: str
    certificate_number: str

def generate_register_number(institution_code: str, year: int) -> str:
    """Generate realistic register number like '1VT18CS001'."""
    seq = random.randint(1, 200)
    return f"{institution_code}{year % 100:02d}CS{seq:03d}"

def generate_marks(num_subjects: int = 6) -> dict:
    """Generate marks for subjects with realistic distribution."""
    subjects = ["Mathematics", "Physics", "Computer Science", 
                "Electronics", "English", "Engineering Drawing"]
    marks = {}
    for subj in subjects[:num_subjects]:
        marks[subj] = random.randint(35, 100)
    return marks

def generate_student_record(config: dict) -> StudentRecord:
    """Generate a complete synthetic student record."""
    institution = random.choice(config['institutions'])
    course = random.choice(config['courses'])
    year = random.randint(*config['year_range'])
    marks = generate_marks()
    total = sum(marks.values())
    percentage = total / len(marks)
    
    return StudentRecord(
        student_name=fake.name(),
        register_number=generate_register_number("1VT", year),
        course=course,
        institution=institution,
        marks=marks,
        total_marks=total,
        percentage=round(percentage, 2),
        result="DISTINCTION" if percentage >= 70 else "PASS" if percentage >= 35 else "FAIL",
        exam_date=f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/{year}",
        issue_date=f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/{year + 1}",
        certificate_number=f"VTU/{year}/{random.randint(10000, 99999)}",
    )
```

**Inputs:** Dataset configuration (institutions, courses, year range)

**Outputs:** `StudentRecord` objects with all certificate fields populated

**Data Structures:** `StudentRecord` dataclass as shown above

**Edge Cases:**
- Issue date must be after exam date — enforce in generation
- Register number format varies by institution — parameterize format
- Edge grades (exactly 35, exactly 100)

**Error Handling:** Validate generated dates are logically consistent.

**Logging:** Log number of records generated.

**Security:** Ensure NO real student names/numbers are used. Faker generates random names.

**Testing:**
```python
def test_generate_student_record():
    config = {"institutions": ["Test Univ"], "courses": ["B.E."], "year_range": [2020, 2024]}
    record = generate_student_record(config)
    assert record.student_name  # not empty
    assert 35 <= record.percentage <= 100
    assert record.issue_date > record.exam_date  # date logic
```

**Acceptance Criteria:**
- Records have all required fields populated
- Names are synthetic (Faker-generated)
- Dates are logically consistent
- Marks are in valid range (35–100)
- Register numbers follow a consistent pattern

**Definition of Done:** Student data generator produces valid, realistic synthetic records.

---

### CHIP DAT-05 — Create Genuine Certificate Generator

**Objective:** Populate certificate templates with synthetic student data to create genuine certificate images.

**Why:** Genuine samples form the "negative class" (not manipulated). They must look realistic so the model learns what real certificates look like.

**Dependencies:** CHIP DAT-03, CHIP DAT-04

**Files to create:**
- `ml/scripts/generate_genuine.py`

**Files to modify:** None

**Implementation:**

1. Load a certificate template image and its layout JSON.
2. Generate a `StudentRecord` using the synthetic data generator.
3. Render each field value onto the template at the coordinates specified in the layout:
   - Use Pillow's `ImageDraw.text()` with appropriate font/size
   - Render marks in a table format
   - Add a synthetic signature (simple handwriting-style line/squiggle)
   - Add a synthetic seal (circular stamp with institution text)
4. Save the populated certificate image.
5. Record metadata: `sample_id`, `class=genuine`, `manipulation_type=none`, `source_institution_format`, `image_quality=high`.

**Inputs:** Template images, layout JSONs, dataset config

**Outputs:** Genuine certificate images in `ml/data/genuine/`, metadata records

**Edge Cases:**
- Text overflow — truncate or reduce font size
- Long names — handle multi-line rendering
- Special characters in names — handle Unicode

**Error Handling:** Skip and log samples where rendering fails.

**Logging:** Log each generated sample with ID and template used.

**Security:** N/A

**Testing:**
- Verify output images have correct dimensions
- Verify text is readable (visual spot-check)
- Verify metadata records match generated images

**Acceptance Criteria:**
- At least 200 genuine certificates generated (per config)
- Each has complete metadata entry
- Text is legible in the generated images
- Multiple template families used

**Definition of Done:** Genuine dataset generated with metadata.

---

### CHIP DAT-06 — Create Image Quality Simulator

**Objective:** Apply realistic quality degradation to certificate images to simulate different scanning/photography conditions.

**Why:** Real-world certificates arrive as phone photos, low-res scans, and screenshots. The model must handle varying quality. ML/Data Docs A.6 requires a range of scan qualities.

**Dependencies:** CHIP DAT-01

**Files to create:**
- `ml/scripts/quality_simulator.py`

**Files to modify:** None

**Implementation:**

Create `ml/scripts/quality_simulator.py` with functions for:
1. **High quality** — no degradation (original)
2. **Medium quality** — slight Gaussian blur (σ=1), minor noise, JPEG compression (quality=85)
3. **Low quality** — heavier blur (σ=2), additive noise, rotation (±2°), resolution reduction (50%), JPEG compression (quality=60), slight perspective warp

```python
def apply_quality(image: Image, quality_level: str) -> Image:
    if quality_level == "high":
        return image
    elif quality_level == "medium":
        return apply_medium_quality(image)
    elif quality_level == "low":
        return apply_low_quality(image)
```

Each function applies the appropriate transformations using Pillow and OpenCV.

**Inputs:** PIL Image, quality level string

**Outputs:** Degraded PIL Image

**Edge Cases:**
- Image already low-quality — don't double-degrade
- Quality degradation must not make text completely illegible

**Error Handling:** Invalid quality level raises `ValueError`.

**Logging:** Log applied quality transformations.

**Security:** N/A

**Testing:**
- High quality image unchanged
- Medium quality image has visible but readable degradation
- Low quality image is degraded but still recognizable as a certificate

**Acceptance Criteria:**
- Three quality levels implemented
- Degradation is visually realistic
- Text remains readable at medium quality
- Quality is recorded in metadata

**Definition of Done:** Quality simulator produces three levels of degradation.

---

### CHIP DAT-07 — Create Name Alteration Manipulation

**Objective:** Implement programmatic name-field alteration to generate `name_altered` manipulation samples.

**Why:** Name alteration is one of the most common certificate forgeries. The manipulation must be detectable by font/spacing analysis and OCR comparison.

**Dependencies:** CHIP DAT-05, CHIP DAT-06

**Files to create:**
- `ml/scripts/manipulations/name_alter.py`

**Files to modify:** None

**Implementation:**

1. Load a genuine certificate image and its corresponding layout JSON.
2. Identify the student name field region from the layout.
3. Apply one or more manipulation techniques:
   - **Font-matched replacement**: Erase the name region (fill with background color), render a different name in the same font/size.
   - **Font-mismatched replacement**: Erase and render with a slightly different font (to simulate a less sophisticated forgery).
   - **Character-level editing**: Replace individual characters (e.g., change one letter of the name).
4. Record the manipulation bounding box and type.

```python
def alter_name(image: Image, layout: dict, new_name: str, method: str = "matched") -> tuple:
    """
    Returns: (manipulated_image, manipulation_bbox)
    """
    field = layout["fields"]["student_name"]
    bbox = (field["x"], field["y"], field["x"] + field["width"], field["y"] + field["height"])
    
    # Erase original region
    draw = ImageDraw.Draw(image)
    draw.rectangle(bbox, fill="white")
    
    # Render new name
    font = get_font(field["font_size"], matched=(method == "matched"))
    draw.text((field["x"], field["y"]), new_name, fill="black", font=font)
    
    return image, bbox
```

**Inputs:** Genuine certificate image, layout JSON, new name

**Outputs:** Manipulated image, manipulation bounding box

**Edge Cases:**
- Background not perfectly white — sample background color before erasing
- Name region overlaps with other fields — crop carefully
- Font unavailable — use closest match

**Error Handling:** If region coordinates are invalid, skip sample and log warning.

**Logging:** Log manipulation applied: original name → new name, method used.

**Security:** N/A

**Testing:**
- Visually verify the name region is altered
- Verify bounding box correctly covers the altered region
- Run OCR on the manipulated image — should extract the NEW name

**Acceptance Criteria:**
- Name is visibly changed in the output image
- Both font-matched and font-mismatched methods work
- Manipulation bounding box accurately marks the altered region

**Definition of Done:** Name alteration function produces detectable manipulations with metadata.

---

### CHIP DAT-08 — Create Marks/Grades Alteration Manipulation

**Objective:** Implement marks/grades field alteration for `marks_altered` samples.

**Why:** Marks alteration is another highly common certificate forgery. Different from name alteration because marks are typically in a table format with specific numeric patterns.

**Dependencies:** CHIP DAT-05

**Files to create:**
- `ml/scripts/manipulations/marks_alter.py`

**Files to modify:** None

**Implementation:**

1. Locate marks/grades region in the layout.
2. Apply manipulation:
   - Change one or more marks values (e.g., 45 → 85)
   - Change total/percentage
   - Change result (FAIL → PASS)
3. Use font-matched or mismatched replacement.
4. Record the manipulation bounding box.

**Inputs:** Genuine certificate image, layout JSON

**Outputs:** Manipulated image, manipulation bounding box, altered fields list

**Edge Cases:**
- Table cell boundaries — must not overflow into adjacent cells
- Number widths differ (1 digit vs 2 digits) — handle alignment
- Percentage/total must be inconsistent with individual marks (this is intentional — the text-consistency module should catch this)

**Error Handling:** Skip if marks region cannot be located.

**Logging:** Log original → altered values.

**Security:** N/A

**Testing:** Visual check + OCR verification of altered values.

**Acceptance Criteria:**
- Marks visibly altered
- Bounding box accurate
- Intentional inconsistency between marks and total (for text-consistency testing)

**Definition of Done:** Marks alteration produces detectable manipulations.

---

### CHIP DAT-09 — Create Date, Cert Number, Signature, and Seal Manipulations

**Objective:** Implement remaining manipulation types: `date_altered`, `cert_number_altered`, `signature_altered`, `seal_altered`.

**Why:** Complete coverage of all manipulation types defined in ML/Data Docs A.4. Each type targets a different field/region for comprehensive forensic testing.

**Dependencies:** CHIP DAT-05

**Files to create:**
- `ml/scripts/manipulations/date_alter.py`
- `ml/scripts/manipulations/cert_number_alter.py`
- `ml/scripts/manipulations/signature_alter.py`
- `ml/scripts/manipulations/seal_alter.py`

**Files to modify:** None

**Implementation:**

1. **Date alteration**: Change exam date or issue date. Optionally create impossible dates (e.g., issue date before exam date) to test text-consistency checks.
2. **Cert number alteration**: Change certificate serial number pattern (e.g., different year code, wrong sequence format).
3. **Signature alteration**: Replace signature region with a signature from a different sample (copy-paste from another certificate). This also exercises copy-paste detection.
4. **Seal alteration**: Replace or blur the seal region, or overlay a seal from a different institution.

Each function follows the same pattern: locate region → erase → render replacement → record bbox.

**Inputs:** Genuine certificate images, layout JSONs

**Outputs:** Manipulated images with metadata for each manipulation type

**Edge Cases:**
- Signature/seal regions may have complex backgrounds
- Date formats may vary — handle DD/MM/YYYY and Month DD, YYYY

**Error Handling:** Skip samples where region detection fails.

**Logging:** Log each manipulation type and affected region.

**Security:** N/A

**Testing:** Visual verification + metadata consistency check for each type.

**Acceptance Criteria:**
- All 4 manipulation types produce altered images
- Bounding boxes accurately mark altered regions
- Each type is distinguishable from others

**Definition of Done:** All remaining single-manipulation types implemented with metadata.

---

### CHIP DAT-10 — Create Multiple-Manipulation Combiner

**Objective:** Generate samples with multiple simultaneous manipulations (`multiple` type).

**Why:** Real-world forgeries may alter multiple fields simultaneously. The model must detect multi-field manipulation. ML/Data Docs A.4 includes `multiple` as a manipulation type.

**Dependencies:** CHIP DAT-07, DAT-08, DAT-09

**Files to create:**
- `ml/scripts/manipulations/multi_alter.py`

**Files to modify:** None

**Implementation:**

1. Randomly select 2–3 manipulation types from the available set.
2. Apply them sequentially to the same genuine image.
3. Record ALL bounding boxes and manipulation types.

```python
def apply_multiple_manipulations(image, layout, count=2):
    manipulations = random.sample(AVAILABLE_TYPES, count)
    all_bboxes = []
    all_types = []
    for manip_type in manipulations:
        image, bbox = MANIPULATION_FUNCTIONS[manip_type](image, layout)
        all_bboxes.append(bbox)
        all_types.append(manip_type)
    return image, all_bboxes, all_types
```

**Inputs:** Genuine image, layout, number of simultaneous manipulations

**Outputs:** Image with multiple alterations, list of bounding boxes, list of manipulation types

**Edge Cases:**
- Overlapping manipulation regions — allow it (tests robustness)
- Conflicting manipulations — e.g., both name and marks altered may create unrealistic combinations

**Error Handling:** If one manipulation fails, log and continue with the rest.

**Logging:** Log all applied manipulations per sample.

**Security:** N/A

**Testing:** Visual check — multiple regions should be altered.

**Acceptance Criteria:**
- Multiple manipulations applied to single image
- All bounding boxes recorded
- Manipulation type list accurately reflects all alterations

**Definition of Done:** Multi-manipulation combiner works with all individual manipulation types.

---

### CHIP DAT-11 — Create Copy-Paste (Clone) Manipulation

**Objective:** Generate copy-paste/clone manipulation samples specifically for forensic clone-detection testing.

**Why:** FR-FOR-01 requires clone/copy-paste detection. The dataset must contain samples with duplicated regions so the forensics module can be tested.

**Dependencies:** CHIP DAT-05

**Files to create:**
- `ml/scripts/manipulations/clone_region.py`

**Files to modify:** None

**Implementation:**

1. Select a region from the certificate (e.g., a digit, a text block, a stamp portion).
2. Copy the region.
3. Paste it at a different location on the same certificate (with optional slight rotation/scale).
4. Record both source and destination bounding boxes.

This is distinct from field-level alterations — it creates detectable duplicate regions.

**Inputs:** Certificate image, region to clone

**Outputs:** Image with cloned region, source bbox, destination bbox

**Edge Cases:**
- Pasted region must not overlap with the source region (for clear detection)
- Small cloned regions may be hard to detect — use meaningful-sized regions

**Error Handling:** Skip if source region is too small.

**Logging:** Log clone source and destination coordinates.

**Security:** N/A

**Testing:** Visual check — duplicated region should be visible.

**Acceptance Criteria:**
- Clone creates a visible duplicate region
- Both source and destination bounding boxes recorded
- Clone is detectable by basic image comparison techniques

**Definition of Done:** Clone manipulation produces samples with detectable duplicated regions.

---

### CHIP DAT-12 — Create Dataset Orchestration Script

**Objective:** Create a master script that orchestrates the entire dataset generation pipeline from templates to final labeled dataset.

**Why:** The full dataset generation must be reproducible with a single command. The random seed ensures deterministic output.

**Dependencies:** CHIP DAT-03 through DAT-11

**Files to create:**
- `ml/scripts/generate_dataset.py`

**Files to modify:** None

**Implementation:**

```python
def main():
    config = load_config("ml/configs/dataset_config.yaml")
    random.seed(config["dataset"]["random_seed"])
    
    # Step 1: Generate templates (if not already present)
    generate_templates(config)
    
    # Step 2: Generate genuine samples
    genuine_metadata = generate_genuine_samples(config)
    
    # Step 3: Apply quality degradation
    apply_quality_variations(genuine_metadata, config)
    
    # Step 4: Generate manipulated samples from genuine
    manipulated_metadata = generate_manipulated_samples(genuine_metadata, config)
    
    # Step 5: Combine metadata
    all_metadata = genuine_metadata + manipulated_metadata
    
    # Step 6: Save master metadata CSV
    save_metadata(all_metadata, "ml/data/metadata.csv")
    
    # Step 7: Print stats
    print_dataset_stats(all_metadata)
```

**Inputs:** `dataset_config.yaml`

**Outputs:** Complete dataset in `ml/data/` with metadata CSV

**Data Structures:**

`metadata.csv` columns:
```
sample_id,file_path,class,manipulation_type,manipulation_region,source_template,base_genuine_id,image_quality
GEN_001,genuine/GEN_001.png,genuine,none,,template_A,,high
MAN_001,manipulated/MAN_001_name_altered.png,manipulated,name_altered,"[400,600,1600,650]",template_A,GEN_001,high
```

**Edge Cases:**
- Script interrupted mid-generation — handle partial datasets
- Disk space — check available space before generating

**Error Handling:** Continue on individual sample failures, log errors, report total at end.

**Logging:** Progress bar or periodic progress messages.

**Security:** N/A

**Testing:** Run script, verify output file count matches config.

**Acceptance Criteria:**
- Single command generates entire dataset
- Random seed produces deterministic output
- Metadata CSV has one row per sample
- Class distribution matches config ratios

**Definition of Done:** Full dataset generation reproducible from single command.

---

### CHIP DAT-13 — Create Dataset Splitter

**Objective:** Split the dataset into train/validation/test sets with stratification and leakage prevention.

**Why:** Proper splitting is critical for valid model evaluation. The same base certificate must NOT appear in both training and test sets (leakage). ML/Data Docs A.3 defines 70/15/15 split.

**Dependencies:** CHIP DAT-12

**Files to create:**
- `ml/scripts/split_dataset.py`

**Files to modify:** None

**Implementation:**

1. Load `metadata.csv`.
2. Group samples by `base_genuine_id` — a genuine certificate and all its derived manipulations form a "family".
3. Split at the family level (not sample level) to prevent leakage.
4. Stratify by `class` (genuine/manipulated) and `manipulation_type` to ensure balanced representation.
5. Save `train.csv`, `val.csv`, `test.csv` in `ml/data/splits/`.

```python
from sklearn.model_selection import GroupShuffleSplit

def split_dataset(metadata_df, config):
    # Group by base certificate to prevent leakage
    groups = metadata_df['base_genuine_id'].fillna(metadata_df['sample_id'])
    
    # First split: separate test set
    gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=config['random_seed'])
    train_val_idx, test_idx = next(gss.split(metadata_df, groups=groups))
    
    # Second split: separate validation from training
    train_val_df = metadata_df.iloc[train_val_idx]
    train_val_groups = groups.iloc[train_val_idx]
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.176, random_state=config['random_seed'])  # 0.176 * 0.85 ≈ 0.15
    train_idx, val_idx = next(gss2.split(train_val_df, groups=train_val_groups))
    
    return train_df, val_df, test_df
```

**Inputs:** `metadata.csv`, split ratios from config

**Outputs:** `train.csv`, `val.csv`, `test.csv`

**Edge Cases:**
- Very small dataset — some manipulation types may not appear in all splits
- `base_genuine_id` is None for genuine samples — use `sample_id` as the group

**Error Handling:** Warn if any manipulation type is missing from a split.

**Logging:** Log split sizes and class distributions per split.

**Security:** N/A

**Testing:**
- Verify no `base_genuine_id` appears in both train and test
- Verify split ratios are approximately 70/15/15
- Verify both classes present in all splits

**Acceptance Criteria:**
- No data leakage between splits
- Split ratios within ±5% of target
- All manipulation types represented in training set
- Test set contains examples of each manipulation type

**Definition of Done:** Leakage-free stratified splits created and validated.

---

### CHIP DAT-14 — Create Dataset Validator

**Objective:** Create a script that validates the integrity and completeness of the generated dataset.

**Why:** Before any model training, the dataset must be verified: no missing files, no duplicate sample IDs, correct label format, balanced classes, valid bounding boxes.

**Dependencies:** CHIP DAT-12, DAT-13

**Files to create:**
- `ml/scripts/validate_dataset.py`

**Files to modify:** None

**Implementation:**

Validation checks:
1. Every `file_path` in `metadata.csv` exists on disk.
2. No duplicate `sample_id` values.
3. All `class` values are either `genuine` or `manipulated`.
4. All `manipulation_type` values are from the allowed set.
5. Genuine samples have `manipulation_type = none`.
6. Manipulated samples have `manipulation_type ≠ none`.
7. Manipulated samples have non-empty `manipulation_region`.
8. Image files are readable (can be opened by PIL).
9. Class distribution is approximately balanced (within tolerance).
10. Split files reference only valid sample IDs.
11. No sample appears in more than one split.

Output: Validation report (pass/fail per check, warnings).

**Inputs:** `metadata.csv`, split files, image directory

**Outputs:** Validation report (printed + saved to `ml/data/validation_report.txt`)

**Edge Cases:**
- Partial dataset (generation interrupted) — report missing files
- Corrupted images — flag as invalid

**Error Handling:** Report all errors but don't fail on first error.

**Logging:** Log all checks and their results.

**Security:** N/A

**Testing:** Run on the generated dataset — all checks should pass.

**Acceptance Criteria:**
- All validation checks pass on the generated dataset
- Report clearly identifies any issues
- Zero missing files
- Zero duplicate IDs

**Definition of Done:** Validation passes with no errors.

---

### CHIP DAT-15 — Create Dataset Statistics Script

**Objective:** Print and save descriptive statistics about the dataset.

**Why:** Statistics provide evidence of dataset quality for the evaluation report (Testing Docs Part C) and the final project documentation.

**Dependencies:** CHIP DAT-12

**Files to create:**
- `ml/scripts/dataset_stats.py`

**Files to modify:** None

**Implementation:**

Print:
1. Total samples (genuine + manipulated)
2. Class distribution (count + percentage)
3. Manipulation type distribution (count + percentage per type)
4. Template family distribution
5. Image quality distribution (high/medium/low)
6. Per-split statistics (train/val/test)
7. Sample image paths for visual inspection

```
=== Dataset Statistics ===
Total samples: 400
  Genuine: 200 (50.0%)
  Manipulated: 200 (50.0%)

Manipulation Type Distribution:
  name_altered: 40 (20.0%)
  marks_altered: 40 (20.0%)
  date_altered: 30 (15.0%)
  cert_number_altered: 20 (10.0%)
  signature_altered: 20 (10.0%)
  seal_altered: 20 (10.0%)
  multiple: 30 (15.0%)

Quality Distribution:
  high: 200 (50.0%)
  medium: 120 (30.0%)
  low: 80 (20.0%)
```

**Inputs:** `metadata.csv`

**Outputs:** Statistics printed to console + saved to `ml/data/dataset_stats.txt`

**Edge Cases:** Empty dataset — report zero counts.

**Error Handling:** N/A

**Logging:** N/A

**Security:** N/A

**Testing:** Verify output matches expected counts from config.

**Acceptance Criteria:**
- Statistics match the dataset config
- All distribution types covered
- Output is human-readable

**Definition of Done:** Statistics script runs and produces correct output.

---

### CHIP DAT-16 — Create Dataset Documentation

**Objective:** Write the dataset README with full documentation.

**Why:** ML/Data Docs require dataset documentation for reproducibility and academic reporting. This documents data sources, consent, generation methodology, labeling scheme, and known limitations.

**Dependencies:** CHIP DAT-12, DAT-14, DAT-15

**Files to create:**
- `ml/data/README.md`

**Files to modify:** None

**Implementation:**

Document the following in `ml/data/README.md`:
1. **Purpose** — training/evaluation dataset for certificate authenticity detection
2. **Source** — synthetically generated from certificate templates
3. **Consent** — no real PII used; all student data is Faker-generated
4. **Generation methodology** — reference to scripts, config, manipulation types
5. **Anonymization** — fully synthetic identities
6. **File naming convention** — `GEN_XXX` for genuine, `MAN_XXX_type` for manipulated
7. **Metadata columns** — explain each column in metadata.csv
8. **Label definitions** — class values, manipulation types
9. **Bounding box format** — [x, y, width, height]
10. **Image quality categories** — high/medium/low definitions
11. **Split strategy** — family-level splitting, leakage prevention
12. **Dataset versioning** — version tag in config
13. **Known limitations** — synthetic only, limited template families, controlled manipulations
14. **Regeneration instructions** — `python ml/scripts/generate_dataset.py`

**Inputs:** ML/Data Docs specifications, generated stats

**Outputs:** `ml/data/README.md`

**Edge Cases:** N/A

**Error Handling:** N/A

**Logging:** N/A

**Security:** N/A

**Testing:** Verify all required sections are present.

**Acceptance Criteria:**
- README covers all required sections from ML/Data Docs A.1–A.7
- Regeneration instructions are complete
- Privacy/consent section explicitly states no real PII

**Definition of Done:** Complete dataset documentation written.

---

### CHIP DAT-17 — Add Compression Artifact Samples

**Objective:** Generate manipulation samples with JPEG re-compression artifacts for forensics testing.

**Why:** FR-FOR-03 requires detection of compression-artifact irregularities (ELA-style checks). The dataset must contain samples with locally re-saved regions at different compression levels.

**Dependencies:** CHIP DAT-05

**Files to create:**
- `ml/scripts/manipulations/compression_artifact.py`

**Files to modify:**
- `ml/scripts/generate_manipulated.py` — integrate compression artifact generation

**Implementation:**

1. Take a genuine certificate image.
2. Select a region (e.g., the marks area).
3. Extract the region, save it as a low-quality JPEG, reload it, and paste it back.
4. The rest of the image remains at original quality — creating detectable compression inconsistency.
5. Record the affected bounding box.

This is specifically different from the quality simulator (which degrades the entire image). Here, only a LOCAL region has different compression artifacts.

**Inputs:** Genuine certificate image, region to re-compress

**Outputs:** Image with local compression artifact, bounding box

**Edge Cases:**
- Very small regions may not show detectable artifacts
- PNG source → JPEG region → paste back creates obvious boundary

**Error Handling:** Skip if region too small.

**Logging:** Log compression quality level used.

**Security:** N/A

**Testing:** Run ELA on the output — the manipulated region should have different error levels.

**Acceptance Criteria:**
- Local compression artifacts are detectable by ELA analysis
- Bounding box accurately marks the re-compressed region

**Definition of Done:** Compression artifact samples generated and verified.

---

### CHIP DAT-18 — Run Full Dataset Generation and Validation

**Objective:** Execute the complete dataset pipeline and validate the results.

**Why:** Final integration of all dataset generation components. This produces the actual dataset used for all ML training.

**Dependencies:** CHIP DAT-01 through DAT-17

**Files to create:** None (all scripts already created)

**Files to modify:** None

**Implementation:**

1. Run `python ml/scripts/generate_dataset.py`
2. Run `python ml/scripts/split_dataset.py`
3. Run `python ml/scripts/validate_dataset.py`
4. Run `python ml/scripts/dataset_stats.py`
5. Visually inspect 10–20 samples (5 genuine, 5 manipulated of different types)
6. Commit dataset scripts and configs (NOT the dataset files themselves — they are gitignored)

**Inputs:** All scripts and configs from previous chips

**Outputs:** Complete validated dataset

**Edge Cases:**
- Generation takes too long — reduce sample count for initial testing
- Disk space issues — check available space first

**Error Handling:** Address any validation failures before proceeding to Phase 09.

**Logging:** Full generation and validation logs.

**Security:** Dataset files stay local, gitignored.

**Testing:** Validation script passes all checks.

**Acceptance Criteria:**
- All images generated successfully
- Metadata complete and consistent
- Validation passes with zero errors
- Dataset statistics match config
- Visual inspection confirms quality
- Splits are leakage-free

**Definition of Done:** Dataset is generated, validated, split, documented, and ready for ML training.

---

## Chip Dependency Graph

```
DAT-01 (Dependencies)
   ↓
DAT-02 (Config)
   ↓
   ├──→ DAT-03 (Template generator)
   │       ↓
   │    DAT-05 (Genuine certificate gen) ← DAT-04
   │       ↓
   │       ├──→ DAT-07 (Name alteration)
   │       ├──→ DAT-08 (Marks alteration)
   │       ├──→ DAT-09 (Date/cert#/sig/seal alteration)
   │       ├──→ DAT-11 (Clone manipulation)
   │       └──→ DAT-17 (Compression artifacts)
   │              ↓
   │           DAT-10 (Multiple manipulations) ← DAT-07, DAT-08, DAT-09
   │              ↓
   │           DAT-12 (Orchestration script)
   │              ↓
   │              ├──→ DAT-13 (Dataset splitter)
   │              ├──→ DAT-14 (Dataset validator) ← DAT-13
   │              └──→ DAT-15 (Dataset stats)
   │                      ↓
   │                   DAT-16 (Documentation)
   │
   └──→ DAT-04 (Synthetic student data) — independent of DAT-03
          ↓
       DAT-06 (Quality simulator) — independent, used by DAT-05

DAT-18 (Full run + validation) ← all above
```

### Parallel Development Opportunities

- DAT-03 (templates) and DAT-04 (synthetic data) can be developed in parallel
- DAT-07, DAT-08, DAT-09, DAT-11, DAT-17 (individual manipulation types) can all be developed in parallel
- DAT-06 (quality simulator) is independent and can be developed anytime after DAT-01

---

## Phase Completion Checklist

```
[ ] DAT-01: Dependencies installed
[ ] DAT-02: Dataset config created
[ ] DAT-03: Certificate templates generated
[ ] DAT-04: Synthetic student data generator working
[ ] DAT-05: Genuine certificates generated
[ ] DAT-06: Image quality simulator working
[ ] DAT-07: Name alteration working
[ ] DAT-08: Marks alteration working
[ ] DAT-09: Date/cert number/signature/seal alterations working
[ ] DAT-10: Multiple manipulation combiner working
[ ] DAT-11: Clone/copy-paste manipulation working
[ ] DAT-12: Full orchestration script working
[ ] DAT-13: Dataset splits created (leakage-free)
[ ] DAT-14: Dataset validation passes
[ ] DAT-15: Dataset statistics generated
[ ] DAT-16: Dataset README documentation complete
[ ] DAT-17: Compression artifact samples generated
[ ] DAT-18: Full pipeline run completed and verified
[ ] Git commits created for all scripts and configs
```

## Phase Acceptance Criteria

- Running `python ml/scripts/generate_dataset.py` produces at least 400 labeled certificate images (200 genuine + 200 manipulated).
- `metadata.csv` has one row per image with all required columns populated.
- `validate_dataset.py` reports zero errors.
- Train/validation/test splits exist with approximately 70/15/15 ratio.
- No `base_genuine_id` appears in more than one split (no leakage).
- All 7 manipulation types (name, marks, date, cert_number, signature, seal, multiple) are represented.
- All 3 quality levels (high, medium, low) are represented.
- No real PII in the dataset.
- Dataset README is complete.

## Recommended Git Commits

```
feat: add dataset generation dependencies and config
feat: create certificate template generator
feat: create synthetic student data generator
feat: create genuine certificate generator
feat: add image quality simulator
feat: implement name and marks manipulation generators
feat: implement date, cert number, signature, seal manipulations
feat: add clone/copy-paste and compression artifact manipulations
feat: create multiple-manipulation combiner
feat: add dataset orchestration, splitting, and validation scripts
feat: add dataset statistics and documentation
feat: generate and validate complete dataset (v1)
```
