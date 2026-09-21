# Course Certificate Authenticity Verification Module

**Authoritative Technical Specification & Architecture Manual**  
**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Module:** Course Certificate Authenticity Verification  

---

## 1. Overview & Business Objective

The **Course Certificate Authenticity Verification Module** extends the platform beyond traditional university transcripts and degrees to handle short-course, boot camp, and online professional credentials (e.g., Coursera, edX, Udemy, Stanford Online, HarvardX, Credly). 

These documents pose unique verification challenges:
1. **Dynamic & Scraped Online Registries**: Unlike university registrar databases, certificates frequently use online verification URLs encoded within QR codes.
2. **Copied QR Code Attack Vector**: A bad actor copies a valid QR code from an authentic certificate and splices it onto a forged certificate with an altered student name or credential ID. Traditional systems checking only QR accessibility erroneously validate the forged document.
3. **Multi-Source Pixel & Font Tampering**: Text inpainting, font variance, and background gradient manipulation are used to forge names, dates, and course titles.

To address these vulnerabilities, this module combines:
- Multi-pass QR code detection and deskewing.
- SSRF-safe URL verification and authoritative issuer registry validation.
- Live online credential scraping and normalization.
- Strict cross-modal field matching (Certificate OCR vs. Online Record).
- Pixel-level document forensics (ELA, Copy-Move, noise inconsistency).
- Signatory stroke and seal crest structure analysis.
- Multi-signal ML classification and explainable rule-based decision synthesis.

---

## 2. End-to-End Pipeline Architecture

```
[Uploaded Certificate: PDF / PNG / JPG]
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│ 1. Ingestion & Preprocessing                           │
│    - Format validation (.pdf, .png, .jpg, .jpeg, .webp)│
│    - Multi-page PDF rasterization via PyMuPDF (200 DPI)│
│    - Dynamic resizing & normalization                  │
└──────────────────┬─────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐ ┌───────────────────────────────────┐
│ 2. Dual OCR      │ │ 3. Robust QR Code Detector        │
│    - EasyOCR /   │ │    - Pass 1: Standard OpenCV      │
│      Tesseract   │ │    - Pass 2: Contrast Enhancement │
│    - Regex Field │ │    - Pass 3: Multi-angle Deskew   │
│      Extraction  │ │    - Fallback: pyzbar / qreader   │
└────────┬─────────┘ └───────────────┬───────────────────┘
         │                           │
         │           ┌───────────────┘
         │           ▼
         │   ┌───────────────────────────────────────────┐
         │   │ 4. URL & Issuer Registry Validation       │
         │   │    - HTTPS enforcement & SSRF protection  │
         │   │    - Authoritative domain lookup          │
         │   │    - Redirection chain tracking (max 3)   │
         │   └───────────────┬───────────────────────────┘
         │                   │
         │                   ▼
         │   ┌───────────────────────────────────────────┐
         │   │ 5. Online Record Scraper & Extractor      │
         │   │    - Safe HTTP client (5.0s timeout)      │
         │   │    - OpenGraph, JSON-LD & DOM parsing     │
         │   └───────────────┬───────────────────────────┘
         │                   │
         ▼                   ▼
┌────────────────────────────────────────────────────────┐
│ 6. Cross-Modal Field Consistency Engine                │
│    - Candidate Name, Cert ID, Course, Date comparison  │
│    - Levenshtein / Token-sort similarity scoring       │
│    - Copied QR Detection:                              │
│      VALID_QR_BUT_CERTIFICATE_DATA_MISMATCH Intercept  │
└──────────────────────────┬─────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌─────────────────────────────────┐ ┌────────────────────┐
│ 7. Document Forensics Engine    │ │ 8. Signature & Seal│
│    - Error Level Analysis (ELA) │ │    - Stroke density│
│    - Copy-Move Block Splicing   │ │    - Circular seal │
│    - Noise Inconsistency        │ │      crest contours│
│    - Bounding Box Localizer     │ └─────────┬──────────┘
└────────────────┬────────────────┘           │
                 └───────────────┬────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────┐
│ 9. Gradient Boosted ML Classifier                      │
│    - 14-dimensional normalized multi-signal vector     │
│    - Calibrated authenticity & fraud probabilities     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 10. Explainable Decision Engine & Report Generator     │
│    - Verdict: VERIFIED | SUSPICIOUS | FRAUDULENT |     │
│               UNVERIFIED / VERIFICATION_UNAVAILABLE    │
│    - 6-Component Weighted Authenticity Score (0-100%)  │
│    - Publication-Grade ReportLab PDF & JSON Dossier    │
└────────────────────────────────────────────────────────┘
```

---

## 3. Core Subsystems

### 3.1 Field Extraction & OCR Engine
The extraction subsystem (`backend/app/modules/course_verification/extractor.py`) normalizes certificate contents into a structured JSON contract:
```json
{
  "candidate_name": "Alice Johnson",
  "course_name": "Machine Learning Specialization",
  "certificate_id": "UC-12345678",
  "credential_id": "UC-12345678",
  "issuer": "Coursera",
  "institution": "Stanford Online",
  "issue_date": "2026-05-14",
  "completion_date": "2026-05-14",
  "expiry_date": null,
  "grade": "98.5%",
  "score": "98.5",
  "duration": "60 hours",
  "verification_url": "https://coursera.org/verify/UC-12345678",
  "qr_content": "https://coursera.org/verify/UC-12345678",
  "ocr_confidence": 0.94
}
```

### 3.2 Robust QR Code Detector
Located in `backend/app/modules/course_verification/qr_detector.py`, executes a 4-pass pipeline:
1. **Pass 1 (Direct)**: Standard `cv2.QRCodeDetector`.
2. **Pass 2 (Morphological Contrast)**: Grayscale contrast stretching + Otsu binarization for textured backgrounds.
3. **Pass 3 (Deskew)**: Rotation search ($\pm 15^\circ, \pm 90^\circ, 180^\circ$) for scanned documents.
4. **Pass 4 (Library Fallback)**: `pyzbar` / `qreader` fallback.

### 3.3 Safe URL Verifier & Issuer Registry
Located in `backend/app/modules/course_verification/url_verifier.py`:
- **SSRF Hardening**: Rejects loopback (`127.0.0.1`), private RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), AWS metadata service (`169.254.169.254`), and IPv6 equivalents.
- **Protocol Constraint**: Rejects plain HTTP in favor of HTTPS.
- **Hop & Timeout Limits**: Maximum 3 redirects, strict 5.0-second timeout.
- **Authoritative Issuers**: Registry tracking known domains (`coursera.org`, `edx.org`, `udemy.com`, `credly.com`, `accredible.com`, `stanford.edu`, `harvard.edu`, `microsoft.com`).

### 3.4 Cross-Modal Field Comparator & Copied QR Interceptor
Located in `backend/app/modules/course_verification/comparator.py`:
- Performs fuzzy token ratio comparison across Name, ID, Course, and Date fields.
- **Copied QR Defense**: If the online verification record resolves successfully to candidate $X$ with certificate ID $Y$, but the certificate document has candidate name $A$ or certificate ID $B$, the system raises:
  ```
  COPIED_QR_DETECTED = True
  VALID_QR_BUT_CERTIFICATE_DATA_MISMATCH
  ```
  This immediately overrides any positive score and caps the verdict to **SUSPICIOUS** or **FRAUDULENT**.

### 3.5 Explainable Decision Engine & Score Weights
Located in `backend/app/modules/course_verification/decision_engine.py`:
- **Authenticity Score Components**:
  - Online Issuer Verification: **25%**
  - Certificate Field Matching: **25%**
  - Document Forensics & Pixel Integrity: **20%**
  - QR Code Detection & Validity: **15%**
  - Issuer & Domain Trust: **10%**
  - Signature & Seal Evidence: **5%**
- **Decision Bands**:
  - 🟢 **VERIFIED**: Score $\ge 85\%$, online record matches certificate, no tampering.
  - 🟡 **SUSPICIOUS**: Copied QR mismatch, or tampering score elevated on name/ID.
  - 🔴 **FRAUDULENT**: Severe tampering, spliced text, or malicious masquerade domain.
  - ⚪ **UNVERIFIED / VERIFICATION_UNAVAILABLE**: Inaccessible URL or offline issuer (never penalized as fraudulent without positive tampering evidence).

---

## 4. Frontend User Experience

Route: `/course-certificate-verification`  
Components:
1. **Interactive File Dropzone**: Drag-and-drop support for PDF, PNG, JPG up to 10MB.
2. **Live Document Canvas**: High-resolution document viewer with bounding box overlays for QR codes and suspicious regions.
3. **Step-by-Step Progress Stepper**: Real-time visual progress from ingestion to final verdict.
4. **Multi-Signal Audit Cards**: Color-coded cards for QR, URL, Scraped Record, Forensics, and Seal/Signature.
5. **PDF Dossier Export**: One-click download of the official publication-grade ReportLab PDF.
