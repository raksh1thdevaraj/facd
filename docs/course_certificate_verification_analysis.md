# Architectural Analysis & Extension Plan: Course Certificate Authenticity Verification Module

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Target Extension:** Course & Completion Certificate Authenticity Verification Module (QR, URL, Issuer Registry, Online Record Comparison, Document Forensics & Explainable ML Risk Fusion)  
**Document Path:** `docs/course_certificate_verification_analysis.md`  
**Date:** September 21, 2026  

---

## 1. Executive Summary

This document performs an exhaustive audit of the existing codebase and designs the architecture for extending the platform with a dedicated **Course Certificate Authenticity Verification Module**. The objective is to allow users (students, recruiters, admissions officers, corporate background verifiers) to upload course, boot camp, professional training, or academic completion certificates (PDF/PNG/JPG) and automatically verify their authenticity using multi-layered physical and digital evidence:
1. **Physical Document Authenticity**: Document forensics (ELA, copy-move detection, noise variance, font/spacing analysis, seal & signature verification).
2. **Digital Verification Integrity**: Automated QR code detection, localized decoding, cryptographic/URL extraction, issuer domain validation, and sandbox online record scraping.
3. **Cross-Modal Consistency**: Field-by-field comparative matching between certificate OCR tokens and online verification records (specifically detecting **copied/transplanted valid QR codes** on tampered documents).
4. **Explainable Fusion Risk Model**: A dedicated tabular classifier producing calibrated **Authenticity** and **Fraud Risk** scores categorized into 4 explainable bands: **VERIFIED (Green)**, **SUSPICIOUS (Yellow)**, **FRAUDULENT (Red)**, and **UNVERIFIED / VERIFICATION UNAVAILABLE (Gray)**.

---

## 2. Audit of Existing System

### 2.1 Technology Stack Summary
| Layer | Existing Technology | Notes / Reusability |
|---|---|---|
| **Frontend** | React 18, Vite 5, TypeScript 5, TailwindCSS 3.4, React Router DOM 6, Lucide React, Axios | Reusable UI components (Navbar, Footer, Glass Panels, Badges, File Upload dropzone, PDF viewer). |
| **Backend API** | Python 3.11, FastAPI 0.110, Pydantic V2, Uvicorn ASGI | Standard REST routing, async execution, standardized error envelopes. |
| **Database** | SQLAlchemy 2.0 ORM, SQLite (`dev.db` for development), PostgreSQL 15 (production), Alembic | Extensible with `CourseCertificateModel` and `IssuerRegistryModel`. |
| **Security & Auth** | JWT Bearer Authentication (OAuth2 password flow), bcrypt password hashing, RBAC (ADMIN, INSTITUTION_VERIFIER, STUDENT) | Existing auth tokens directly protect and attribute course certificate jobs. |
| **Storage** | Local structured disk storage (`storage/uploads`, `storage/preprocessed`, `storage/reports`, `storage/templates`), abstractable to S3/Cloud Storage | File hashing, MIME validation, and path isolation already standard. |
| **OCR System** | EasyOCR, PyTesseract, modular token builders, field extractors (`name`, `date`, `cert_id`, `grade`, etc.) | Fully reusable for candidate, course, date, and cert ID extraction. |
| **Forensics** | Error Level Analysis (ELA), Copy-Move block matching, noise inconsistency, font size/spacing variance | Directly reusable for tamper detection and heatmap generation. |
| **ML & Score Fusion** | ResNet visual CNN, XGBoost tabular baseline, Weighted Late Fusion, Stacking Meta-Classifier | Architecture pattern reusable; dedicated course risk model will be added. |
| **Reporting** | ReportLab PDF generation, HMAC-SHA256 digital signing, QR code stamping, JSON serialization | Verification report pipeline can generate specialized course verification reports. |

### 2.2 Existing Modules & Directory Layout
```text
backend/app/
├── api/v1/endpoints/
│   ├── auth.py                  # User authentication & tokens
│   ├── certificates.py          # Academic certificate upload & verification
│   ├── institutions.py          # Registered institutions & domain mapping
│   ├── templates.py             # Master layout templates
│   ├── records.py               # Student academic record databases
│   ├── reports.py               # Verification report endpoints
│   └── health.py                # System diagnostics & health
├── models/
│   ├── certificate.py           # Core certificate job ORM model
│   ├── ocr_field.py             # Extracted OCR fields
│   ├── forensic.py              # Forensic analysis sub-scores & regions
│   ├── ml_prediction.py         # Visual & tabular prediction cache
│   └── report.py                # Verification report data & HMAC signatures
├── modules/
│   ├── ingestion/               # File validation, hashing, MIME detection
│   ├── preprocessing/           # PDF rasterization, contrast enhancement, deskewing
│   ├── ocr/                     # EasyOCR/Tesseract engine + regex field extractors
│   ├── text_consistency/        # Date ordering, grade ranges, cert ID syntax
│   ├── forensics/               # ELA, copy-move, noise, stroke/spacing analysis
│   ├── template_matching/       # ORB/SIFT alignment, SSIM, seal matcher
│   ├── ml_classifier/           # Tabular XGBoost inference
│   ├── visual_model/            # PyTorch ResNet50 visual CNN
│   ├── score_fusion/            # Late fusion & stacking meta-learner
│   ├── explainability/          # SHAP feature importance & unified overlay
│   └── report_generator/        # PDF generation, HMAC signer
└── services/
    ├── pipeline_orchestrator.py # Multi-stage sequential executor
    └── fallback_handler.py     # Graceful degradation for restricted hardware
```

---

## 3. Reusable Components & Synergies

Instead of reinventing or duplicating existing work, the Course Certificate module will leverage established infrastructure:
1. **Document Ingestion & PDF Rasterization**: Reuse `app.modules.ingestion.validator.DocumentValidator` and `app.modules.preprocessing.pdf_rasterizer.PDFRasterizer` to convert multi-page PDFs or high-resolution images into normalized RGB matrices.
2. **OCR Tokenization**: Reuse `app.modules.ocr.service.OCRService` to detect text boxes, tokens, confidence levels, and initial field candidates.
3. **Forensic Analysis**: Reuse `app.modules.forensics.service.ForensicService` for pixel-level tampering probability, ELA maps, copy-move splicing, and compression anomalies.
4. **Security & Authentication**: Reuse `app.api.v1.deps.get_current_user` for access control and `app.core.security` for HMAC-SHA256 signature verification.
5. **Database Engine**: Use existing SQLAlchemy connection pooling (`app.database.engine` and `Base`).

---

## 4. Delta Architecture: Course Certificate Module

```
Uploaded Course Certificate (PDF/PNG/JPG)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Ingestion & Preprocessing (Rasterize, Resize, Normalize)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ 2. Dual-Engine OCR & Regex    │   │ 3. Robust QR Code Detector    │
│ Candidate Name, Course Name,  │   │ Detect, Decode & Normalize    │
│ Cert ID, Issuer, Issue Date,  │   │ Verification URL & Payload    │
│ Completion Date, Expiry, Grade│   │ (OpenCV / pyzbar / qreader)   │
└───────────────┬───────────────┘   └───────────────┬───────────────┘
                │                                   │
                │     ┌─────────────────────────────┘
                │     ▼
                │ ┌─────────────────────────────────────────────────┐
                │ │ 4. Issuer Registry & Domain Security Check       │
                │ │ Match domain vs. trusted issuer registry        │
                │ │ SSRF protection, HTTPS check, safe redirect     │
                │ └─────────────────┬───────────────────────────────┘
                │                   │
                │                   ▼
                │ ┌─────────────────────────────────────────────────┐
                │ │ 5. Online Record Scraper & Comparator           │
                │ │ Fetch live verification endpoint safely         │
                │ │ Extract online candidate, course, ID, date      │
                │ └─────────────────┬───────────────────────────────┘
                │                   │
                ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Cross-Modal Field Consistency Engine                     │
│ Compare OCR Fields vs. Online Record Fields                 │
│ Detect: COPIED_QR_BUT_DATA_MISMATCH                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ 7. Document Tampering Engine  │   │ 8. Signature & Seal Analysis  │
│ Pixel Forensics (ELA, Noise,  │   │ Detect presence, alignment,   │
│ Copy-Move, Text Manipulation) │   │ and stroke consistency        │
└───────────────┬───────────────┘   └───────────────┬───────────────┘
                │                                   │
                └──────────────────┬────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Course Certificate ML Fraud-Risk Model (LightGBM/XGBoost)│
│ Features: OCR Conf, Tamper Prob, QR Valid, Domain Trust,    │
│ Name Match, ID Match, Date Match, Course Match, Sig Score   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. Explainable Decision Engine & Verification Report       │
│ Verdict: VERIFIED | SUSPICIOUS | FRAUDULENT | UNVERIFIED    │
│ Authenticity Score (0-100%) & Granular Evidence Table       │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Detailed Component Design

### 5.1 QR Code Detection & Decoding Engine (`app/modules/course_verification/qr_detector.py`)
- **Multi-pass Detection**:
  - Pass 1: Direct OpenCV `QRCodeDetector` on preprocessed image.
  - Pass 2: Adaptive thresholding / morphological contrast boost for low-contrast or textured certificates.
  - Pass 3: Multi-scale search and orientation deskewing ($\pm 15^\circ, \pm 90^\circ, 180^\circ$).
  - Pass 4: Fallback to `pyzbar` / `qreader` when installed.
- **Output Data Structure**:
  ```python
  class QRCodeDetectionResult(BaseModel):
      qr_detected: bool
      qr_decoded: bool
      raw_content: Optional[str] = None
      verification_url: Optional[str] = None
      bounding_box: Optional[list[int]] = None
      confidence: float = 0.0
      error_message: Optional[str] = None
  ```

### 5.2 Issuer Registry & Safe URL Verifier (`app/modules/course_verification/url_verifier.py`)
- **SSRF & Network Security Protection**:
  - Enforce HTTPS protocol.
  - Restrict private/internal IP address ranges (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.169.254`).
  - Max redirect limit: 3 hops.
  - Timeout limit: 5.0 seconds.
  - User-Agent sanitization.
- **Issuer Registry**:
  - Structured list of known credentials platforms (e.g., Coursera, edX, Udemy, HarvardX, Stanford Online, Credly, Accredible, Trailhead, Microsoft Learn, AWS Training) with trusted root domains and regex patterns for certificate IDs.
- **Domain Trust Classification**:
  - `TRUSTED_ISSUER`: Domain matches verified official issuer registry.
  - `SUSPICIOUS_DOMAIN`: Domain masquerades or uses dynamic DNS / IP literal.
  - `UNKNOWN_DOMAIN`: Valid public domain but unregistered in directory.
  - `UNREACHABLE_ENDPOINT`: Server returns 404, 500, or timed out (categorized as `VERIFICATION_UNAVAILABLE`, never claimed fraudulent solely due to downtime).

### 5.3 Online Record Scraper & OCR Field Comparator (`app/modules/course_verification/comparator.py`)
- **Safe HTML & JSON Payload Parsing**:
  - Extract structured metadata from OpenGraph tags (`og:title`, `og:description`), JSON-LD schema (`EducationalOccupationalCredential`), or HTML DOM tables.
- **Normalized Field Comparison**:
  - Normalized string distance using `rapidfuzz` (Token Sort Ratio & Levenshtein similarity $\ge 85\%$ threshold).
  - Date normalization parsing (e.g., "September 2026", "2026-09-15", "15/09/2026").
  - Certificate ID alphanumeric canonicalization (stripping hyphens and spaces).
- **Copied QR Attack Detection (Critical Spec Requirement)**:
  - If `qr_valid == True` BUT `name_match == False` or `cert_id_match == False`:
    - Flag: `VALID_QR_BUT_CERTIFICATE_DATA_MISMATCH = True`.
    - Penalty: Hard veto forcing final verdict into `SUSPICIOUS` or `FRAUD_RISK`.

### 5.4 Document Tampering & Signature/Seal Integration (`app/modules/course_verification/tampering_analyzer.py`)
- Reuses existing ELA, copy-move detection, and Laplacian noise analysis.
- Extracts localized crops around:
  - Candidate Name bounding box.
  - Certificate ID bounding box.
  - Seal and Signature regions.
- Computes localized anomaly scores to determine if text substitution occurred over an authentic background.

### 5.5 Machine Learning Fraud-Risk Model (`ml/models/course_cert_classifier.joblib`)
- **Model Architecture**: Gradient-boosted decision trees (LightGBM / XGBoost / Random Forest) trained on a structured 14-dimensional feature vector:
  1. `ocr_confidence` $[0.0, 1.0]$
  2. `tampering_probability` $[0.0, 1.0]$
  3. `qr_detected` $[0, 1]$
  4. `qr_decoded` $[0, 1]$
  5. `url_valid_syntax` $[0, 1]$
  6. `issuer_trusted` $[0, 1]$
  7. `domain_match` $[0, 1]$
  8. `online_available` $[0, 1]$
  9. `name_match_score` $[0.0, 1.0]$
  10. `course_match_score` $[0.0, 1.0]$
  11. `cert_id_match_score` $[0.0, 1.0]$
  12. `date_match_score` $[0.0, 1.0]$
  13. `signature_score` $[0.0, 1.0]$
  14. `seal_score` $[0.0, 1.0]$

### 5.6 Decision Engine & Explainable Authenticity Scoring
- **Configurable Authenticity Score Weights**:
  - Online Issuer Verification: **25%**
  - Certificate Field Matching: **25%**
  - Document Integrity & Forensics: **20%**
  - QR Verification: **15%**
  - Issuer / Domain Trust: **10%**
  - Signature & Seal Evidence: **5%**
- **Decision Status Matrix**:
  - `VERIFIED`: Official online verification matches certificate fields AND document integrity is clean.
  - `SUSPICIOUS`: QR works but fields mismatch (copied QR attack) OR tampering detected around crucial fields.
  - `FRAUDULENT`: Confirmed spliced fields, invalid fake issuer masquerade, or multiple forged digital/physical signals.
  - `UNVERIFIED / VERIFICATION_UNAVAILABLE`: Offline issuer, verification page unreachable or timeout (never classified as fraudulent without positive evidence of tampering).

---

## 6. Database Schema Extensions

We extend the database by adding two ORM tables to [`backend/app/models/`](file:///c:/Users/rangs/Documents/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/backend/app/models):

### 6.1 `IssuerRegistryModel` (`backend/app/models/issuer_registry.py`)
```python
class IssuerRegistryModel(Base):
    __tablename__ = "issuer_registry"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issuer_name = Column(String(256), nullable=False, unique=True, index=True)
    official_domain = Column(String(256), nullable=False)
    verification_domain = Column(String(256), nullable=False)
    verification_pattern = Column(String(512), nullable=True)
    certificate_id_pattern = Column(String(256), nullable=True)
    trusted_status = Column(
        String(32), default="TRUSTED", nullable=False
    )  # TRUSTED, UNKNOWN, SUSPICIOUS
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 6.2 `CourseCertificateVerificationModel` (`backend/app/models/course_verification.py`)
```python
class CourseCertificateVerificationModel(Base):
    __tablename__ = "course_certificate_verifications"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("app_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Document info
    uploaded_file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    original_filename = Column(String(256), nullable=False)
    mime_type = Column(String(64), nullable=False)

    # Extracted data
    extracted_fields_json = Column(JSON, nullable=True)
    qr_data_json = Column(JSON, nullable=True)
    verification_url = Column(String(512), nullable=True)
    issuer = Column(String(256), nullable=True)

    # Online verification
    online_verification_data_json = Column(JSON, nullable=True)
    field_comparison_json = Column(JSON, nullable=True)

    # Forensic & ML signals
    tampering_analysis_json = Column(JSON, nullable=True)
    ml_prediction_json = Column(JSON, nullable=True)

    # Final verdict & scores
    authenticity_score = Column(Float, nullable=False, default=0.0)
    fraud_risk_score = Column(Float, nullable=False, default=0.0)
    final_status = Column(
        String(32), nullable=False, index=True
    )  # VERIFIED, SUSPICIOUS, FRAUDULENT, UNVERIFIED, etc.
    evidence_summary_json = Column(JSON, nullable=True)

    # Report paths
    report_pdf_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

---

## 7. API Endpoints Specification

New FastAPI router in `backend/app/api/v1/endpoints/course_certificates.py`:
- `POST /api/v1/course-certificates/upload` — Upload and rasterize course certificate (PDF/JPG/PNG).
- `POST /api/v1/course-certificates/{id}/verify` — Trigger asynchronous verification pipeline.
- `GET /api/v1/course-certificates/{id}` — Get live job status and intermediate findings.
- `GET /api/v1/course-certificates/{id}/report` — Get complete verification report JSON.
- `GET /api/v1/course-certificates/{id}/download-report` — Download official verification PDF report.
- `GET /api/v1/course-certificates/{id}/qr` — Get extracted QR code crop and decoded payload.
- `GET /api/v1/course-certificates/{id}/online-verification` — Get raw online record comparison.
- `GET /api/v1/issuers` — List recognized credential issuers and domain patterns.
- `POST /api/v1/issuers` — Register new credential issuer (Admin only).

---

## 8. Dataset Strategy & Synthetic Generation Pipeline

### 8.1 External Repositories Documentation (`dataset/README.md`)
- **Dataset A — DocTamper**: Document text tampering and altered numbers. (Documented in `dataset/external/DocTamper/README.md` with manual acquisition protocol; not committed to Git).
- **Dataset B — AIForge-Doc**: Inpainting and generative forgeries.
- **Dataset C — QR Threat Detection**: Benign, malicious, and tampered QR codes.
- **Dataset D — CEDAR Signature Dataset**: Genuine and forged offline signatures.
- **Dataset E — Omni-IML**: Optional benchmark for image manipulation localization.

### 8.2 Custom Course Certificate Dataset (`dataset/course_certificates/`)
- Target: 5,000–6,000 samples created specifically for research without violating privacy.
- Subdirectories:
  - `genuine/` (1,000–2,000 samples)
  - `tampered/name_changed/` (300 samples)
  - `tampered/certificate_id_changed/` (300 samples)
  - `tampered/date_changed/` (300 samples)
  - `tampered/course_changed/` (300 samples)
  - `tampered/grade_changed/` (300 samples)
  - `tampered/logo_changed/` (200 samples)
  - `tampered/seal_changed/` (200 samples)
  - `tampered/signature_changed/` (200 samples)
  - `tampered/qr_replaced/` (300 samples)
  - `tampered/qr_copied/` (300 samples — valid QR from cert A spliced onto cert B)
  - `tampered/multiple_fields/` (500 samples)
  - `metadata.csv`
- Split strategy: 70% Train, 15% Val, 15% Test grouped by base template to guarantee zero data leakage.

---

## 9. Frontend Integration Plan

### 9.1 Route & Navigation
- Add route `/course-certificate-verification` in `App.tsx`.
- Add "Course Verification" button/link with Lucide `Award` icon in `Navbar.tsx`.

### 9.2 Course Verification Page (`frontend/src/pages/CourseVerificationPage.tsx`)
- Drag-and-drop document upload (PDF, JPG, PNG up to 10MB).
- Live Document Preview with bounding box overlay.
- Step-by-step verification progress steppers:
  1. OCR Field Extraction
  2. QR Detection & URL Extraction
  3. Issuer Registry Lookup
  4. Online Verification Scraper
  5. Cross-Modal Field Comparison
  6. Document Forensics & Tampering Heatmap
  7. Final Explainable Score Synthesis
- Color-coded Verdict Banner:
  - 🟢 **VERIFIED**: Green card with confidence percentage.
  - 🟡 **SUSPICIOUS**: Amber warning highlighting specific mismatched fields or transplanted QR evidence.
  - 🔴 **FRAUDULENT**: Red alert indicating positive manipulation.
  - ⚪ **UNVERIFIED**: Slate notification indicating offline or unreachable issuer.
- Downloadable PDF Verification Report button.

---

## 10. Risk Analysis & Conflict Prevention

| Potential Conflict / Risk | Mitigation Strategy |
|---|---|
| Overwriting or breaking existing academic degree verification pipeline | Keep all new endpoints and models isolated under `/api/v1/course-certificates/` and separate database tables. |
| Inaccessible online verification URL causing false "FRAUDULENT" verdict | Explicit rule: Network timeouts or 404/500 errors produce `UNVERIFIED / VERIFICATION_UNAVAILABLE`, never `FRAUDULENT` unless positive tampering evidence exists. |
| Transferred QR code deceiving the system | Explicit comparative rule: `VALID_QR_BUT_CERTIFICATE_DATA_MISMATCH` directly forces verdict to `SUSPICIOUS`. |
| SSRF vulnerabilities when backend verifies arbitrary URLs | Strict URL sanitization, allowlist filtering, blocking loopback/private subnets, and enforcing timeouts. |
| Committing large training datasets to Git | Strictly enforce `.gitignore` rules for `dataset/raw/`, `dataset/external/`, `*.sql.gz`, `*.joblib`, `*.pt`. |
