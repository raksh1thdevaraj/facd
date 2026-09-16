# Software Requirements Document (SRD / SRS)
## AI-Based Detection of Fake or Manipulated Academic Certificates

**Version:** 1.0
**Date:** September 15, 2026
**Status:** Draft

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for the AI-Based Academic Certificate Authenticity Assessment System. It defines the functional and non-functional requirements, system architecture, data requirements, interface specifications, and constraints needed to design, build, and evaluate the system.

### 1.2 Scope
The system accepts certificate images/PDFs, preprocesses them, extracts textual data via OCR, performs consistency and image-forensic analysis, applies a trained ML/DL classification model, and produces an authenticity/risk score with an interpretable report. A web-based interface is provided for upload and results viewing.

### 1.3 Intended Audience
Software developers, ML engineers, project evaluators/guides, and QA testers involved in building and assessing the system.

### 1.4 Definitions & Abbreviations
- **OCR** — Optical Character Recognition
- **ML** — Machine Learning
- **DL** — Deep Learning
- **CV** — Computer Vision
- **PRD** — Product Requirements Document
- **API** — Application Programming Interface
- **UI** — User Interface
- **Confusion Matrix** — Table used to evaluate classification model performance

---

## 2. Overall Description

### 2.1 System Perspective
The system is a standalone web application composed of a frontend upload/results UI, a backend API layer, and an ML/CV processing pipeline. It may optionally interface with institution-provided template/record datasets for comparison.

### 2.2 System Functions (Summary)
1. Document upload and validation
2. Image preprocessing
3. OCR-based text extraction
4. Text consistency analysis
5. Image forensic/tamper analysis
6. Template/record comparison (optional, when data available)
7. ML/DL-based classification
8. Score fusion and risk assessment
9. Report generation and visualization
10. User/role management and history storage

### 2.3 User Classes
- **Verifier/Reviewer** — uploads certificates, views reports
- **Institution Admin/Registrar** — manages templates/records for their institution
- **System Admin** — manages users, monitors system, views analytics

### 2.4 Operating Environment
- Web-based system accessible via modern browsers (Chrome, Firefox, Edge, Safari).
- Backend services deployable on a cloud or on-premise server supporting Python-based ML frameworks.
- Should support both CPU and GPU inference (GPU preferred for DL models).

### 2.5 Design & Implementation Constraints
- OCR and CV components depend on the quality of input scans/photos.
- Model performance constrained by availability of a labeled/synthetic dataset of genuine and manipulated certificates.
- Initial version targets a defined certificate format/structure rather than fully unconstrained global formats.

### 2.6 Assumptions & Dependencies
- Availability of open-source OCR (e.g., Tesseract) and CV/ML libraries (e.g., OpenCV, PyTorch/TensorFlow).
- Availability of a dataset (real + synthetically manipulated) for training and evaluation.
- Institutional templates/records, where used, are supplied and maintained by the institution.

---

## 3. Functional Requirements (Detailed, IDs for Traceability)

### 3.1 Module: Document Ingestion
| ID | Requirement |
|---|---|
| FR-ING-01 | The system shall accept certificate files in JPG, PNG, and PDF formats. |
| FR-ING-02 | The system shall validate uploaded files for size limits and supported formats. |
| FR-ING-03 | The system shall reject and report errors for corrupted or unsupported files. |
| FR-ING-04 | The system shall support batch upload of multiple certificates in a single session. |

### 3.2 Module: Preprocessing
| ID | Requirement |
|---|---|
| FR-PRE-01 | The system shall resize input images to a standard resolution for downstream processing. |
| FR-PRE-02 | The system shall apply noise reduction to improve OCR/CV accuracy. |
| FR-PRE-03 | The system shall apply contrast enhancement and normalization. |
| FR-PRE-04 | The system shall apply perspective/skew correction for angled scans/photos. |
| FR-PRE-05 | The system shall convert PDF input into processable image frames (page rasterization). |

### 3.3 Module: OCR / Information Extraction
| ID | Requirement |
|---|---|
| FR-OCR-01 | The system shall extract student name, register/roll number, course/program name, marks/grades, dates, and certificate/serial number from the certificate. |
| FR-OCR-02 | The system shall assign a confidence score to each extracted field. |
| FR-OCR-03 | The system shall allow manual correction of low-confidence OCR fields via the UI. |
| FR-OCR-04 | The system shall support extraction from both printed and (where feasible) semi-structured handwritten fields. |

### 3.4 Module: Text Consistency Analysis
| ID | Requirement |
|---|---|
| FR-TXT-01 | The system shall validate date fields for logical consistency (e.g., issue date not before enrollment date). |
| FR-TXT-02 | The system shall validate grade/marks formats against expected grading schemes. |
| FR-TXT-03 | The system shall flag mismatches between extracted institution name and known/registered institution names. |
| FR-TXT-04 | The system shall detect anomalies in certificate/serial number formatting patterns. |

### 3.5 Module: Image Forensics / Tamper Detection
| ID | Requirement |
|---|---|
| FR-FOR-01 | The system shall detect copy-paste/cloned regions within the certificate image. |
| FR-FOR-02 | The system shall detect font and spacing inconsistencies within text fields. |
| FR-FOR-03 | The system shall detect compression-artifact irregularities indicative of local edits (e.g., Error Level Analysis-style checks). |
| FR-FOR-04 | The system shall detect layout misalignment relative to expected certificate structure. |
| FR-FOR-05 | The system shall analyze seal, stamp, and signature regions for irregularities. |

### 3.6 Module: Template & Record Comparison
| ID | Requirement |
|---|---|
| FR-TPL-01 | The system shall allow registered institutions to upload trusted certificate templates. |
| FR-TPL-02 | The system shall compare an uploaded certificate's layout against the matching registered template, when available. |
| FR-TPL-03 | The system shall verify extracted data fields against stored institutional records, when available, and report match/mismatch status. |
| FR-TPL-04 | The system shall proceed with general forensic/ML analysis when no template/record match is available. |

### 3.7 Module: ML/DL Classification
| ID | Requirement |
|---|---|
| FR-ML-01 | The system shall use a trained ML/DL model to classify certificate samples based on learned visual and textual features. |
| FR-ML-02 | The model shall output a probability/confidence score indicating likelihood of manipulation. |
| FR-ML-03 | The system shall support periodic retraining/updating of the model as new labeled data becomes available. |
| FR-ML-04 | The system shall log model version used for each assessment (for traceability/audit). |

### 3.8 Module: Score Fusion & Reporting
| ID | Requirement |
|---|---|
| FR-SCR-01 | The system shall combine text-consistency, forensic, template-comparison, and ML classification outputs into a single authenticity/risk score. |
| FR-SCR-02 | The system shall express the result as a risk score/band (e.g., numeric score and Low/Medium/High category) rather than a binary genuine/fake verdict. |
| FR-SCR-03 | The system shall generate a report listing flagged fields/regions and the specific factors contributing to the score. |
| FR-SCR-04 | The system shall visually highlight suspicious regions on the certificate image in the report. |
| FR-SCR-05 | The system shall allow the report to be exported as a downloadable PDF. |

### 3.9 Module: User & Access Management
| ID | Requirement |
|---|---|
| FR-USR-01 | The system shall support role-based access control (Admin, Institution/Registrar, Verifier). |
| FR-USR-02 | The system shall maintain a history of past verifications per user/organization. |
| FR-USR-03 | The system shall provide an admin dashboard with usage analytics (volume processed, flag rates, etc.). |
| FR-USR-04 | The system shall maintain an audit log of uploads, analyses, and report generations. |

---

## 4. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | Single-certificate end-to-end analysis shall complete within an acceptable target latency (e.g., ≤ 30 seconds under normal load). |
| NFR-02 | Scalability | The system shall support batch analysis of at least 100 documents per job without failure. |
| NFR-03 | Reliability | The system shall handle malformed/low-quality inputs gracefully without crashing, returning a clear error/low-confidence result instead. |
| NFR-04 | Security | Uploaded documents and extracted personal data shall be encrypted in transit (TLS) and at rest. |
| NFR-05 | Privacy | The system shall implement a defined data retention policy and support data deletion requests. |
| NFR-06 | Usability | The web UI shall be usable by non-technical staff without dedicated training. |
| NFR-07 | Explainability | Every generated risk score shall be accompanied by human-readable justification of contributing factors. |
| NFR-08 | Maintainability | The ML pipeline shall be modular, allowing individual components (OCR, forensics, classifier) to be updated independently. |
| NFR-09 | Portability | The web application shall function correctly across major modern browsers without platform-specific plugins. |
| NFR-10 | Auditability | All verification actions shall be logged with timestamp, user, and model version for traceability. |

---

## 5. System Architecture (High-Level)

```
┌─────────────────────┐
│   Web UI (Frontend)  │  Upload, view results, manage templates
└──────────┬───────────┘
           │ REST API
┌──────────▼───────────┐
│   Backend API Layer   │  Auth, request routing, orchestration
└──────────┬───────────┘
           │
┌──────────▼─────────────────────────────────────────────┐
│                Processing Pipeline (Async Jobs)          │
│  ┌───────────┐  ┌────────┐  ┌───────────┐  ┌──────────┐ │
│  │Preprocess │→ │  OCR   │→ │ Text/Cons.│  │ Forensics│ │
│  │  Module   │  │ Module │  │  Checks   │  │  Module  │ │
│  └───────────┘  └────────┘  └───────────┘  └──────────┘ │
│                         │            │                    │
│                         ▼            ▼                    │
│                 ┌──────────────────────┐                  │
│                 │ Template/Record Match │ (optional)       │
│                 └───────────┬──────────┘                  │
│                              ▼                             │
│                    ┌──────────────────┐                    │
│                    │ ML/DL Classifier │                    │
│                    └────────┬─────────┘                    │
│                              ▼                             │
│                    ┌──────────────────┐                    │
│                    │  Score Fusion &  │                    │
│                    │  Report Generator│                    │
│                    └──────────────────┘                    │
└───────────────────────────┬──────────────────────────────┘
                              ▼
                  ┌───────────────────────┐
                  │ Database / File Store │  History, templates, logs
                  └───────────────────────┘
```

---

## 6. Data Requirements

### 6.1 Input Data
- Certificate images (JPG/PNG) or PDFs.
- Optional: institutional templates (image/structured format) and institutional record datasets (e.g., CSV/DB of valid student-certificate records).

### 6.2 Training/Evaluation Data
- Genuine certificate samples.
- Synthetically manipulated certificate samples (e.g., altered names, grades, dates, certificate numbers, signatures) generated for controlled training/testing.
- Labeled ground truth (genuine vs. manipulated, and manipulation type where applicable).

### 6.3 Output Data
- Extracted structured fields with confidence scores.
- Authenticity/risk score and category.
- Flagged regions (bounding boxes/coordinates on the image).
- Exportable PDF report.
- Verification history records.

### 6.4 Data Storage
- Relational/NoSQL database for user accounts, verification history, and metadata.
- Object storage for uploaded certificate files and generated reports.
- Secure storage for institutional templates/records with access restricted to the owning institution.

---

## 7. External Interface Requirements

### 7.1 User Interfaces
- Upload screen (single/batch).
- Extracted-fields review/correction screen.
- Results/report screen with visual highlighting of flagged regions.
- Template/record management screen (for institution admins).
- Admin analytics dashboard.

### 7.2 API Interfaces
- REST endpoints for: file upload, job status polling, result retrieval, template/record CRUD, user/role management, report export.

### 7.3 Hardware Interfaces
- None beyond standard client devices (desktop/laptop with browser) and server-side compute (CPU/GPU) for model inference.

---

## 8. Use Case Summary

| Use Case | Primary Actor | Description |
|---|---|---|
| UC-1: Upload & Verify Single Certificate | Verifier | Upload one certificate, receive risk score and report |
| UC-2: Batch Verify Certificates | Verifier | Upload multiple certificates, receive consolidated results |
| UC-3: Correct OCR Fields | Verifier | Manually correct low-confidence extracted fields before final analysis |
| UC-4: Register Institution Template | Institution Admin | Upload official template/records for comparison |
| UC-5: Export Report | Verifier | Download PDF verification report |
| UC-6: View Analytics | System Admin | View system-wide usage and flag-rate statistics |
| UC-7: Retrain/Update Model | ML Engineer (internal) | Update classifier with new labeled data |

---

## 9. Evaluation Plan

- **Dataset split:** Training / validation / test sets of genuine and synthetically manipulated certificates.
- **Metrics:** Accuracy, Precision, Recall, F1-score, Confusion Matrix.
- **Additional analysis:** Per-manipulation-type detection rate (e.g., separately evaluate detection of altered grades vs. altered signatures vs. altered dates).
- **Baseline comparison:** Compare fused pipeline score against individual sub-modules (OCR-only consistency checks vs. forensic-only vs. ML-only) to justify the multi-signal fusion approach.

---

## 10. Constraints & Limitations

- Detection accuracy is bounded by the realism and diversity of the synthetic manipulation dataset used for training.
- The system provides a risk assessment, not a legal determination of authenticity.
- Performance may degrade on certificate formats significantly different from those represented in the training data.
- Requires reasonably legible scans/photos; extremely poor-quality inputs may yield low-confidence results across all modules.

---

## 11. Appendix

### 11.1 Traceability Note
Each functional requirement ID (e.g., FR-OCR-01) should be mapped to corresponding test cases during the QA/evaluation phase to ensure full requirement coverage.

### 11.2 Related Document
See the accompanying **Product Requirements Document (PRD)** for user personas, business goals, scope boundaries, and success metrics that inform these software requirements.
