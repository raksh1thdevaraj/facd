# Design Documents
## AI-Based Detection of Fake or Manipulated Academic Certificates

**Version:** 1.0
**Date:** September 15, 2026
**Status:** Draft

This document consolidates the System Architecture Document, High-Level Design (HLD), Low-Level Design (LLD), Data Flow Diagrams (DFD Level 0/1/2), ER Diagram & Database Schema, and UML Diagrams (Use Case, Sequence, Activity) for the project, building on the PRD and SRD.

---

# Part A: System Architecture Document

## A.1 Purpose
Describes the overall structure of the system, its major components, how they interact, and the technology choices behind each layer.

## A.2 Architectural Style
The system follows a **layered, service-oriented architecture** with an asynchronous processing pipeline for compute-heavy ML/CV tasks, so the UI remains responsive while analysis runs in the background.

## A.3 Component Overview

| Layer | Component | Responsibility |
|---|---|---|
| Presentation | Web UI | Upload, review, results, template management, admin dashboard |
| API | Backend API (REST) | Auth, request validation, job orchestration, response formatting |
| Processing | Preprocessing Service | Resize, denoise, contrast, normalize, perspective-correct |
| Processing | OCR Service | Field extraction + confidence scoring |
| Processing | Text-Consistency Service | Rule-based validation of extracted fields |
| Processing | Forensics Service | Tamper/manipulation detection on image |
| Processing | Template/Record Matching Service | Optional comparison against institutional data |
| Processing | ML/DL Classifier Service | Learned authenticity classification |
| Processing | Score Fusion & Report Service | Combines all signals into final score + report |
| Data | Database | Users, roles, history, templates, records, audit logs |
| Data | Object Storage | Uploaded files, generated reports, model artifacts |
| Cross-cutting | Job Queue / Orchestrator | Manages async pipeline execution per document |
| Cross-cutting | Auth & RBAC | Role-based access (Admin / Institution / Verifier) |

## A.4 Suggested Technology Stack

| Layer | Suggested Technology |
|---|---|
| Frontend | React / Next.js |
| Backend API | Python (FastAPI) or Node.js (Express) |
| OCR | Tesseract OCR / EasyOCR / cloud OCR API |
| CV / Forensics | OpenCV, PIL, scikit-image |
| ML/DL | PyTorch or TensorFlow (CNN-based classifier) |
| Job Queue | Celery + Redis, or a simple async task queue |
| Database | PostgreSQL |
| File/Object Storage | Local/cloud object storage (e.g., S3-compatible) |
| Deployment | Docker containers; optional GPU-enabled inference node |

## A.5 Architecture Diagram (Deployment View)

```
                        ┌───────────────────────────┐
                        │        Client Browser       │
                        └──────────────┬──────────────┘
                                       │ HTTPS
                        ┌──────────────▼──────────────┐
                        │        Web UI (React)        │
                        └──────────────┬──────────────┘
                                       │ REST/JSON
                        ┌──────────────▼──────────────┐
                        │     Backend API (FastAPI)     │
                        │  Auth │ Validation │ Routing  │
                        └───┬───────────┬───────────┬──┘
                            │           │           │
                 ┌──────────▼──┐ ┌──────▼─────┐ ┌───▼────────┐
                 │  Job Queue   │ │ PostgreSQL │ │  Object     │
                 │ (Celery/Redis)│ │  Database │ │  Storage    │
                 └──────┬───────┘ └────────────┘ └─────────────┘
                        │
        ┌───────────────▼────────────────────────────────┐
        │             Processing Workers (Async)            │
        │  Preprocess → OCR → Text-Checks → Forensics       │
        │       → Template Match → ML Classifier             │
        │       → Score Fusion → Report Generator            │
        └─────────────────────────────────────────────────┘
```

---

# Part B: High-Level Design (HLD)

## B.1 Module Breakdown

### B.1.1 Ingestion Module
- Accepts uploaded files, validates type/size, stores raw file, creates a job record, pushes job to queue.

### B.1.2 Preprocessing Module
- Reads raw image/PDF, rasterizes PDF pages, applies resize/denoise/contrast/normalize/perspective-correction, outputs a cleaned image for downstream modules.

### B.1.3 OCR Module
- Runs text detection + recognition on the cleaned image.
- Maps recognized text regions to expected certificate fields (name, register number, course, marks, dates, certificate number) using layout heuristics or a trained field-tagging model.
- Outputs structured JSON with field values + confidence scores.

### B.1.4 Text-Consistency Module
- Applies rule-based checks (date logic, grade-format validation, known-institution name matching, certificate-number pattern checks).
- Outputs a list of consistency flags with severity.

### B.1.5 Forensics Module
- Runs copy-paste/clone detection, font/spacing anomaly detection, compression-artifact analysis (ELA-style), layout-alignment check, seal/signature-region analysis.
- Outputs a list of flagged regions (with bounding boxes) and forensic sub-scores.

### B.1.6 Template/Record Matching Module
- If a template is registered for the detected institution, aligns the certificate to the template and computes a structural-similarity score.
- If institutional records are available, checks extracted fields (name, register number, marks) against the stored record.
- Outputs match/mismatch status; module is skipped gracefully if no template/record exists.

### B.1.7 ML/DL Classification Module
- Takes engineered features (from OCR + forensics + template modules) and/or raw image embeddings.
- Runs a trained classifier (e.g., CNN over image patches + a tabular model over extracted features, or a combined multimodal model).
- Outputs a manipulation-probability score.

### B.1.8 Score Fusion & Report Module
- Combines text-consistency flags, forensic sub-scores, template/record match status, and ML classification probability into one weighted authenticity/risk score.
- Maps score to a risk band (Low / Medium / High).
- Generates a report: overall score, per-module findings, highlighted image regions, downloadable PDF.

### B.1.9 User & Access Management Module
- Handles authentication, role-based permissions, verification history, audit logging, and admin analytics.

## B.2 Module Interaction Flow

```
Upload → Ingestion → Preprocessing → OCR ─┬─→ Text-Consistency ─┐
                                            ├─→ Forensics ────────┼─→ Score Fusion → Report
                                            └─→ Template/Record ─┘        ↑
                                                                  ML Classifier
```

---

# Part C: Low-Level Design (LLD)

## C.1 OCR Module — Key Functions

| Function | Description |
|---|---|
| `preprocess_image(image)` | Returns cleaned image (denoise, contrast, deskew) |
| `run_ocr(image)` | Returns raw OCR tokens with bounding boxes and confidence |
| `map_fields(tokens, layout_hints)` | Maps raw tokens to structured fields (name, marks, date, etc.) |
| `get_field_confidence(field)` | Returns confidence score for a given field |
| `flag_low_confidence_fields(fields, threshold)` | Returns list of fields needing manual review |

## C.2 Forensics Module — Key Functions

| Function | Description |
|---|---|
| `detect_clone_regions(image)` | Returns bounding boxes of duplicated/copy-pasted regions |
| `check_font_consistency(text_regions)` | Flags font/spacing anomalies across fields |
| `run_error_level_analysis(image)` | Returns compression-artifact heatmap |
| `check_layout_alignment(image, expected_layout)` | Returns alignment deviation score |
| `analyze_signature_seal_region(image, region)` | Returns irregularity score for seal/signature |
| `compute_forensic_score(all_signals)` | Aggregates forensic sub-scores into one forensic score |

## C.3 Template/Record Matching Module — Key Functions

| Function | Description |
|---|---|
| `identify_institution(fields)` | Attempts to match certificate to a known institution |
| `load_template(institution_id)` | Loads registered template, if available |
| `align_to_template(image, template)` | Computes structural similarity / alignment score |
| `verify_against_record(fields, institution_id)` | Checks fields against stored institutional record |

## C.4 ML/DL Classifier Module — Key Functions

| Function | Description |
|---|---|
| `extract_features(ocr_output, forensic_output, template_output)` | Builds the feature vector/tensor for the model |
| `load_model(version)` | Loads the trained classifier (with version tag for audit) |
| `predict(features)` | Returns manipulation probability |
| `explain_prediction(features, prediction)` | Returns top contributing factors (e.g., via feature importance / Grad-CAM for image regions) |

## C.5 Score Fusion Module — Key Functions

| Function | Description |
|---|---|
| `fuse_scores(text_flags, forensic_score, template_status, ml_probability)` | Computes weighted final score |
| `map_to_risk_band(score)` | Converts numeric score to Low/Medium/High |
| `generate_report(job_id, all_outputs)` | Compiles the full report object |
| `export_report_pdf(report)` | Renders report as downloadable PDF |

## C.6 Class Diagram (Simplified, Textual)

```
Certificate
 ├─ id, file_path, upload_date, uploaded_by, status
 ├─ + preprocess()
 └─ + getExtractedFields()

OCRResult
 ├─ certificate_id, field_name, value, confidence

ForensicResult
 ├─ certificate_id, check_type, flagged_region, score

TemplateMatchResult
 ├─ certificate_id, institution_id, match_score, status

MLPrediction
 ├─ certificate_id, model_version, probability, top_factors

VerificationReport
 ├─ certificate_id, final_score, risk_band, findings[], pdf_path
 └─ + export()

User
 ├─ id, name, role, institution_id

Institution
 ├─ id, name, template_ref, records_ref
```

---

# Part D: Data Flow Diagrams (DFD)

## D.1 DFD Level 0 (Context Diagram)

```
                 ┌───────────┐
   Certificate → │           │ → Verification Report
   Upload        │   AI      │
                 │Certificate│
   Template/     │Verification│ → Analytics/Audit Log
   Records    →  │  System   │
                 └───────────┘
        ▲                          │
        │                          ▼
     Verifier /              Institution Admin /
   Institution Admin              System Admin
```

## D.2 DFD Level 1

```
[User] --(1) Upload Certificate--> [1.0 Ingestion & Validation]
                                        │
                                        ▼
                              [2.0 Preprocessing]
                                        │
                                        ▼
                              [3.0 OCR Extraction] --stores--> (D1: Extracted Fields)
                                        │
                     ┌──────────────────┼───────────────────┐
                     ▼                  ▼                   ▼
        [4.0 Text-Consistency]  [5.0 Forensics]   [6.0 Template/Record Match]
                     │                  │                   │
                     └──────────┬───────┴─────────┬─────────┘
                                ▼                  ▼
                        [7.0 ML Classification] --uses--> (D2: Trained Model)
                                │
                                ▼
                     [8.0 Score Fusion & Report]
                                │
                                ▼
                   (D3: Verification History) → [User: View/Export Report]
```

## D.3 DFD Level 2 — Expansion of "7.0 ML Classification"

```
[Extracted Fields (D1)] ──┐
[Forensic Signals] ───────┼──> [7.1 Feature Engineering] ──> (D4: Feature Vector)
[Template Match Status] ──┘                                        │
                                                                     ▼
                                                        [7.2 Load Model (D2)]
                                                                     │
                                                                     ▼
                                                          [7.3 Run Inference]
                                                                     │
                                                                     ▼
                                                   [7.4 Generate Explanation]
                                                                     │
                                                                     ▼
                                                         → 8.0 Score Fusion
```

---

# Part E: ER Diagram & Database Schema

## E.1 Entity-Relationship Diagram (Textual)

```
User (1) ──── belongs to ──── (1) Institution
  │
  │ (1:N) uploads
  ▼
Certificate (1) ──── (1:1) ──── PreprocessedImage
  │
  ├── (1:N) → OCRField
  ├── (1:N) → ForensicFinding
  ├── (0:1) → TemplateMatchResult
  ├── (1:1) → MLPrediction
  └── (1:1) → VerificationReport

Institution (1) ──── (0:N) → InstitutionTemplate
Institution (1) ──── (0:N) → InstitutionRecord
```

## E.2 Database Schema (Simplified DDL-style)

```sql
-- Users & Institutions
CREATE TABLE institution (
    institution_id   SERIAL PRIMARY KEY,
    name              VARCHAR(255) NOT NULL,
    created_at        TIMESTAMP DEFAULT now()
);

CREATE TABLE app_user (
    user_id           SERIAL PRIMARY KEY,
    name              VARCHAR(255),
    email             VARCHAR(255) UNIQUE NOT NULL,
    role              VARCHAR(50) CHECK (role IN ('admin','institution_admin','verifier')),
    institution_id    INT REFERENCES institution(institution_id),
    created_at        TIMESTAMP DEFAULT now()
);

-- Certificates & Processing
CREATE TABLE certificate (
    certificate_id    SERIAL PRIMARY KEY,
    uploaded_by       INT REFERENCES app_user(user_id),
    file_path         TEXT NOT NULL,
    upload_date       TIMESTAMP DEFAULT now(),
    status            VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE ocr_field (
    ocr_field_id      SERIAL PRIMARY KEY,
    certificate_id    INT REFERENCES certificate(certificate_id),
    field_name        VARCHAR(100),
    field_value       TEXT,
    confidence        FLOAT
);

CREATE TABLE forensic_finding (
    finding_id        SERIAL PRIMARY KEY,
    certificate_id    INT REFERENCES certificate(certificate_id),
    check_type        VARCHAR(100),
    region_bbox       JSON,
    score             FLOAT
);

CREATE TABLE template_match_result (
    match_id          SERIAL PRIMARY KEY,
    certificate_id    INT REFERENCES certificate(certificate_id),
    institution_id    INT REFERENCES institution(institution_id),
    match_score       FLOAT,
    status            VARCHAR(50)
);

CREATE TABLE ml_prediction (
    prediction_id     SERIAL PRIMARY KEY,
    certificate_id    INT REFERENCES certificate(certificate_id),
    model_version     VARCHAR(50),
    probability       FLOAT,
    top_factors       JSON
);

CREATE TABLE verification_report (
    report_id         SERIAL PRIMARY KEY,
    certificate_id    INT REFERENCES certificate(certificate_id),
    final_score       FLOAT,
    risk_band         VARCHAR(20),
    findings_summary  JSON,
    pdf_path          TEXT,
    generated_at      TIMESTAMP DEFAULT now()
);

-- Institutional Reference Data
CREATE TABLE institution_template (
    template_id       SERIAL PRIMARY KEY,
    institution_id    INT REFERENCES institution(institution_id),
    template_file     TEXT,
    uploaded_at       TIMESTAMP DEFAULT now()
);

CREATE TABLE institution_record (
    record_id         SERIAL PRIMARY KEY,
    institution_id    INT REFERENCES institution(institution_id),
    register_number   VARCHAR(100),
    student_name      VARCHAR(255),
    course             VARCHAR(255),
    marks              VARCHAR(100),
    issue_date         DATE
);

CREATE TABLE audit_log (
    log_id            SERIAL PRIMARY KEY,
    user_id           INT REFERENCES app_user(user_id),
    action            VARCHAR(255),
    certificate_id    INT REFERENCES certificate(certificate_id),
    timestamp         TIMESTAMP DEFAULT now()
);
```

---

# Part F: UML Diagrams

## F.1 Use Case Diagram (Textual)

```
                     ┌───────────────────────────────────┐
                     │      AI Certificate Verification     │
                     │              System                  │
                     │                                       │
   Verifier ───────► │ • Upload Certificate                 │
                     │ • Correct OCR Fields                 │
                     │ • View Verification Report           │
                     │ • Export Report (PDF)                │
                     │                                       │
Institution Admin ─► │ • Register Template                  │
                     │ • Upload Institutional Records        │
                     │ • View Institution Verification Log   │
                     │                                       │
   System Admin ───► │ • Manage Users & Roles                │
                     │ • View Analytics Dashboard            │
                     │ • Manage/Update ML Model               │
                     └───────────────────────────────────┘
```

## F.2 Sequence Diagram — "Upload & Verify Certificate"

```
Verifier      WebUI        API          Queue        Workers        DB
   │            │            │             │              │           │
   │ Upload File│            │             │              │           │
   ├───────────►│            │             │              │           │
   │            │ POST /verify            │              │           │
   │            ├───────────►│             │              │           │
   │            │            │ Save file + create job      │           │
   │            │            ├──────────────────────────────────────►│
   │            │            │ Enqueue job │              │           │
   │            │            ├────────────►│              │           │
   │            │  job_id    │             │              │           │
   │◄───────────┤◄───────────┤             │              │           │
   │            │            │             │ Dequeue job  │           │
   │            │            │             ├─────────────►│           │
   │            │            │             │  Preprocess → OCR →      │
   │            │            │             │  Forensics → ML →        │
   │            │            │             │  Fuse → Report            │
   │            │            │             │              ├──────────►│
   │  Poll status/result     │             │              │           │
   ├───────────►│───────────►│◄──────────────────────────────────────┤
   │            │  Report    │             │              │           │
   │◄───────────┤◄───────────┤             │              │           │
```

## F.3 Activity Diagram — "Certificate Processing Pipeline"

```
        [Start]
           │
           ▼
   Upload Certificate
           │
           ▼
   Validate File Type/Size ──(invalid)──► Show Error ──► [End]
           │ (valid)
           ▼
    Preprocess Image
           │
           ▼
      Run OCR Extraction
           │
           ▼
  Confidence below threshold? ──(yes)──► Prompt Manual Correction
           │ (no)                                   │
           ▼◄──────────────────────────────────────┘
   Run Text-Consistency Checks
           │
           ▼
   Run Forensic Analysis
           │
           ▼
  Template/Record Available? ──(yes)──► Run Template/Record Match
           │ (no)                                   │
           ▼◄──────────────────────────────────────┘
   Run ML/DL Classification
           │
           ▼
     Fuse All Scores
           │
           ▼
  Generate Report + Highlight Flags
           │
           ▼
   Store in History / Notify User
           │
           ▼
         [End]
```

---

## G. Traceability Note
Each design element in this document maps back to the functional requirements defined in the SRD (e.g., the OCR Module implements FR-OCR-01 to FR-OCR-04; the Forensics Module implements FR-FOR-01 to FR-FOR-05). This mapping should be carried into the Requirement Traceability Matrix (RTM) and later into the Test Plan/Test Cases document.
