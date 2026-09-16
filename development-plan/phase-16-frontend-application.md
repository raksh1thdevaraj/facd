# Phase 16 — Frontend Application

## 1. Purpose

Implement the complete user-facing web application frontend using React 18, TypeScript, Vite, and TailwindCSS / modern CSS. This module delivers an intuitive, responsive, and visually compelling single-page application (SPA) covering certificate upload (drag-and-drop with client-side validation), real-time animated pipeline progress tracking, an interactive visual verification results dashboard with multi-layer overlay toggling (OCR boxes, Grad-CAM, ELA heatmaps, clone lines), and instant PDF/JSON report downloads.

## 2. Why This Phase Exists

The frontend is the primary touchpoint through which admissions officers, employers, and students interact with the AI verification system:
- High-stakes results must be presented with immediate clarity: A prominent, color-coded verdict banner (`AUTHENTIC`, `SUSPICIOUS`, `MANIPULATED`) accompanied by an intuitive radial authenticity gauge.
- Transparent explainability requires interactivity: Instead of viewing static images, users must be able to pan, zoom, and selectively toggle individual evidence layers (e.g. toggle "Show Grad-CAM Heatmap", toggle "Show OCR Bounding Boxes", toggle "Show Copy-Move Clones") to inspect the evidence directly on the certificate canvas.
- Real-time progress feedback eliminates user anxiety during the 8–15 second multi-stage analysis pipeline by rendering an animated stage-by-stage stepper (Ingestion -> Preprocessing -> OCR -> Forensics -> ML -> Report).
- The public QR verification page enables rapid smartphone-based verification of printed paper reports.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-FE-01** | Certificate upload view with drag-and-drop, format validation, and client-side preview | React Dropzone component supporting PDF, PNG, JPEG up to 10MB |
| **FR-FE-02** | Real-time analysis pipeline progress tracking with stage-by-stage status indicator | Polling hook (`usePipelineProgress`) with animated stepper component |
| **FR-FE-03** | Comprehensive verification results dashboard (verdict banner, radial score meter, details card) | Dynamic results layout with color-coded verdict themes and score cards |
| **FR-FE-04** | Interactive certificate viewer with toggleable visual evidence layers | Canvas / SVG overlay component with layer toggles (OCR, ELA, Grad-CAM, Clones) |
| **FR-FE-05** | Instant PDF and JSON report download action buttons | Direct streaming download handlers with loading spinners |
| **FR-FE-06** | Public QR report verification landing page (`/verify-report/:id`) | Lightweight, responsive standalone verification page for smartphone browsers |
| **NFR-09** | Cross-browser compatibility (Chrome, Firefox, Safari, Edge) | Modern standard HTML5/CSS3/ES6+ build targets |
| **NFR-10** | Usability & Accessibility (WCAG AA contrast, intuitive workflow) | High-contrast status colors, keyboard navigation, clear typography |
| **TC-FE-01** | File upload component test (drag-and-drop, validation, preview) | Chip FE-11 |
| **TC-FE-02** | Pipeline progress indicator and stage transitions test | Chip FE-11 |
| **TC-FE-03** | Results dashboard rendering test (verdict, score, credentials) | Chip FE-12 |
| **TC-FE-04** | Interactive document viewer layer toggling test | Chip FE-12 |
| **TC-FE-05** | PDF report download trigger test | Chip FE-12 |

## 4. Inputs

- Backend REST API endpoints from Phase 14 (`/api/v1/certificates`, `/api/v1/reports`, `/api/v1/auth`).
- User authentication tokens and profile state from Phase 15.
- Design tokens, color palette, and asset icons.

## 5. Outputs

- Production React + TypeScript SPA running on `http://localhost:5173` (dev) and optimized production bundle (`frontend/dist/`).
- Reusable UI component library (Dropzone, RadialGauge, LayerViewer, Stepper, VerdictBadge).
- Client-side API service layer with Axios interceptors and error handling.

## 6. Dependencies

- **Previous phases:** Phase 01 (Frontend Shell), Phase 14 (Backend API), Phase 15 (Auth Endpoints).
- **Libraries:** `react`, `react-dom`, `react-router-dom`, `axios`, `lucide-react` (icons), `tailwindcss`, `clsx`, `tailwind-merge`.

## 7. Files and Folder Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/                    # Navbar, Footer, Button, Card, Spinner, Modal
│   │   ├── upload/
│   │   │   ├── FileDropzone.tsx       # Drag-and-drop certificate upload
│   │   │   └── FilePreview.tsx        # Thumbnail / PDF preview
│   │   ├── progress/
│   │   │   ├── PipelineStepper.tsx    # 10-stage animated progress indicator
│   │   │   └── StatusPoller.tsx       # Background status polling coordinator
│   │   ├── results/
│   │   │   ├── VerdictBanner.tsx      # Authentic / Suspicious / Manipulated banner
│   │   │   ├── ScoreGauge.tsx         # Radial authenticity meter [0–100%]
│   │   │   ├── CredentialsCard.tsx    # Extracted student particulars table
│   │   │   ├── SubsystemScores.tsx    # Visual, ML, Text, Forensic score breakdown
│   │   │   ├── FindingsDossier.tsx    # Categorized accordion findings list
│   │   │   └── InteractiveViewer.tsx  # Canvas/SVG document viewer with layer toggles
│   ├── pages/
│   │   ├── HomePage.tsx               # Hero, quick launcher, demo certificates
│   │   ├── UploadPage.tsx             # Upload workflow and progress page
│   │   ├── ResultsPage.tsx            # Verification results dashboard
│   │   ├── VerifyReportPage.tsx       # Public QR verification landing page
│   │   ├── LoginPage.tsx              # Authentication login / register
│   │   └── NotFoundPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts                 # Authentication context and token management
│   │   ├── useCertificateUpload.ts    # Upload execution and error handling
│   │   └── usePipelineProgress.ts     # Polling hook tracking job progress (0–100%)
│   ├── services/
│   │   ├── api.ts                     # Configured Axios client with auth interceptors
│   │   ├── certificateService.ts      # API client for certificate upload & status
│   │   └── reportService.ts           # API client for reports and downloads
│   ├── types/
│   │   ├── certificate.ts
│   │   ├── report.ts
│   │   └── auth.ts
│   └── App.tsx                        # React Router layout and route definitions
```

---

## 8. Implementation Chips

---

### CHIP FE-01 — Frontend State Architecture, API Client & Axios Interceptors

**Objective:** Configure the centralized Axios HTTP client with automatic base URL configuration, request authorization headers (JWT Bearer injection), and 401 response interceptors with silent token refresh.

**Why:** Decouples API network logic from UI components, ensuring every request includes valid credentials and handles session expiration seamlessly.

**Dependencies:** Phase 01 (Frontend Shell), Phase 15 (Auth API).

**Files to create:**
- `frontend/src/services/api.ts`
- `frontend/src/types/auth.ts`

**Implementation:**
1. Configure Axios instance:
   ```typescript
   export const apiClient = axios.create({
     baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
     headers: { "Content-Type": "application/json" }
   });
   ```
2. Request interceptor: If `accessToken` exists in `localStorage` / memory, attach `Authorization: Bearer ${token}`.
3. Response interceptor:
   - If response is 401 Unauthorized: Attempt token refresh via `/auth/refresh`.
   - If refresh succeeds, retry failed request.
   - If refresh fails, clear auth state and redirect to `/login`.

**Acceptance Criteria:**
- Automatically attaches tokens and handles token expiration gracefully.

---

### CHIP FE-02 — Responsive App Layout, Navigation Bar & Design Theme

**Objective:** Implement the global responsive layout with navigation header, user profile dropdown, active route highlighting, system health indicator, and mobile menu.

**Why:** Provides the foundational visual frame and branding for the entire application across desktop and mobile viewports.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `frontend/src/components/common/Navbar.tsx`
- `frontend/src/components/common/Footer.tsx`
- `frontend/src/App.tsx` (Update routes)

**Implementation:**
1. Navbar features:
   - Brand logo with shield checkmark icon.
   - Navigation links: "Verify Certificate", "Sample Demos", "History", "Admin" (role-guarded).
   - User account status: "Login" button if guest; user avatar with role badge if authenticated.
2. Responsive hamburger menu for mobile screens.
3. Footer with version info, academic disclaimers, and documentation links.

**Acceptance Criteria:**
- Responsive navigation collapses gracefully on mobile devices.

---

### CHIP FE-03 — Drag-and-Drop Certificate Upload Component

**Objective:** Implement `FileDropzone` supporting drag-and-drop or file selection for PDF, PNG, and JPEG files with client-side file size (< 10MB) and format validation (FR-FE-01, TC-FE-01).

**Why:** Gives users an effortless, error-tolerant upload experience before initiating network transfers.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `frontend/src/components/upload/FileDropzone.tsx`
- `frontend/src/components/upload/FilePreview.tsx`

**Implementation:**
1. Dropzone behavior:
   - Drag hover states with animated blue/indigo dashed borders.
   - Accepted file types: `.pdf`, `.png`, `.jpg`, `.jpeg`.
   - File size validation: Reject files $> 10$MB immediately with friendly error message: *"File exceeds 10MB limit. Please upload a compressed or lower-resolution scan."*
2. File preview:
   - For images: Render live local thumbnail using `URL.createObjectURL(file)`.
   - For PDFs: Render PDF icon with filename, file size, and page count badge.
   - Remove/replace file button.
3. Include sample demo certificates button: Allows one-click testing using pre-loaded genuine and forged sample certificates.

**Acceptance Criteria:**
- Validates file type and size client-side; displays instant image preview (TC-FE-01).

---

### CHIP FE-04 — Real-Time Pipeline Progress Indicator & Status Polling Hook

**Objective:** Implement `usePipelineProgress` custom hook and `PipelineStepper` component that polls `GET /api/v1/certificates/{id}/status` every 800ms and renders an animated 6-stage stepper (FR-FE-02, TC-FE-02).

**Why:** Replaces static loading spinners with an informative, transparent progress experience showing exactly which AI analysis stage is currently active.

**Dependencies:** Phase 14 Backend API.

**Files to create:**
- `frontend/src/hooks/usePipelineProgress.ts`
- `frontend/src/components/progress/PipelineStepper.tsx`

**Implementation:**
1. Stepper stages:
   1. Document Ingestion & Validation
   2. Image Preprocessing & Deskewing
   3. OCR Text & Field Extraction
   4. Forensics & Typography Analysis
   5. Multimodal AI & Record Verification
   6. Report Dossier Generation
2. Component visual states:
   - Completed stage: Green circle with checkmark.
   - Active stage: Pulsing blue circle with animated spinner.
   - Pending stage: Muted gray circle.
   - Failed stage: Red circle with exclamation icon and error message.
3. Polling logic:
   - Poll every 800ms while `status === "PROCESSING"` or `"PENDING"`.
   - When `status === "COMPLETED"`, auto-navigate to `/results/{id}`.
   - If `status === "FAILED"`, stop polling and display actionable error message with retry button.

**Acceptance Criteria:**
- Smoothly transitions through stages from 0% to 100% and auto-redirects on completion (TC-FE-02).

---

### CHIP FE-05 — Verification Results: Verdict Banner & Radial Score Gauge

**Objective:** Implement high-impact visual components for the primary authenticity verdict and score: `VerdictBanner` and animated SVG `ScoreGauge` (FR-FE-03, TC-FE-03).

**Why:** Users must understand the definitive outcome of the verification in the first 2 seconds of opening the dashboard.

**Dependencies:** Phase 11 Decision Engine.

**Files to create:**
- `frontend/src/components/results/VerdictBanner.tsx`
- `frontend/src/components/results/ScoreGauge.tsx`

**Implementation:**
1. `VerdictBanner`:
   - `AUTHENTIC`: Emerald green theme (`bg-emerald-50 border-emerald-500 text-emerald-900`), large ShieldCheck icon, label: "CERTIFICATE VERIFIED AS AUTHENTIC".
   - `SUSPICIOUS`: Amber yellow theme (`bg-amber-50 border-amber-500 text-amber-900`), AlertTriangle icon, label: "SUSPICIOUS — MANUAL REVIEW RECOMMENDED".
   - `MANIPULATED`: Crimson red theme (`bg-rose-50 border-rose-500 text-rose-900`), AlertOctagon icon, label: "EVIDENCE OF MANIPULATION DETECTED".
   - Displays Three-Tier badge: "Tier 1: Institutional Record Match" or "Tier 2: Template Consistent".
2. `ScoreGauge`:
   - Animated SVG circular progress ring displaying authenticity percentage (e.g. `94%`).
   - Color transitions dynamically: Green ($\ge 85\%$), Amber ($60–84\%$), Red ($< 60\%$).
   - Displays confidence rating sub-label: "Confidence: High (98%)".

**Acceptance Criteria:**
- Renders responsive verdict banner and animated radial gauge matching backend status (TC-FE-03).

---

### CHIP FE-06 — Verification Results: Extracted Credentials & Subsystem Scores

**Objective:** Implement `CredentialsCard` displaying extracted student particulars and `SubsystemScores` displaying the horizontal progress bars for each analytical module (FR-FE-03).

**Why:** Allows reviewers to verify student details at a glance and see exactly which subsystem scored high or low.

**Dependencies:** Phase 05 (OCR), Phase 11 (Scores).

**Files to create:**
- `frontend/src/components/results/CredentialsCard.tsx`
- `frontend/src/components/results/SubsystemScores.tsx`

**Implementation:**
1. `CredentialsCard`:
   - Clean 2-column grid showing Student Name, Roll No, Degree, University, Issue Date, CGPA.
   - Low-confidence OCR fields ($< 0.70$) highlighted with amber warning pill: *"Low OCR Confidence (64%) — Verify Manually"*.
2. `SubsystemScores`:
   - Horizontal progress bars for:
     - Deep Learning Visual AI (`92%`)
     - Forensic Image Analysis (`88%`)
     - Typographical Consistency (`95%`)
     - Master Template Alignment (`84%`)
     - Database Record Verification (`100%`)

**Acceptance Criteria:**
- Accurately renders extracted fields and modular score breakdown bars.

---

### CHIP FE-07 — Interactive Document Viewer with Multi-Layer Overlays

**Objective:** Implement `InteractiveViewer` rendering the high-resolution certificate image with pan/zoom controls and toggleable SVG/Canvas evidence overlay layers (FR-FE-04, TC-FE-04).

**Why:** The centerpiece of the verification dashboard. Allows investigators to interactively toggle evidence on and off directly over the certificate canvas.

**Dependencies:** Phase 12 Explainability.

**Files to create:**
- `frontend/src/components/results/InteractiveViewer.tsx`

**Implementation:**
1. Viewer controls:
   - Zoom In / Zoom Out / Reset Zoom buttons.
   - Fullscreen modal toggle.
2. Toggleable Evidence Layer Toolbar:
   - `[x] OCR Bounding Boxes`: Renders green/amber boxes over detected words; hovering displays recognized text and confidence %.
   - `[x] Forensic Anomalies`: Highlights ELA recompression blocks and SIFT copy-move clone lines.
   - `[x] Deep Learning Grad-CAM`: Overlays semi-transparent thermal heatmap showing CNN attention peaks.
   - `[x] Typography Anomalies`: Highlights baseline drift and font size mismatches with callout badges.
3. Implementation: Render responsive SVG coordinate overlay layered directly over the base `<img>` element using normalized coordinates $[0.0, 1.0]$.

**Acceptance Criteria:**
- Users can smoothly zoom, pan, and toggle individual visual evidence layers independently (TC-FE-04).

---

### CHIP FE-08 — Categorized Findings Dossier & Executive Summary Accordion

**Objective:** Implement `FindingsDossier` component presenting natural-language findings in an expandable accordion grouped by severity (`CRITICAL`, `MAJOR`, `WARNING`, `INFO`) (FR-FE-03).

**Why:** Gives users clear, readable explanations of every detected issue without technical jargon.

**Dependencies:** Phase 12 Explainability.

**Files to create:**
- `frontend/src/components/results/FindingsDossier.tsx`

**Implementation:**
1. Accordion items:
   - Severity pill with color coding.
   - Finding title and concise description.
   - "Locate on Certificate" action button: Clicking scrolls and zooms the `InteractiveViewer` directly to the corresponding bounding box coordinate.
2. Pristine certificate state: Displays positive affirmations (e.g. *"Typography is consistent across all lines"*, *"No compression anomalies detected"*).

**Acceptance Criteria:**
- Categorizes findings by severity and links directly to visual viewer coordinates.

---

### CHIP FE-09 — Report Download Action Triggers & Sharing

**Objective:** Implement action buttons for downloading official PDF verification reports, exporting raw JSON, and copying shareable verification links (FR-FE-05, TC-FE-05).

**Why:** Enables users to save, archive, or distribute the verification dossier in one click.

**Dependencies:** Phase 13 Report System.

**Files to create:**
- `frontend/src/components/results/ReportActions.tsx`

**Implementation:**
1. "Download Official PDF Report":
   - Calls `GET /api/v1/reports/{id}/pdf`.
   - Triggers native browser file download (`verification_report_{id}.pdf`) with download progress spinner.
2. "Export Machine-Readable JSON":
   - Downloads structured JSON for API integration.
3. "Copy Verification Link":
   - Copies public verification URL to clipboard with toast notification.

**Acceptance Criteria:**
- Successfully initiates PDF and JSON file downloads with loading indicators (TC-FE-05).

---

### CHIP FE-10 — Public QR Report Verification Landing Page

**Objective:** Implement the standalone, responsive public report verification page at `/verify-report/:id` designed specifically for mobile smartphone browsers (FR-FE-06).

**Why:** When someone scans the QR code on a printed verification report, this lightweight page opens immediately to confirm the report's official validity.

**Dependencies:** Phase 13 Report System, Phase 14 Backend API.

**Files to create:**
- `frontend/src/pages/VerifyReportPage.tsx`

**Implementation:**
1. Features:
   - Official system header: "Official Academic Verification Registry".
   - Digital HMAC Signature Verification Check: Green badge: *"Cryptographic Signature Verified — Authentic Record"*.
   - Summary of verified certificate: Student Name, Roll No, Degree, University, Issue Date, Final Verdict, Verification Timestamp.
   - "Download Original PDF" button.
2. Mobile-optimized: Clean, fast-loading, zero login required.

**Acceptance Criteria:**
- Loads instantly on mobile browsers and displays verified report confirmation.

---

### CHIP FE-11 — Unit Tests: Upload Component and Progress Stepper

**Objective:** Test client-side upload validation, drag-and-drop interactions, and animated pipeline progress transitions (TC-FE-01, TC-FE-02).

**Dependencies:** CHIP FE-03, CHIP FE-04.

**Files to create:**
- `frontend/src/tests/FileDropzone.test.tsx`
- `frontend/src/tests/PipelineStepper.test.tsx`

**Implementation:**
1. Test `dropzone_rejects_oversized_file()`: Simulating 15MB file triggers error notification (TC-FE-01).
2. Test `dropzone_accepts_valid_pdf()`: Simulating 2MB PDF sets file state and displays preview.
3. Test `stepper_advances_through_pipeline_stages()`: Mocking status updates transitions active stage indicator correctly (TC-FE-02).

**Acceptance Criteria:**
- 100% test pass rate across upload and progress components.

---

### CHIP FE-12 — Unit Tests: Results Dashboard & Interactive Overlay Toggling

**Objective:** Test results dashboard rendering, layer toggle state changes in the interactive viewer, and PDF download triggers (TC-FE-03, TC-FE-04, TC-FE-05).

**Dependencies:** CHIP FE-05, CHIP FE-07, CHIP FE-09.

**Files to create:**
- `frontend/src/tests/ResultsPage.test.tsx`
- `frontend/src/tests/InteractiveViewer.test.tsx`

**Implementation:**
1. Test `verdict_banner_renders_correct_theme()`: Verdict `MANIPULATED` displays crimson styling and alert icon (TC-FE-03).
2. Test `layer_toggles_show_and_hide_overlays()`: Toggling "Grad-CAM" switch renders corresponding overlay element (TC-FE-04).
3. Test `download_pdf_button_triggers_api_call()`: Clicking download triggers API request (TC-FE-05).

**Acceptance Criteria:**
- All frontend integration test cases pass.

---

## 9. Implementation Order and Dependencies

```
CHIP FE-01 (Axios Client & Auth Interceptors)
    ↓
CHIP FE-02 (Responsive Navbar & Layout)
    ↓
CHIP FE-03 (Drag-and-Drop Dropzone)
    ↓
CHIP FE-04 (Progress Stepper & Polling Hook)
    ↓
├── CHIP FE-05 (Verdict Banner & Score Gauge)
├── CHIP FE-06 (Credentials & Subsystem Scores)
├── CHIP FE-07 (Interactive Multi-Layer Viewer)
├── CHIP FE-08 (Findings Dossier Accordion)
└── CHIP FE-09 (Report Download Actions)
    ↓
CHIP FE-10 (Public QR Verification Landing Page)
    ↓
CHIP FE-11 & CHIP FE-12 (Frontend Component Tests)
```

---

## 10. Phase Completion Checklist

- [ ] File dropzone supports drag-and-drop for PDF, PNG, and JPEG with 10MB client-side validation.
- [ ] Live image preview and PDF badge displayed immediately upon file selection.
- [ ] Animated 6-stage pipeline stepper provides real-time progress feedback (0–100%).
- [ ] Prominent verdict banner clearly displays `AUTHENTIC`, `SUSPICIOUS`, or `MANIPULATED`.
- [ ] Radial score gauge animates authenticity percentage with dynamic color transitions.
- [ ] Extracted academic credentials table highlights low-confidence OCR fields.
- [ ] Interactive viewer supports zoom/pan and independent toggling of OCR, ELA, Grad-CAM, and typography layers.
- [ ] Categorized findings dossier lists natural language findings grouped by severity.
- [ ] Instant PDF and JSON report downloads functional with loading feedback.
- [ ] Public mobile-friendly QR verification page at `/verify-report/:id` confirms report validity.
- [ ] Test cases TC-FE-01 through TC-FE-05 passing with 100% success rate.
