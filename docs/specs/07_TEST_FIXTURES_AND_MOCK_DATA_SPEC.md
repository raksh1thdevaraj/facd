# Test Fixtures & Mock Data Specification

**Document ID:** SPEC-07  
**Status:** Approved / Authoritative  
**Domain:** Automated Testing, Mock Fixtures, Seed Scripts  

---

## 1. Purpose

This document specifies the required automated test fixtures, synthetic mock files, institutional seed records, and test assertion tolerances. Having standardized test fixtures ensures that the AI developer can build and verify unit, integration, and end-to-end tests deterministically.

---

## 2. Directory Layout for Test Fixtures

```text
tests/
├── fixtures/
│   ├── certificates/
│   │   ├── valid_clean_certificate.png
│   │   ├── tampered_grades_certificate.png
│   │   ├── copy_move_certificate.png
│   │   ├── skewed_30deg_photo.jpg
│   │   ├── sample_two_page.pdf
│   │   └── corrupted_zero_byte.png
│   ├── ocr_responses/
│   │   └── mock_tesseract_output.json
│   └── institutional_records/
│       └── mock_students.csv
├── conftest.py
├── test_ingestion.py
├── test_preprocessing.py
├── test_ocr.py
├── test_forensics.py
├── test_text_consistency.py
├── test_score_fusion.py
└── test_api_e2e.py
```

---

## 3. Standard Synthetic Certificate Fixtures

The AI developer must write a fixture generator script (`tests/fixtures/generate_fixtures.py`) utilizing Pillow to create the required test images deterministically if binary files are not checked in:

| File Name | Characteristics | Expected Pipeline Behavior |
| :--- | :--- | :--- |
| `valid_clean_certificate.png` | Resolution $1920 \times 1080$, white background, clear black typography, genuine date & marks. | Passes all consistency checks; $S_{\text{risk}} < 20.0$ (LOW). |
| `tampered_grades_certificate.png` | Grade field "7.5" has been inpainted with "9.8" using mismatched font and different local JPEG quality ($Q=60$). | Flagged by ELA and Font Anomaly; $S_{\text{risk}} > 75.0$ (HIGH). |
| `copy_move_certificate.png` | Digit "8" duplicated across marks columns via patch paste. | Flagged by ORB cluster matching; $S_{\text{risk}} > 80.0$ (HIGH). |
| `skewed_30deg_photo.jpg` | Clean certificate rotated by $+15.0^{\circ}$ and slightly noisy. | Deskew module corrects angle to $\pm 1.0^{\circ}$; OCR successfully extracts text. |
| `sample_two_page.pdf` | Valid 2-page PDF document. | Rasterizer generates 2 frame images; processes page 1. |
| `corrupted_zero_byte.png` | Empty 0-byte file. | Rejected during Ingestion validation with `400 Bad Request`. |

---

## 4. Institutional Database Seed Data

### 4.1 Mock Institutions Table (`seed_institutions.json`)
```json
[
  {
    "institution_id": "inst-001-apex-univ",
    "name": "Apex University of Technology",
    "code": "AUT",
    "domain": "apexuniv.edu",
    "active": true
  },
  {
    "institution_id": "inst-002-national-inst",
    "name": "National Institute of Science & Humanities",
    "code": "NISH",
    "domain": "nish.edu",
    "active": true
  }
]
```

### 4.2 Mock Student Records (`mock_students.csv`)
```csv
register_number,student_name,institution_code,course,cgpa,passing_year,certificate_number
AUT2020CS101,Aarav Sharma,AUT,Bachelor of Technology in Computer Science,8.65,2024,CERT-AUT-2024-8901
AUT2020EC142,Priya Patel,AUT,Bachelor of Technology in Electronics,9.12,2024,CERT-AUT-2024-8902
NISH2021BBA05,Rohan Mehta,NISH,Bachelor of Business Administration,7.80,2024,CERT-NISH-2024-1142
```

---

## 5. Test Assertion Tolerances & Performance Thresholds

When running the automated test suite (`pytest tests/ -v`), the code must satisfy these quantitative pass criteria:

1. **Deskew Accuracy:** Deskew module must detect and correct skew angles between $-45^{\circ}$ and $+45^{\circ}$ within a tolerance of $\pm 2.0^{\circ}$.
2. **OCR Token Accuracy:** Clean fixture OCR character accuracy must be $\ge 92\%$.
3. **Execution Latency:**
   - Single-image preprocessing: $< 1.5\text{ seconds}$ on standard CPU.
   - Forensic analysis (ELA + Copy-Move): $< 3.5\text{ seconds}$ on standard CPU.
   - Full synchronous verification pipeline (CPU): $< 8.0\text{ seconds}$.
4. **Test Coverage:** All core pipeline modules (`src/pipeline/*`) must maintain $\ge 85\%$ line coverage.
