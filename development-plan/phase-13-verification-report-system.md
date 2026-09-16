# Phase 13 — Verification Report System

## 1. Purpose

Implement the official verification report generation and archiving subsystem. This module compiles the complete investigative dossier—certificate metadata, cryptographic SHA-256 fingerprint, extracted OCR academic fields, three-tier match status, composite authenticity scores, individual subsystem breakdowns, annotated visual evidence images (Grad-CAM, ELA heatmap, typography overlays), natural language findings, and a report-authenticity QR code—into downloadable PDF and machine-readable JSON formats.

## 2. Why This Phase Exists

The verification report is the definitive deliverable of the system:
- University admissions officers, academic registrars, and corporate HR recruiters require an official, court-admissible or compliance-grade summary of findings.
- The report must be self-verifying: Anyone holding a printed physical copy of the verification report must be able to scan an embedded QR code to verify that the report itself is authentic and un-tampered (using a cryptographic report hash).
- Both human-readable (structured PDF with side-by-side visual evidence) and machine-readable (JSON API response for automated HR background-check integration) formats are required.
- Standardizing the report format ensures legal defensibility and consistent audit trails across thousands of certificate assessments.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-REP-01** | Generate structured verification report (PDF and JSON formats) | ReportLab PDF compilation engine and Pydantic JSON serializer |
| **FR-REP-02** | Comprehensive report contents (metadata, OCR fields, 3-tier status, scores, evidence images, findings, QR code) | Multi-section report document model assembling all upstream outputs |
| **FR-REP-03** | Export report as downloadable PDF and JSON API response | FastAPI download endpoints with proper MIME streaming (`application/pdf`) |
| **FR-REP-04** | Unique Report ID generation, cryptographic signature, and persistent archiving | UUID v4 / collision-free report identifier, HMAC-SHA256 signature, filesystem archiving |
| **NFR-03** | Performance (< 3 seconds PDF generation time) | Pre-scaled image embedding and efficient ReportLab flowable elements |
| **NFR-08** | Modular architecture separating data assembly from rendering | Clean separation between `ReportAssembler`, `PDFRenderer`, and `JSONRenderer` |
| **TC-REP-01** | JSON report generation with all required fields test | Chip REP-11 |
| **TC-REP-02** | PDF report generation with ReportLab, layout, tables, and images test | Chip REP-11 |
| **TC-REP-03** | QR code generation and verification URL linking test | Chip REP-12 |
| **TC-REP-04** | Report tamper-evident digital signature/hash verification test | Chip REP-12 |
| **TC-REP-05** | PDF download and rendering integrity test | Chip REP-12 |

## 4. Inputs

- Certificate record and raw metadata from Phase 03.
- Preprocessed and enhanced image paths from Phase 04.
- Extracted academic fields from Phase 05.
- Text consistency scores and anomaly descriptions from Phase 06.
- Forensic findings and heatmap images from Phase 07.
- Three-tier status and record verification details from Phase 08.
- Baseline ML and Visual CNN prediction scores from Phases 09 & 10.
- Final verification decision and composite authenticity score from Phase 11.
- Natural language explanation and visual overlay paths from Phase 12.

## 5. Outputs

- Persisted PDF verification report (`storage/reports/{report_id}.pdf`).
- Persisted JSON verification report (`storage/reports/{report_id}.json`).
- Tamper-evident report verification hash (HMAC-SHA256).
- Embedded report verification QR code image (`storage/reports/{report_id}_qr.png`).
- Populated database record in `verification_report` table linking report paths.

## 6. Dependencies

- **Previous phases:** Phases 01 through 12 (Consumes outputs of all previous phases).
- **Libraries:** `reportlab`, `qrcode`, `Pillow`, `pydantic`, `fastapi`, `cryptography`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── modules/
│   │   └── report_generator/
│   │       ├── __init__.py
│   │       ├── assembler.py           # Assembles all pipeline outputs into ReportData
│   │       ├── qr_generator.py        # Generates verification QR code linked to report URL
│   │       ├── signer.py              # HMAC-SHA256 report digital signature generator
│   │       ├── pdf_renderer.py        # ReportLab PDF template and flowable builder
│   │       ├── json_renderer.py       # Standard JSON report exporter
│   │       └── service.py             # Orchestrator: ReportService
│   └── schemas/
│       └── report.py                  # Pydantic schemas: FullVerificationReport, ReportSummary
└── tests/
    └── unit/
        ├── test_report_assembler.py
        ├── test_qr_generator.py
        ├── test_report_signer.py
        ├── test_pdf_renderer.py
        └── test_report_service.py
```

---

## 8. Implementation Chips

---

### CHIP REP-01 — Verification Report Data Model & Assembler

**Objective:** Define the complete `FullVerificationReport` Pydantic domain schema and implement `ReportAssembler` to harvest and structure outputs from all 10 preceding analytical modules (FR-REP-01, FR-REP-02).

**Why:** Decouples report data collection from presentation rendering. The assembled data model feeds both the PDF generator and the JSON API response with zero discrepancy.

**Dependencies:** Phases 03 through 12.

**Files to create:**
- `backend/app/schemas/report.py`
- `backend/app/modules/report_generator/assembler.py`

**Implementation:**
1. Define `FullVerificationReport(BaseModel)` schema:
   - **Header & Metadata:**
     - `report_id: UUID`
     - `certificate_id: UUID`
     - `generated_at: datetime`
     - `file_metadata`: `filename`, `file_size_kb`, `file_format`, `sha256_checksum`, `upload_timestamp`
   - **Executive Verdict:**
     - `verdict`: `AUTHENTIC` | `SUSPICIOUS` | `MANIPULATED`
     - `authenticity_score`: float $[0.0, 1.0]$ (and formatted as percentage)
     - `confidence_score`: float $[0.0, 1.0]$
     - `tier_status`: `TIER_1_VERIFIED` | `TIER_2_CONSISTENT` | `TIER_3_INCONSISTENT`
     - `veto_applied`: bool, `veto_reason`: Optional[str]
     - `executive_summary`: str
   - **Extracted Academic Credentials:**
     - `student_name`, `roll_number`, `degree_program`, `institution_name`, `issue_date`, `grade_cgpa`, `certificate_id_num`
     - Flagged status and confidence per field
   - **Subsystem Score Breakdown:**
     - `visual_ai_score`: float
     - `tabular_ml_score`: float
     - `text_consistency_score`: float
     - `image_forensic_score`: float
     - `template_match_score`: float
   - **Investigative Findings:**
     - List of categorized natural language findings (Severity, Category, Description)
     - List of top contributing SHAP features
   - **Visual Evidence References:**
     - File paths to Original Image, OCR Overlay, Forensic Heatmap, Grad-CAM Heatmap, Unified Evidence Overlay
   - **Security & Integrity:**
     - `report_hmac_signature`: str
     - `verification_url`: str
2. Implement `ReportAssembler.assemble(...)` taking individual phase results and returning validated `FullVerificationReport`.

**Acceptance Criteria:**
- Generates fully populated, validated `FullVerificationReport` instance with 100% field coverage.

---

### CHIP REP-02 — Report Verification QR Code Generator

**Objective:** Generate a high-contrast QR code containing a secure verification URL linking to the official web verification endpoint for that specific report (FR-REP-02, TC-REP-03).

**Why:** Enables anyone holding a printed paper copy of the report to scan the QR code with a smartphone camera and immediately verify that the physical report matches the authentic digital report stored on the verification server.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/report_generator/qr_generator.py`

**Implementation:**
1. Implement `generate_report_qr(report_id: UUID, base_url: str, output_dir: Path) -> Path`:
   - Construct verification URL: `verification_url = f"{base_url}/verify-report/{report_id}"`.
   - Initialize QR generator:
     ```python
     qr = qrcode.QRCode(
         version=1,
         error_correction=qrcode.constants.ERROR_CORRECT_M,
         box_size=10,
         border=2
     )
     qr.add_data(verification_url)
     qr.make(fit=True)
     qr_img = qr.make_image(fill_color="black", back_color="white")
     ```
   - Save QR code to `storage/reports/{report_id}_qr.png`.
2. Embed university/system logo or shield icon at center of QR code (optional branding).

**Acceptance Criteria:**
- Generates valid, easily scannable PNG QR code encoding the exact report URL (TC-REP-03).

---

### CHIP REP-03 — Tamper-Evident Report Digital Signature & Hash

**Objective:** Compute a cryptographic HMAC-SHA256 signature across all canonical report fields (verdict, score, student roll number, timestamp) using a server secret key (FR-REP-02, TC-REP-04).

**Why:** Guarantees tamper-evidence. If someone modifies a single character or score in the stored report file, the HMAC signature verification fails immediately.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/report_generator/signer.py`

**Implementation:**
1. Implement `sign_report(report_data: FullVerificationReport, secret_key: str) -> str`:
   - Construct canonical string:
     `canonical = f"{report_data.report_id}|{report_data.certificate_id}|{report_data.file_metadata.sha256_checksum}|{report_data.verdict}|{report_data.authenticity_score:.4f}|{report_data.extracted_fields.roll_number}|{report_data.generated_at.isoformat()}"`.
   - Compute HMAC-SHA256:
     ```python
     signature = hmac.new(secret_key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
     ```
2. Implement `verify_report_signature(report_data: FullVerificationReport, signature: str, secret_key: str) -> bool`:
   - Recompute signature and compare using constant-time comparison `hmac.compare_digest()`.

**Acceptance Criteria:**
- Computes reproducible HMAC signature; detects any modification to scores or metadata (TC-REP-04).

---

### CHIP REP-04 — ReportLab Stylesheet, Typography & Header Layout

**Objective:** Configure the ReportLab PDF canvas styles, professional typography (Helvetica/Times), color palette (Navy Blue `#1A237E`, Emerald `#00C853`, Amber `#FFD600`, Crimson `#D50000`), and standard header/footer canvas flowables (FR-REP-01).

**Why:** An official verification report must present a clean, authoritative, publication-grade visual aesthetic suitable for legal and institutional compliance.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/modules/report_generator/pdf_styles.py`

**Implementation:**
1. Create `NumberedCanvas` flowable:
   - Computes total page count dynamically ("Page X of Y").
   - Renders running header with institution logo and running footer with report ID, generation timestamp, and confidentiality disclaimer.
2. Define custom paragraph styles:
   - `ReportTitle`: 22pt bold, `#1A237E`
   - `SectionHeading`: 14pt bold, `#283593` with horizontal underline rule
   - `VerdictBanner`: High-contrast colored banner based on verdict
   - `FieldLabel`: 9pt bold, `#424242`
   - `FieldValue`: 10pt regular, `#212121`
   - `FindingBullet`: 9pt regular, `#37474F`

**Acceptance Criteria:**
- Establishes unified, professional PDF design system with dynamic page numbering.

---

### CHIP REP-05 — Section Renderers: Executive Verdict & Credentials Table

**Objective:** Implement ReportLab flowables for Section 1 (Executive Summary & Verdict Banner) and Section 2 (Extracted Academic Credentials Table) (FR-REP-02).

**Why:** Verification officers look first at the top-line verdict and student particulars before inspecting granular forensic details.

**Dependencies:** CHIP REP-04.

**Files to create:**
- `backend/app/modules/report_generator/pdf_sections/executive_section.py`
- `backend/app/modules/report_generator/pdf_sections/credentials_section.py`

**Implementation:**
1. Executive Verdict Banner:
   - Full-width callout table with colored background:
     - `AUTHENTIC`: Pale green `#E8F5E9` background, dark green `#1B5E20` text, large shield checkmark icon.
     - `SUSPICIOUS`: Pale amber `#FFF8E1` background, dark amber `#F57F17` text, warning triangle icon.
     - `MANIPULATED`: Pale red `#FFEBEE` background, dark red `#B71C1C` text, alert octagonal icon.
   - Display: Verdict, Authenticity Score %, Confidence %, Three-Tier Status.
   - Paragraph: Executive summary narrative.
2. Credentials Table:
   - 2-column grid displaying:
     - Student Name | Roll / Registration No.
     - Degree / Program | Issuing University
     - Passing Year / Date | Grade / CGPA / Class
     - Certificate Serial No. | Document SHA-256 (truncated)
   - Visual badges: Green tick for verified fields, yellow warning pill for OCR confidence $< 0.70$.

**Acceptance Criteria:**
- Renders high-impact executive verdict banner and structured academic credentials table.

---

### CHIP REP-06 — Section Renderers: Subsystem Scores & Findings Dossier

**Objective:** Implement Section 3 (Analytical Subsystem Score Breakdown Table) and Section 4 (Categorized Key Findings & Natural Language Dossier) (FR-REP-02).

**Why:** Breaks down the math and plain-English reasons behind the verdict for forensic scrutiny.

**Dependencies:** CHIP REP-04.

**Files to create:**
- `backend/app/modules/report_generator/pdf_sections/scores_section.py`
- `backend/app/modules/report_generator/pdf_sections/findings_section.py`

**Implementation:**
1. Subsystem Score Table:
   - Columns: Analysis Subsystem, Score / Metric, Weight, Status, Brief Finding.
   - Rows:
     - Deep Learning Visual AI (CNN)
     - Tabular ML Classifier (Random Forest)
     - Typographical Consistency (Baseline/SWT)
     - Digital Image Forensics (ELA/Clone/Noise)
     - Institutional Template Matching (SSIM)
     - University Database Record Verification
2. Categorized Findings Section:
   - Color-coded bullet points grouped by severity (`CRITICAL`, `MAJOR`, `WARNING`, `INFO`).
   - Bullet text rendered using `FindingBullet` style.

**Acceptance Criteria:**
- Accurately renders score table and bulleted findings with clear visual hierarchy.

---

### CHIP REP-07 — Section Renderers: Visual Evidence Annex & Heatmap Plates

**Objective:** Implement Section 5 (Visual Evidence Annex) embedding side-by-side comparison plates of original image, OCR bounding box overlay, forensic ELA/thermal heatmap, and Grad-CAM activation map (FR-REP-02).

**Why:** Visual proof is essential for human confirmation. Showing side-by-side plates in the PDF report allows reviewers to immediately verify the cloned seal or manipulated text line.

**Dependencies:** CHIP REP-04.

**Files to create:**
- `backend/app/modules/report_generator/pdf_sections/evidence_section.py`

**Implementation:**
1. Layout: 2x2 grid of image plates formatted using ReportLab `Image` flowables:
   - Plate A: Original Uploaded Certificate Image
   - Plate B: Unified Anomaly Overlay (highlighted bounding boxes & legend)
   - Plate C: Forensic Heatmap (ELA & Copy-Move clone lines)
   - Plate D: Deep Learning Grad-CAM Attention Heatmap
2. Auto-scale images: Maintain original aspect ratio while constraining to cell bounds ($240 \times 170$ pt per plate).
3. Caption beneath each plate explaining the visualization.

**Acceptance Criteria:**
- Embeds all 4 visual evidence plates with sharp resolution and proper aspect ratio constraints.

---

### CHIP REP-08 — Section Renderers: QR Code, Audit Trail & Legal Disclaimer

**Objective:** Implement the final Report Footer section containing the scannable verification QR code, digital HMAC signature, institutional audit trail, and legal disclaimer notice (FR-REP-02).

**Why:** Completes the document's chain of custody and provides clear legal guidance on the advisory nature of AI-assisted authenticity verification.

**Dependencies:** CHIP REP-02, CHIP REP-03, CHIP REP-04.

**Files to create:**
- `backend/app/modules/report_generator/pdf_sections/footer_section.py`

**Implementation:**
1. Table with 2 columns:
   - Left Column: Digital HMAC signature string, Report ID, SHA-256 hash, and legal disclaimer text.
   - Right Column: Embedded QR code ($80 \times 80$ pt) with instruction: *"Scan to verify official authenticity of this report."*
2. Legal disclaimer:
   - *"Notice: This authenticity report is generated by an AI-assisted academic verification system using automated forensics, OCR, and institutional record matching. It is intended to assist admissions officers and employers. Final confirmation of academic credentials remains with the issuing institution."*

**Acceptance Criteria:**
- Renders scannable QR code, cryptographic signature, and legal disclaimer on final page.

---

### CHIP REP-09 — PDF Report Compilation & Optimization Service

**Objective:** Implement `PDFReportRenderer` to assemble all section flowables, build the multi-page PDF document using ReportLab `SimpleDocTemplate`, and optimize output file size (FR-REP-01, FR-REP-03).

**Why:** Coordinates the end-to-end PDF generation workflow and enforces the $< 3.0$ second performance requirement (NFR-03).

**Dependencies:** CHIP REP-04 through CHIP REP-08.

**Files to create:**
- `backend/app/modules/report_generator/pdf_renderer.py`

**Implementation:**
1. Implement `render_pdf_report(report_data: FullVerificationReport, output_path: Path) -> Path`:
   - Initialize `SimpleDocTemplate` (A4 format, margins: left=36pt, right=36pt, top=40pt, bottom=40pt).
   - Build flowable story list:
     1. Header & Title
     2. Executive Verdict Banner
     3. Extracted Credentials Grid
     4. Subsystem Score Breakdown Table
     5. Categorized Findings Dossier
     6. PageBreak()
     7. Visual Evidence Annex (4 plates)
     8. QR Code, Signature & Legal Footer
   - Compile document using `doc.build(story, canvasmaker=NumberedCanvas)`.
2. Execution benchmark: Ensure total generation time is $< 2.5$ seconds for standard 2-page report.

**Acceptance Criteria:**
- Generates professional, publication-ready 2-page PDF document within 3.0 seconds (TC-REP-02).

---

### CHIP REP-10 — JSON Report Exporter & Download API Endpoints

**Objective:** Implement JSON serialization service and FastAPI HTTP endpoints `GET /api/v1/reports/{id}/json` and `GET /api/v1/reports/{id}/pdf` for downloading reports (FR-REP-03, FR-REP-04).

**Why:** Provides the frontend UI and third-party API clients with immediate access to raw report data or downloadable PDF binaries.

**Dependencies:** CHIP REP-01, CHIP REP-09.

**Files to create:**
- `backend/app/modules/report_generator/json_renderer.py`
- `backend/app/api/v1/endpoints/reports.py`

**Implementation:**
1. Implement `export_json_report(report_data: FullVerificationReport) -> dict`:
   - Serialize Pydantic model with ISO-formatted timestamps and rounded floats.
2. Endpoints:
   - `GET /api/v1/reports/{report_id}`: Returns JSON report schema.
   - `GET /api/v1/reports/{report_id}/pdf`: Returns `FileResponse(path, media_type="application/pdf", filename=f"verification_report_{report_id}.pdf")`.
3. Error handling: Return HTTP 404 if report ID does not exist.

**Acceptance Criteria:**
- API serves valid JSON schema and streaming PDF file with correct content headers (TC-REP-05).

---

### CHIP REP-11 — Unit Tests: JSON and PDF Report Generation

**Objective:** Test automated assembly of `FullVerificationReport`, JSON serialization, and ReportLab PDF document compilation (TC-REP-01, TC-REP-02).

**Dependencies:** CHIP REP-01, CHIP REP-09.

**Files to create:**
- `backend/tests/unit/test_report_assembler.py`
- `backend/tests/unit/test_pdf_renderer.py`

**Implementation:**
1. Test `test_report_assembler_populates_all_fields()`: Verify no missing or null values in critical report attributes (TC-REP-01).
2. Test `test_json_report_serialization()`: Verify JSON output parses cleanly and matches Pydantic schema (TC-REP-01).
3. Test `test_pdf_generation_creates_valid_file()`: Verify generated PDF has size $> 50$KB and begins with `%PDF-1.` magic header (TC-REP-02).

**Acceptance Criteria:**
- 100% test pass rate on JSON and PDF generation routines.

---

### CHIP REP-12 — Unit Tests: QR Verification, Signatures & Download Endpoints

**Objective:** Test QR code scannability, HMAC digital signature verification, and report download API integrity (TC-REP-03, TC-REP-04, TC-REP-05).

**Dependencies:** CHIP REP-02, CHIP REP-03, CHIP REP-10.

**Files to create:**
- `backend/tests/unit/test_qr_generator.py`
- `backend/tests/unit/test_report_signer.py`
- `backend/tests/integration/test_report_api.py`

**Implementation:**
1. Test `test_qr_code_decodes_to_verification_url()`: Read generated QR image with `cv2.QRCodeDetector()` and assert decoded string equals verification URL (TC-REP-03).
2. Test `test_hmac_signature_tamper_detection()`: Alter 1 character in report score; verify signature verification returns `False` (TC-REP-04).
3. Test `test_pdf_download_endpoint()`: Request `GET /api/v1/reports/{id}/pdf` via test client; assert HTTP 200 and `application/pdf` Content-Type (TC-REP-05).

**Acceptance Criteria:**
- All tests pass, validating QR codes, HMAC signatures, and API streaming.

---

## 9. Implementation Order and Dependencies

```
CHIP REP-01 (Report Data Model & Assembler)
    ↓
CHIP REP-02 (Verification QR Code) ───────┐
    ↓                                     │
CHIP REP-03 (HMAC Digital Signature)      │
    ↓                                     │
CHIP REP-04 (ReportLab Styles & Canvas)   │
    ↓                                     │
├── CHIP REP-05 (Verdict & Credentials)   │
├── CHIP REP-06 (Scores & Findings)       │
├── CHIP REP-07 (Visual Evidence Annex)   │
└── CHIP REP-08 (QR & Signature Footer) ◄─┘
    ↓
CHIP REP-09 (PDF Compilation Engine)
    ↓
CHIP REP-10 (JSON Exporter & Download API)
    ↓
CHIP REP-11 & CHIP REP-12 (Unit & Integration Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Complete `FullVerificationReport` data schema models all pipeline findings without loss.
- [ ] Verification QR code generated with scannable URL linking to report verification page.
- [ ] Cryptographic HMAC-SHA256 digital signature generated, providing tamper evidence.
- [ ] Professional ReportLab PDF template renders executive verdict, credentials, scores, and findings.
- [ ] Visual evidence annex embeds side-by-side original, overlay, forensic, and Grad-CAM heatmaps.
- [ ] Scannable QR code and legal disclaimer embedded in report footer.
- [ ] High-resolution 2-page PDF document compiles in under 3.0 seconds (NFR-03).
- [ ] Endpoints expose both JSON API and direct streaming PDF downloads.
- [ ] Test cases TC-REP-01 through TC-REP-05 passing with 100% success rate.
