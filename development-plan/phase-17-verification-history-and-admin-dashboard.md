# Phase 17 — Verification History & Admin Dashboard

## 1. Purpose

Implement the verification history and administrative oversight subsystem. This module delivers two primary frontend/backend interfaces:
1. **Verification History Dashboard:** Allows users and institutional verifiers to browse, search, filter, paginate, and re-download past certificate assessments.
2. **Administrative Control Center:** Provides platform administrators and university registrars with aggregate fraud analytics, system health monitors, university onboarding tools, master template management, and an immutable audit log explorer.

## 2. Why This Phase Exists

A verification platform requires long-term management and auditability:
- Institutional verifiers process hundreds of student certificates per semester. They need a searchable, paginated history to track which certificates passed or failed, export batch verification summaries, and re-access reports without re-uploading documents.
- University leadership and platform administrators need high-level fraud intelligence: What percentage of submitted certificates are fraudulent? Which specific manipulation techniques (e.g. grade tampering vs. cloned seals) are trending?
- Administrators must onboard new partner universities, configure master certificate templates, and manage user access.
- Security officers require an audit explorer to investigate suspicious IP activity or track employee verification actions.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-HIS-01** | Verification history table with pagination, multi-criteria filtering, and search | Paginated data grid with search by Name, Roll No, Verdict, Institution, Date |
| **FR-ADM-01** | Aggregate analytics dashboard (total verified, fraud rate, manipulation breakdown) | SQL aggregation queries and analytics charts (Bar, Donut, Time Series) |
| **FR-ADM-02** | System performance and health monitoring (average latency, error rates, disk usage) | Real-time diagnostic widgets tracking pipeline performance metrics |
| **FR-ADM-03** | Institution management portal (CRUD universities, status toggle, verifier assignment) | Administrative CRUD interface for university records |
| **FR-ADM-04** | Master template management portal (template upload, seal ROI preview, activation) | Visual template manager with interactive ROI boundary preview |
| **FR-ADM-05** | Searchable audit log explorer (filter by User, IP, Action, Timestamp) | Audit log data table with JSON detail inspector modal |
| **NFR-03** | Query performance (< 300ms history queries, < 500ms analytics) | Indexed SQL lookups and optimized aggregation queries |
| **TC-ADM-01** | Verification history pagination and filtering test | Chip ADM-11 |
| **TC-ADM-02** | Admin analytics aggregation and chart rendering test | Chip ADM-11 |
| **TC-ADM-03** | Institution CRUD and status toggle test | Chip ADM-12 |
| **TC-ADM-04** | Master template registration and preview test | Chip ADM-12 |
| **TC-ADM-05** | Audit log query and filter inspection test | Chip ADM-12 |

## 4. Inputs

- Database tables from Phase 14 (`certificate`, `verification_report`, `institution`, `institution_template`, `audit_log`).
- Authenticated user context and RBAC claims from Phase 15.

## 5. Outputs

- Verification History View (`/history`) in frontend.
- Admin Dashboard View (`/admin`) in frontend with sub-tabs: Overview, Institutions, Templates, Audit Logs.
- Backend API router `/api/v1/admin` providing aggregation and management endpoints.

## 6. Dependencies

- **Previous phases:** Phase 14 (Database & Backend API), Phase 15 (RBAC), Phase 16 (Frontend App).
- **Libraries:** Frontend: `react`, `lucide-react`, `recharts` / `chart.js` (for analytics charts); Backend: `sqlalchemy`, `fastapi`.

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── admin.py           # /api/v1/admin analytics and management endpoints
│   ├── schemas/
│   │   └── admin.py                   # AnalyticsSummary, InstitutionManagement schemas
│   └── services/
│       └── analytics_service.py       # SQL aggregation calculations
frontend/
├── src/
│   ├── pages/
│   │   ├── HistoryPage.tsx            # Verification history list & search
│   │   └── admin/
│   │       ├── AdminDashboardPage.tsx # Parent admin portal shell with tabs
│   │       ├── AnalyticsOverview.tsx  # KPI cards and Recharts analytics charts
│   │       ├── InstitutionsManager.tsx # University CRUD table & modal
│   │       ├── TemplatesManager.tsx   # Master template gallery & ROI inspector
│   │       └── AuditLogsViewer.tsx    # Audit log grid with JSON modal
│   ├── components/
│   │   ├── history/
│   │   │   ├── HistoryTable.tsx       # Paginated certificate records grid
│   │   │   ├── HistoryFilterBar.tsx   # Search, verdict filter, date range picker
│   │   │   └── QuickActionMenu.tsx    # View report, download PDF, delete action
│   │   └── admin/
│   │       ├── MetricCard.tsx         # KPI widget with trend arrow
│   │       ├── TemplatePreviewModal.tsx # Interactive seal ROI boundary preview
│   │       └── AuditDetailModal.tsx   # JSON viewer for audit event details
│   └── services/
│       └── adminService.ts            # Axios API calls for admin endpoints
└── tests/
    ├── backend/
    │   └── test_admin_endpoints.py
    └── frontend/
        └── HistoryPage.test.tsx
```

---

## 8. Implementation Chips

---

### CHIP ADM-01 — Verification History Data Grid & Query Service

**Objective:** Implement the backend query service and REST endpoint `GET /api/v1/certificates/history` supporting multi-column filtering, text search, sorting, and pagination (FR-HIS-01).

**Why:** Powers the history dashboard, allowing users to find specific student certificates among thousands of past submissions within 300ms.

**Dependencies:** Phase 14 Backend API, Phase 15 RBAC.

**Files to create:**
- `backend/app/api/v1/endpoints/certificates.py` (Enhance history query)
- `backend/app/services/certificate_service.py`

**Implementation:**
1. Support query parameters:
   - `page: int = 1`, `limit: int = 20`
   - `verdict: Optional[str]` (`AUTHENTIC`, `SUSPICIOUS`, `MANIPULATED`)
   - `search: Optional[str]` (Searches across Student Name, Roll Number, and Filename)
   - `institution_id: Optional[UUID]`
   - `date_from: Optional[date]`, `date_to: Optional[date]`
   - `sort_by: str = "created_at"`, `order: str = "desc"`
2. RBAC isolation:
   - If `role == "INSTITUTION_VERIFIER"`, automatically restrict query to certificates belonging to `user.institution_id`.
   - If `role == "PUBLIC_USER"`, restrict query to certificates uploaded by `user.id`.
   - If `role == "ADMIN"`, allow querying across all institutions.
3. Optimize queries using SQL indexes on `created_at`, `file_hash`, and `job_status`.

**Acceptance Criteria:**
- Returns paginated list of certificate records with total count and page metadata in $< 200$ms (TC-ADM-01).

---

### CHIP ADM-02 — Frontend Verification History Page & Filter Bar

**Objective:** Implement `HistoryPage` and `HistoryFilterBar` in the React frontend with search inputs, verdict dropdown filters, date pickers, and a clean data table (FR-HIS-01).

**Why:** Delivers a responsive, accessible interface for browsing past verifications.

**Dependencies:** CHIP ADM-01, Phase 16 Frontend.

**Files to create:**
- `frontend/src/pages/HistoryPage.tsx`
- `frontend/src/components/history/HistoryTable.tsx`
- `frontend/src/components/history/HistoryFilterBar.tsx`

**Implementation:**
1. Filter bar controls:
   - Search input with debounce (300ms).
   - Verdict dropdown: "All Verdicts", "Authentic Only", "Suspicious Only", "Manipulated Only".
   - Institution selector (if Admin).
   - Date range selector.
2. Data table columns:
   - Thumbnail preview (click to enlarge).
   - Student Name & Roll No.
   - Issuing University.
   - Upload Date & Time.
   - Authenticity Score badge (e.g. `92%` green, `34%` red).
   - Verdict Pill (`AUTHENTIC`, `SUSPICIOUS`, `MANIPULATED`).
   - Actions: "View Full Report", "Download PDF", "Delete" (if permitted).
3. Pagination controls: "Previous", page numbers, "Next", records per page selector.

**Acceptance Criteria:**
- Filter bar immediately updates table results; supports responsive scrolling on smaller screens (TC-ADM-01).

---

### CHIP ADM-03 — Backend Fraud Analytics & Aggregation Engine

**Objective:** Implement SQL aggregation routines in `AnalyticsService` and expose `GET /api/v1/admin/analytics/summary` computing fraud metrics and time-series trends (FR-ADM-01).

**Why:** Provides executive metrics tracking total throughput, fraud rates, and anomaly distributions.

**Dependencies:** Phase 14 Backend API.

**Files to create:**
- `backend/app/services/analytics_service.py`
- `backend/app/schemas/admin.py`

**Implementation:**
1. Compute KPI metrics:
   - `total_certificates_verified: int`
   - `total_authentic_count: int`
   - `total_suspicious_count: int`
   - `total_manipulated_count: int`
   - `overall_fraud_rate_percentage: float`
   - `average_pipeline_latency_seconds: float`
2. Compute categorical breakdown:
   - Manipulation breakdown by technique: Text Baseline Drift, Cloned Stamps/Seals, ELA Compression Anomalies, Database Contradictions.
3. Compute time-series data:
   - Daily verification volume and daily fraud count over the last 30 days (for trend charts).
4. Cache summary results in memory for 60 seconds to prevent DB overhead on high-traffic dashboards.

**Acceptance Criteria:**
- Aggregates metrics across millions of records in $< 350$ms using indexed SQL counts (TC-ADM-02).

---

### CHIP ADM-04 — Admin Overview Dashboard & Visual Analytics Charts

**Objective:** Implement `AnalyticsOverview` in the frontend using Recharts to visualize KPI cards, volume time-series charts, and fraud breakdown donut charts (FR-ADM-01).

**Why:** Gives platform administrators an instant graphical pulse on certificate verification operations.

**Dependencies:** CHIP ADM-03.

**Files to create:**
- `frontend/src/pages/admin/AnalyticsOverview.tsx`
- `frontend/src/components/admin/MetricCard.tsx`

**Implementation:**
1. Top KPI Cards:
   - Total Documents Analyzed (with % change vs last week).
   - Authentic Rate (e.g. 78.4%).
   - Detected Fraud Rate (e.g. 14.2% in crimson).
   - Flagged for Review (e.g. 7.4% in amber).
   - Average Analysis Time (e.g. 8.2s).
2. Charts:
   - **Verification Trends (Line/Area Chart):** Daily volume of verified documents vs. fraudulent documents over last 30 days.
   - **Verdict Distribution (Donut Chart):** Proportions of Authentic, Suspicious, and Manipulated certificates.
   - **Common Tampering Modalities (Bar Chart):** Frequency of detected anomaly types (Font Mismatch, SIFT Clone, ELA, DB Contradiction).

**Acceptance Criteria:**
- Charts render cleanly with interactive hover tooltips and responsive resizing (TC-ADM-02).

---

### CHIP ADM-05 — System Performance & Diagnostic Monitors

**Objective:** Implement the System Health monitoring tab in the admin dashboard tracking real-time server health, storage utilization, and pipeline latency (FR-ADM-02).

**Why:** Proactively informs administrators if storage is filling up or if OCR latency is degrading.

**Dependencies:** Phase 14 Backend API.

**Files to create:**
- `frontend/src/pages/admin/SystemHealthTab.tsx`

**Implementation:**
1. Diagnostic widgets:
   - Database Connection Status: Connected (Ping latency: 4ms).
   - Storage Usage: Progress bar showing disk usage (e.g. 14.2 GB used of 100 GB).
   - Poppler & PaddleOCR engine status: Online / Ready.
   - Pipeline Stage Latency Breakdown:
     - Ingestion: 0.8s
     - Preprocessing: 2.1s
     - OCR Extraction: 3.4s
     - Forensics: 1.8s
     - ML / DL Inference: 0.9s
     - Report Generation: 1.2s

**Acceptance Criteria:**
- Accurately displays subsystem health and latency benchmarks.

---

### CHIP ADM-06 — Institution Management Portal

**Objective:** Implement university onboarding and management interface under `/admin/institutions` allowing administrators to register new universities, edit details, and toggle active status (FR-ADM-03).

**Why:** Essential for platform expansion as new colleges and universities partner with the verification registry.

**Dependencies:** Phase 14 Backend API.

**Files to create:**
- `frontend/src/pages/admin/InstitutionsManager.tsx`

**Implementation:**
1. University listing table:
   - University Name & Institution Code.
   - Contact Email & State/Country.
   - Registered Master Templates count.
   - Verified Records count.
   - Active / Inactive toggle switch.
   - Actions: Edit, Manage Templates, View Records.
2. "Add New Institution" Modal Form:
   - Name, Code, Email, Phone, Official Website.
   - Client-side validation.
   - Submits `POST /api/v1/institutions`.

**Acceptance Criteria:**
- Full CRUD operations functional with immediate state update in data table (TC-ADM-03).

---

### CHIP ADM-07 — Master Template Management Portal & ROI Previewer

**Objective:** Implement template management interface under `/admin/templates` allowing university verifiers to view registered templates, inspect the university seal ROI, and upload new master templates (FR-ADM-04).

**Why:** Allows universities to maintain an active catalog of their official degree templates across different graduation years.

**Dependencies:** Phase 08 (Templates), Phase 14 Backend API.

**Files to create:**
- `frontend/src/pages/admin/TemplatesManager.tsx`
- `frontend/src/components/admin/TemplatePreviewModal.tsx`

**Implementation:**
1. Template catalog grid:
   - Template thumbnail preview.
   - Template Name, Degree Program, Effective Year Range (e.g. 2020–2024).
   - Status badge (Active / Archived).
2. "Template Inspector" Modal:
   - Displays high-resolution master template canvas.
   - Visualizes university seal bounding box ROI overlay in bright blue.
   - Visualizes masked variable text zones (Student Name, Roll No) in yellow.
3. "Upload New Template" Wizard:
   - Step 1: Upload high-res template image.
   - Step 2: Interactive drag-to-select box defining the University Seal ROI.
   - Step 3: Define effective years and degree program.
   - Submits template registration payload.

**Acceptance Criteria:**
- Visualizes template layout and seal ROI; handles template onboarding wizard (TC-ADM-04).

---

### CHIP ADM-08 — Searchable Audit Log Explorer

**Objective:** Implement the Audit Log Explorer view under `/admin/audit-logs` allowing compliance officers to search and filter system-wide events (FR-ADM-05).

**Why:** Provides full visibility into who uploaded, verified, modified, or downloaded certificates across the enterprise.

**Dependencies:** Phase 14 (Audit Service).

**Files to create:**
- `frontend/src/pages/admin/AuditLogsViewer.tsx`
- `frontend/src/components/admin/AuditDetailModal.tsx`

**Implementation:**
1. Audit log data table:
   - Timestamp (ISO UTC & local time).
   - User Email & Role badge.
   - Action Pill (`CERTIFICATE_UPLOADED`, `REPORT_DOWNLOADED`, `USER_LOGIN`).
   - IP Address.
   - Target Certificate ID (clickable link).
   - Action Details preview.
2. "View Event Details" Modal:
   - Formatted, syntax-highlighted JSON viewer showing the full `details_json` payload for the selected audit event.
3. Multi-criteria filtering: Search by IP, user email, action type, or date range.

**Acceptance Criteria:**
- Displays audit log records with interactive JSON payload inspector (TC-ADM-05).

---

### CHIP ADM-09 — Export Verification History to CSV / Excel

**Objective:** Implement client-side and server-side CSV export allowing verifiers to download their filtered history table as a spreadsheet (`.csv`).

**Why:** Required for institutional reporting, compliance archives, and batch auditing.

**Dependencies:** CHIP ADM-01.

**Files to create:**
- `frontend/src/utils/csvExport.ts`

**Implementation:**
1. "Export to CSV" button on History Page:
   - Exports all currently filtered records with columns: `Certificate ID`, `Filename`, `Student Name`, `Roll Number`, `Degree`, `University`, `Upload Date`, `Verdict`, `Authenticity Score %`, `Tier Status`.
   - Triggers direct browser download: `verification_history_export_{date}.csv`.

**Acceptance Criteria:**
- Generates clean, properly escaped CSV file matching active filter criteria.

---

### CHIP ADM-10 — Frontend Navigation Guard & Role-Guarded Route Shell

**Objective:** Implement React Router route guards enforcing role restrictions (`AdminRoute`, `VerifierRoute`) to prevent unauthorized access to `/admin` routes.

**Why:** Hardens client-side navigation security; non-admins attempting to navigate to `/admin` are immediately redirected to `/history` with a permission warning toast.

**Dependencies:** Phase 15 (RBAC), Phase 16 (Auth Hook).

**Files to create:**
- `frontend/src/components/common/RoleGuard.tsx`

**Acceptance Criteria:**
- Non-admin users are blocked from loading administrative UI pages.

---

### CHIP ADM-11 — Unit Tests: History Pagination, Filtering and Analytics

**Objective:** Test backend history pagination, multi-criteria filtering, and analytics calculation routines (TC-ADM-01, TC-ADM-02).

**Dependencies:** CHIP ADM-01, CHIP ADM-03.

**Files to create:**
- `backend/tests/integration/test_admin_endpoints.py`

**Implementation:**
1. Test `test_history_verdict_filtering()`: Verify querying `verdict=MANIPULATED` returns only manipulated certificates (TC-ADM-01).
2. Test `test_history_search_query()`: Verify search matches student name substring.
3. Test `test_analytics_kpi_calculation()`: Verify total counts and fraud rate arithmetic match database ground truth (TC-ADM-02).

**Acceptance Criteria:**
- 100% test pass rate across history and analytics backend tests.

---

### CHIP ADM-12 — Unit Tests: Institutions, Templates and Audit Logs

**Objective:** Test institution CRUD, master template registration, and audit log query endpoints (TC-ADM-03, TC-ADM-04, TC-ADM-05).

**Dependencies:** CHIP ADM-06, CHIP ADM-07, CHIP ADM-08.

**Files to modify:**
- `backend/tests/integration/test_admin_endpoints.py`

**Implementation:**
1. Test `test_institution_crud_and_status_toggle()`: Create institution, toggle active status, verify DB state (TC-ADM-03).
2. Test `test_template_registration_stores_roi()`: Upload template, verify seal ROI JSON is persisted (TC-ADM-04).
3. Test `test_audit_log_query_returns_ordered_events()`: Verify audit log endpoint returns events ordered by timestamp descending (TC-ADM-05).

**Acceptance Criteria:**
- All administrative integration test cases pass.

---

## 9. Implementation Order and Dependencies

```
CHIP ADM-01 (History Query Service)
    ↓
CHIP ADM-02 (Frontend History Page & Filter Bar)
    ↓
CHIP ADM-03 (Backend Fraud Analytics Engine)
    ↓
CHIP ADM-04 (Admin Analytics Overview & Charts)
    ↓
CHIP ADM-05 (System Performance & Health)
    ↓
CHIP ADM-06 (Institution Management Portal)
    ↓
CHIP ADM-07 (Master Template Management)
    ↓
CHIP ADM-08 (Searchable Audit Log Explorer)
    ↓
CHIP ADM-09 (CSV Export) & CHIP ADM-10 (Route Guards)
    ↓
CHIP ADM-11 & CHIP ADM-12 (Integration Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Verification history grid supports search, verdict filtering, date range pickers, and pagination.
- [ ] History queries execute in under 300ms using indexed database lookups.
- [ ] Analytics overview renders KPI widgets, 30-day verification trends, and fraud modality charts.
- [ ] System health tab monitors storage utilization, OCR latency, and database connectivity.
- [ ] Institution management portal enables onboarding universities and toggling active status.
- [ ] Master template manager visualizes template catalog and seal ROI bounding boxes.
- [ ] Searchable audit log explorer displays all user actions with JSON detail modal.
- [ ] Role guards prevent unauthorized users from viewing administrative pages.
- [ ] Verification history exports to CSV in one click.
- [ ] Test cases TC-ADM-01 through TC-ADM-05 passing with 100% success rate.
