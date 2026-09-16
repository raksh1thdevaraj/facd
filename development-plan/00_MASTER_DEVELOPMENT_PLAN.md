# Master Development Plan

## AI-Based Detection of Fake or Manipulated Academic Certificates

**Version:** 1.0
**Date:** September 15, 2026
**Status:** Implementation-Ready

---

## 1. Project Overview

This project builds a web-based AI-assisted academic certificate authenticity assessment system. A user (admissions officer, recruiter, registrar, or admin) uploads a certificate image or PDF through a React frontend. The file is sent to a FastAPI backend, which creates an asynchronous processing job. The job passes the certificate through a multi-stage analysis pipeline:

1. **Ingestion** — validate file type/size, store the raw file, create a job record.
2. **Preprocessing** — rasterize PDFs, resize, denoise, enhance contrast, correct skew/perspective, normalize.
3. **OCR** — extract text with bounding boxes and confidence scores, map tokens to structured fields (name, marks, dates, certificate number, etc.).
4. **Text Consistency** — apply rule-based checks on extracted fields (date logic, grade format, institution name, cert-number pattern).
5. **Image Forensics** — detect copy-paste cloning, font/spacing anomalies, compression artifacts (ELA-style), layout misalignment, seal/signature irregularities.
6. **Template/Record Matching** — if an institutional template or student record is registered, compare layout similarity and verify field values.
7. **ML/DL Classification** — run a trained model (tabular baseline, then optionally a CNN visual branch, then optionally a fused multimodal model) to produce a manipulation probability.
8. **Score Fusion** — combine all module outputs into a single weighted risk score mapped to a risk band (Low / Medium / High).
9. **Explainability** — generate human-readable explanations: feature importance (SHAP for tabular), Grad-CAM heatmaps (for CNN), contributing factors list.
10. **Report Generation** — compile findings, suspicious-region overlays, and a downloadable PDF report.

The system produces a **risk assessment**, not an absolute legal claim. Every score is accompanied by the specific signals that contributed to it, suspicious regions highlighted on the certificate image, and a disclaimer that final determination is a human responsibility.

---

## 2. Final Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Browser                           │
│                     React + Vite + TypeScript                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS / REST / JSON
┌────────────────────────────▼────────────────────────────────────┐
│                     Backend API (FastAPI)                        │
│        Auth │ Validation │ Routing │ Job Orchestration           │
└───┬────────────────┬──────────────────┬─────────────────────────┘
    │                │                  │
┌───▼──────┐  ┌──────▼───────┐  ┌──────▼──────────┐
│ Job Queue │  │  PostgreSQL  │  │  File Storage   │
│  (Redis/  │  │   Database   │  │ (Local / S3)    │
│  in-proc) │  └──────────────┘  └─────────────────┘
└─────┬─────┘
      │
┌─────▼───────────────────────────────────────────────────────────┐
│              Processing Pipeline (Async Workers)                 │
│                                                                  │
│  ┌──────────┐   ┌─────────┐   ┌────────────────┐   ┌──────────┐│
│  │Preprocess│ → │  OCR    │ → │Text-Consistency│   │Forensics ││
│  │  Module  │   │ Module  │   │    Module       │   │  Module  ││
│  └──────────┘   └────┬────┘   └───────┬────────┘   └────┬─────┘│
│                      │                │                   │      │
│                      │        ┌───────▼───────────────────▼──┐  │
│                      │        │ Template / Record Matching    │  │
│                      │        │        (optional)             │  │
│                      │        └──────────────┬───────────────┘  │
│                      │                       │                   │
│                      ▼                       ▼                   │
│               ┌────────────────────────────────┐                │
│               │     ML / DL Classifier          │                │
│               │ (Tabular → CNN → Fused)         │                │
│               └──────────────┬─────────────────┘                │
│                              ▼                                   │
│               ┌────────────────────────────────┐                │
│               │     Score Fusion                │                │
│               └──────────────┬─────────────────┘                │
│                              ▼                                   │
│               ┌────────────────────────────────┐                │
│               │  Explainability + Report Gen    │                │
│               └────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────┘
```

### Processing Flow Detail

```
Certificate Upload (JPG/PNG/PDF)
        ↓
   File Validation
        ↓
   Store Raw File + Create Job
        ↓
   Enqueue Job
        ↓
   ┌─── Preprocessing ───┐
   │ PDF rasterization    │
   │ Resize               │
   │ Denoise              │
   │ Contrast enhance     │
   │ Perspective correct  │
   │ Normalize            │
   └──────────┬───────────┘
              ↓
   ┌─── OCR ──────────────┐
   │ Text detection        │
   │ Text recognition      │
   │ Bounding boxes        │
   │ Confidence scores     │
   │ Field mapping         │
   │ (pause for correction │
   │  if low confidence)   │
   └──────────┬───────────┘
              ↓
   ┌──── Parallel Analysis ────────────────────┐
   │                                            │
   │  Text Consistency    Image Forensics       │
   │  ├ Date logic        ├ Clone detection     │
   │  ├ Grade format      ├ Font/spacing        │
   │  ├ Institution name  ├ ELA artifacts       │
   │  └ Cert number       ├ Layout alignment    │
   │                      └ Seal/signature      │
   │                                            │
   └────────────────┬──────────────────────────┘
                    ↓
   Template/Record Match (if available)
                    ↓
   ML/DL Classification
                    ↓
   Score Fusion → Risk Score + Risk Band
                    ↓
   Explainability → Contributing Factors
                    ↓
   Report Generation → PDF
                    ↓
   Store Results → Notify User
```

---

## 3. Technology Stack

### 3.1 Frontend

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **React 18** | UI framework | Component-based, large ecosystem, well-documented | Yes (MIT) | Yes |
| **Vite** | Build tool / dev server | Fast HMR, simple config, modern defaults | Yes (MIT) | Yes |
| **TypeScript** | Type-safe JavaScript | Catches errors early, better IDE support | Yes (Apache 2.0) | Yes |
| **Tailwind CSS** | Utility-first CSS | Rapid styling, consistent design, responsive | Yes (MIT) | Yes |
| **React Router** | Client-side routing | SPA navigation between upload, results, history, admin | Yes (MIT) | Yes |
| **Axios** | HTTP client | Clean API for REST calls to backend | Yes (MIT) | Yes |
| **React PDF** | PDF rendering in browser | Preview certificates in-browser | Yes (MIT) | Yes |

### 3.2 Backend

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **Python 3.11+** | Primary language | ML/CV ecosystem, FastAPI compatibility | Yes | Yes |
| **FastAPI** | Web framework | Async support, auto-docs (Swagger), Pydantic validation | Yes (MIT) | Yes |
| **Pydantic v2** | Data validation / schemas | Request/response validation, settings management | Yes (MIT) | Yes |
| **Uvicorn** | ASGI server | Production-ready async server for FastAPI | Yes (BSD) | Yes |
| **python-multipart** | File upload handling | Required by FastAPI for file uploads | Yes (Apache 2.0) | Yes |
| **python-jose / PyJWT** | JWT authentication | Stateless auth tokens | Yes (MIT) | Yes |
| **passlib + bcrypt** | Password hashing | Secure credential storage | Yes (BSD) | Yes |
| **Redis + rq** (or **Celery**) | Job queue | Async processing of analysis pipeline | Yes (BSD) | Important |
| **SQLAlchemy 2.0** | ORM | Database abstraction, migrations via Alembic | Yes (MIT) | Yes |
| **Alembic** | Database migrations | Schema versioning | Yes (MIT) | Yes |

> **Note on job queue:** For initial local development, a simple in-process background task (FastAPI `BackgroundTasks` or a basic Redis queue via `rq`) is sufficient. Celery is the stretch option for production-scale batch processing.

### 3.3 Computer Vision / Image Processing

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **OpenCV (cv2)** | Image processing | Industry-standard CV library, perspective correction, clone detection | Yes (Apache 2.0) | Yes |
| **Pillow (PIL)** | Image I/O and manipulation | Read/write/resize images, PDF rasterization helper | Yes (HPND) | Yes |
| **NumPy** | Numerical arrays | Underlying data structure for all image operations | Yes (BSD) | Yes |
| **scikit-image** | Advanced image analysis | ELA, SSIM, structural comparison, forensic utilities | Yes (BSD) | Yes |
| **pdf2image + poppler** | PDF to image conversion | Rasterize PDF pages at configurable DPI | Yes (MIT / GPL) | Yes |

### 3.4 OCR

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **PaddleOCR** | **Primary OCR engine** | High accuracy, lightweight, bounding boxes + confidence out of the box, supports structured/table detection, fully local, no API costs | Yes (Apache 2.0) | Yes |

> **Decision:** PaddleOCR is chosen as the single primary OCR engine. It provides text detection, recognition, bounding boxes, and confidence scores in a single package. EasyOCR is the fallback alternative if PaddleOCR installation causes issues on the target platform. Do NOT implement multiple OCR engines.

### 3.5 Machine Learning

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **scikit-learn** | Baseline ML models | Random Forest, Logistic Regression, evaluation metrics, feature importance | Yes (BSD) | Yes |
| **pandas** | Data manipulation | Feature engineering, dataset management | Yes (BSD) | Yes |
| **joblib** | Model serialization | Save/load trained sklearn models | Yes (BSD) | Yes |

### 3.6 Deep Learning

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **PyTorch** | DL framework | Transfer learning, CNN backbone, Grad-CAM support | Yes (BSD) | Important |
| **torchvision** | Pretrained models + transforms | EfficientNet/ResNet backbones, image augmentation | Yes (BSD) | Important |
| **SHAP** | Explainability (tabular) | Feature importance for tree/linear models | Yes (MIT) | Important |
| **pytorch-grad-cam** | Explainability (CNN) | Grad-CAM heatmaps for visual model | Yes (MIT) | Optional |

### 3.7 Database

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **PostgreSQL 15+** | Primary database | Robust, supports JSON columns, production-ready | Yes (PostgreSQL License) | Yes |
| **SQLite** | Local dev fallback | Zero-config for early development phases | Yes (Public Domain) | Optional |

> **Strategy:** Use SQLite during initial backend development (Phases 1–13) for simplicity. Switch to PostgreSQL when deploying or integrating all modules (Phase 14+). SQLAlchemy abstracts the difference.

### 3.8 PDF Generation

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **ReportLab** | PDF report generation | Create structured PDF reports with images, tables, text | Yes (BSD) | Yes |
| **WeasyPrint** | Alternative PDF gen | HTML-to-PDF (if HTML templates are preferred for reports) | Yes (BSD) | Optional (alternative to ReportLab) |

### 3.9 Testing

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **pytest** | Unit + integration testing | Standard Python test framework | Yes (MIT) | Yes |
| **httpx** | Async HTTP test client | Test FastAPI endpoints | Yes (BSD) | Yes |
| **pytest-cov** | Coverage reporting | Measure test coverage | Yes (MIT) | Yes |
| **Playwright** | E2E browser testing | Automated UI testing | Yes (Apache 2.0) | Optional |
| **Factory Boy** | Test data factories | Generate test fixtures | Yes (MIT) | Optional |

### 3.10 Development Tools

| Technology | Role | Why | Free/Open-Source | Mandatory |
|---|---|---|---|---|
| **Git** | Version control | Track all changes | Yes | Yes |
| **GitHub** | Repository hosting | Code hosting, issues | Yes (free tier) | Yes |
| **venv / virtualenv** | Python environment | Isolated dependencies | Yes | Yes |
| **`.env` + python-dotenv** | Environment config | Secrets management for local dev | Yes (BSD) | Yes |
| **Docker + docker-compose** | Containerization | Reproducible dev/deploy environment | Yes (Apache 2.0) | Optional |
| **pre-commit** | Git hooks | Linting/formatting before commit | Yes (MIT) | Optional |
| **Ruff** | Python linter/formatter | Fast, all-in-one Python linting | Yes (MIT) | Optional |

---

## 4. Database Schema Summary

The database schema follows the Design Documents (Part E). **11 tables** are defined:

| Table | Purpose | Key Relationships |
|---|---|---|
| `institution` | Registered institutions | Parent of `app_user`, `institution_template`, `institution_record` |
| `app_user` | Users with roles | Belongs to `institution`, uploads `certificate` |
| `certificate` | Uploaded certificate files | Parent of all analysis result tables |
| `ocr_field` | Extracted OCR fields per certificate | FK → `certificate` |
| `forensic_finding` | Forensic analysis results | FK → `certificate` |
| `template_match_result` | Template comparison results | FK → `certificate`, `institution` |
| `ml_prediction` | ML model predictions | FK → `certificate` |
| `verification_report` | Final reports | FK → `certificate` |
| `institution_template` | Registered certificate templates | FK → `institution` |
| `institution_record` | Stored student records for verification | FK → `institution` |
| `audit_log` | All user actions logged | FK → `app_user`, `certificate` |

> **Implementation Requirement:** The Design Docs schema will be enhanced with:
> - `password_hash` column on `app_user` (required for authentication, not in original schema but technically necessary)
> - `preprocessed_image_path` column on `certificate` (store path to preprocessed image for reuse)
> - `text_consistency_result` table (the original schema stores forensic findings but not text-consistency results as a separate table — needed to satisfy FR-TXT-01 to FR-TXT-04 traceability)
> - `job_status` and `job_error` columns on `certificate` table for async processing tracking
>
> These are labeled as **Supporting Requirements** — technically necessary additions not explicitly defined in the original schema but required for the system to function.

---

## 5. Development Phases — Dependency Graph

```
Phase 01: Project Foundation
    ↓
Phase 02: Dataset & Data Pipeline
    ↓
Phase 03: Document Ingestion
    ↓
Phase 04: Image Preprocessing
    ↓
Phase 05: OCR & Information Extraction
    ↓
Phase 06: Text Consistency Analysis
    ↓                              ↓
Phase 07: Image Forensics ←────────┘ (parallel after OCR)
    ↓
Phase 08: Template & Record Verification
    ↓
Phase 09: ML Baseline Model
    ↓
Phase 10: Deep Learning Visual Model
    ↓
Phase 11: Multimodal Model & Score Fusion
    ↓
Phase 12: Explainability & Suspicious Regions
    ↓
Phase 13: Verification Report System
    ↓
Phase 14: Database & Backend API
    ↓
Phase 15: Authentication & RBAC
    ↓
Phase 16: Frontend Application
    ↓
Phase 17: Verification History & Admin Dashboard
    ↓
Phase 18: End-to-End Integration
    ↓
Phase 19: Testing & Evaluation
    ↓
Phase 20: Deployment & Security
    ↓
Phase 21: Documentation & Final Submission
    ↓
Phase 22: Final Polish & Demo
```

### Parallelization Notes

- Phases 06 and 07 (Text Consistency and Forensics) can be developed in parallel after Phase 05 (OCR).
- Phase 16 (Frontend) can start skeleton work during Phase 14 (Backend).
- Phase 02 (Dataset) can proceed in parallel with Phase 03 (Ingestion) once Foundation is done.

---

## 6. Feature Priority Matrix

### CORE — Must be completed for a viable project

| Feature | Phase |
|---|---|
| Project setup, repo, environment | 01 |
| Dataset creation (genuine + synthetic manipulated) | 02 |
| Certificate upload (JPG/PNG/PDF) | 03 |
| PDF rasterization | 03, 04 |
| Image preprocessing pipeline | 04 |
| OCR field extraction + confidence | 05 |
| Text consistency checks | 06 |
| Basic forensics (clone, ELA, font) | 07 |
| Baseline ML model (Random Forest) | 09 |
| Score fusion | 11 |
| Verification report | 13 |
| Backend API | 14 |
| Frontend upload + results | 16 |
| Unit + integration tests | 19 |
| Evaluation (accuracy, precision, recall, F1, confusion matrix) | 19 |

### IMPORTANT — Should be completed for a strong project

| Feature | Phase |
|---|---|
| Template matching | 08 |
| Institutional record verification | 08 |
| CNN visual model | 10 |
| Multimodal fusion | 11 |
| Explainability (SHAP, feature importance) | 12 |
| Suspicious region visualization | 12 |
| PDF report export | 13 |
| Authentication / RBAC | 15 |
| Verification history | 17 |
| OCR manual correction flow | 05, 16 |
| Ablation study | 19 |

### OPTIONAL — Nice to have

| Feature | Phase |
|---|---|
| Grad-CAM heatmaps for CNN | 12 |
| Admin analytics dashboard | 17 |
| Audit logging | 15, 17 |
| Batch upload | 03 |
| Batch processing optimization | 18 |

### STRETCH — Advanced features if time permits

| Feature | Phase |
|---|---|
| Advanced multimodal neural network fusion | 11 |
| Learned fusion weights (trained fusion model) | 11 |
| Automated model retraining pipeline | 10 |
| Docker deployment | 20 |
| GPU inference optimization | 20 |
| Active learning from reviewer corrections | Future |

---

## 7. Requirement Traceability Summary

### Functional Requirements → Phase Mapping

| Requirement ID | Description | Phase(s) |
|---|---|---|
| FR-ING-01 | Accept JPG/PNG/PDF | 03 |
| FR-ING-02 | Validate file size/format | 03 |
| FR-ING-03 | Reject corrupted/unsupported files | 03 |
| FR-ING-04 | Batch upload | 03 |
| FR-PRE-01 | Resize to standard resolution | 04 |
| FR-PRE-02 | Noise reduction | 04 |
| FR-PRE-03 | Contrast enhancement + normalization | 04 |
| FR-PRE-04 | Perspective/skew correction | 04 |
| FR-PRE-05 | PDF to image rasterization | 04 |
| FR-OCR-01 | Extract structured fields | 05 |
| FR-OCR-02 | Confidence scores per field | 05 |
| FR-OCR-03 | Manual correction of low-confidence fields | 05, 16 |
| FR-OCR-04 | Support printed + semi-structured handwritten | 05 |
| FR-TXT-01 | Date consistency validation | 06 |
| FR-TXT-02 | Grade/marks format validation | 06 |
| FR-TXT-03 | Institution name mismatch detection | 06 |
| FR-TXT-04 | Certificate number pattern anomaly | 06 |
| FR-FOR-01 | Clone/copy-paste detection | 07 |
| FR-FOR-02 | Font/spacing inconsistency detection | 07 |
| FR-FOR-03 | Compression artifact detection (ELA) | 07 |
| FR-FOR-04 | Layout misalignment detection | 07 |
| FR-FOR-05 | Seal/signature irregularity analysis | 07 |
| FR-TPL-01 | Institution template upload | 08 |
| FR-TPL-02 | Template layout comparison | 08 |
| FR-TPL-03 | Record field verification | 08 |
| FR-TPL-04 | Graceful fallback when no template/record | 08 |
| FR-ML-01 | ML/DL classification model | 09, 10, 11 |
| FR-ML-02 | Probability/confidence output | 09, 10, 11 |
| FR-ML-03 | Support periodic retraining | 09, 10 |
| FR-ML-04 | Log model version per assessment | 09, 14 |
| FR-SCR-01 | Combine signals into risk score | 11 |
| FR-SCR-02 | Risk score/band output | 11 |
| FR-SCR-03 | Report with flagged fields/regions | 13 |
| FR-SCR-04 | Visual highlighting of suspicious regions | 12, 13 |
| FR-SCR-05 | PDF export | 13 |
| FR-USR-01 | Role-based access control | 15 |
| FR-USR-02 | Verification history per user/org | 17 |
| FR-USR-03 | Admin analytics dashboard | 17 |
| FR-USR-04 | Audit log | 15, 17 |

### Non-Functional Requirements → Phase Mapping

| NFR ID | Description | Phase(s) |
|---|---|---|
| NFR-01 | Single-cert latency ≤30s | 18, 19 |
| NFR-02 | Batch scalability (100 docs) | 18, 19 |
| NFR-03 | Graceful failure on bad input | 03, 04, 05, 18 |
| NFR-04 | Encryption in transit + at rest | 20 |
| NFR-05 | Data retention policy + deletion | 20 |
| NFR-06 | Usable by non-technical staff | 16, 19 |
| NFR-07 | Explainable risk scores | 12, 13 |
| NFR-08 | Modular ML pipeline | 01, 09, 10, 11 |
| NFR-09 | Cross-browser web application | 16 |
| NFR-10 | Audit logging with timestamp/user/model | 15, 17 |

---

## 8. Project Structure (Target)

```
AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/
├── docs/                              # Existing project documentation
│   ├── PRD_AI_Certificate_Verification.md
│   ├── SRD_AI_Certificate_Verification.md
│   ├── Design_Docs_AI_Certificate_Verification.md
│   ├── ML_Data_Docs_AI_Certificate_Verification.md
│   ├── Testing_Docs_AI_Certificate_Verification.md
│   └── Abstract.md
│
├── development-plan/                  # This development roadmap
│   ├── 00_MASTER_DEVELOPMENT_PLAN.md
│   ├── phase-01-project-foundation.md
│   ├── ...
│   └── phase-22-final-polish-and-demo.md
│
├── backend/                           # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Settings / env config
│   │   ├── database.py                # SQLAlchemy engine + session
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── api/                       # API routers
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── certificates.py
│   │   │   │   ├── templates.py
│   │   │   │   ├── records.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── users.py
│   │   │   │   └── admin.py
│   │   ├── services/                  # Business logic
│   │   ├── modules/                   # Analysis pipeline modules
│   │   │   ├── ingestion/
│   │   │   ├── preprocessing/
│   │   │   ├── ocr/
│   │   │   ├── text_consistency/
│   │   │   ├── forensics/
│   │   │   ├── template_matching/
│   │   │   ├── ml_classifier/
│   │   │   ├── score_fusion/
│   │   │   ├── explainability/
│   │   │   └── report_generator/
│   │   ├── core/                      # Auth, security, exceptions
│   │   └── utils/                     # Shared utilities
│   ├── tests/                         # All tests
│   ├── alembic/                       # DB migrations
│   ├── requirements.txt
│   ├── .env.example
│   └── pyproject.toml
│
├── frontend/                          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/                  # API client
│   │   ├── types/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.ts
│
├── ml/                                # ML experiment workspace
│   ├── data/                          # Dataset (gitignored)
│   ├── notebooks/                     # Exploration notebooks
│   ├── scripts/                       # Training/evaluation scripts
│   ├── models/                        # Saved model artifacts
│   └── configs/                       # Experiment configs
│
├── storage/                           # Uploaded files + generated reports (gitignored)
│
├── docker-compose.yml                 # Optional containerization
├── .gitignore
├── .env.example
└── README.md
```

---

## 9. Git Strategy

### Branch Strategy (Simple)

- `main` — stable, working code
- `dev` — active development branch
- Feature branches: `feat/phase-XX-description`

### Commit Convention

```
feat: description          # New feature
fix: description           # Bug fix
test: description          # Test additions
docs: description          # Documentation
refactor: description      # Code restructuring
chore: description         # Config, deps, tooling
```

### Commit Frequency

- At least one commit per completed chip
- At minimum, one commit per completed feature group within a phase
- Never one giant commit for an entire phase

---

## 10. Phase Summary Table

| Phase | Name | Est. Chips | Priority | Dependencies |
|---|---|---|---|---|
| 01 | Project Foundation | 15 | CORE | None |
| 02 | Dataset & Data Pipeline | 18 | CORE | 01 |
| 03 | Document Ingestion | 15 | CORE | 01 |
| 04 | Image Preprocessing | 14 | CORE | 03 |
| 05 | OCR & Information Extraction | 18 | CORE | 04 |
| 06 | Text Consistency Analysis | 14 | CORE | 05 |
| 07 | Image Forensics | 18 | CORE | 04 |
| 08 | Template & Record Verification | 14 | IMPORTANT | 05, 07 |
| 09 | ML Baseline Model | 16 | CORE | 02, 06, 07 |
| 10 | Deep Learning Visual Model | 15 | IMPORTANT | 02, 04, 09 |
| 11 | Multimodal Model & Score Fusion | 16 | CORE | 09, 10, 06, 07, 08 |
| 12 | Explainability & Suspicious Regions | 14 | IMPORTANT | 09, 10, 11 |
| 13 | Verification Report System | 14 | CORE | 11, 12 |
| 14 | Database & Backend API | 22 | CORE | 01, 03–13 |
| 15 | Authentication & RBAC | 14 | IMPORTANT | 14 |
| 16 | Frontend Application | 30 | CORE | 14, 15 |
| 17 | Verification History & Admin Dashboard | 14 | IMPORTANT | 15, 16 |
| 18 | End-to-End Integration | 12 | CORE | 01–17 |
| 19 | Testing & Evaluation | 22 | CORE | 18 |
| 20 | Deployment & Security | 12 | OPTIONAL | 18 |
| 21 | Documentation & Final Submission | 10 | CORE | 19 |
| 22 | Final Polish & Demo | 8 | CORE | 21 |

---

## 11. Risk Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Limited training data | Poor model generalization | Synthetic manipulation generation + augmentation (Phase 02) |
| False positives on genuine certificates | Trust loss | Risk scores with confidence + explanation, not binary verdicts |
| OCR errors on low-quality scans | Incorrect downstream analysis | Preprocessing pipeline + human-in-the-loop correction |
| Sophisticated forgeries evading detection | Missed detections | Multi-signal fusion (text + visual + template) |
| PaddleOCR installation issues | Blocked OCR phase | EasyOCR as documented fallback |
| Complex multimodal model fails to train | No ML results | Baseline Random Forest provides fallback results |
| PostgreSQL setup complexity | Blocked backend work | SQLite for early development, PostgreSQL for integration |

---

## 12. Disclaimer

This system produces a **risk assessment**, not a legal determination. The final report must always include:

- A disclaimer that results are advisory, not legally binding
- The model version and verification timestamp
- Known limitations of the analysis
- A recommendation for human review of flagged documents
