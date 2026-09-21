# Phase 14 — Database & Backend API

## 1. Purpose

Implement the complete production database architecture and unified RESTful API subsystem. This module realizes all 11 tables from the Design Documents plus the supporting `text_consistency_result` table using SQLAlchemy 2.0, manages schema versioning via Alembic migrations, provides asynchronous background job orchestration for long-running certificate analysis pipelines, and exposes versioned, validated, and documented FastAPI endpoints (`/api/v1`) with full audit logging and error handling.

## 2. Why This Phase Exists

Up to this point, individual analytical algorithms (OCR, Forensics, Template Matching, ML, Explainability, Reports) were developed and tested as standalone Python modules. This phase integrates them into an enterprise web service:
- Persistent relational storage: Every certificate, user, audit action, OCR token, forensic finding, and verification report must be stored with strict foreign key integrity and indexing.
- Asynchronous pipeline execution: Certificate analysis (OCR + Forensics + DL inference) takes 8–15 seconds total. Running this synchronously inside an HTTP request would block threads and cause gateway timeouts. An async background task runner (FastAPI `BackgroundTasks` / Redis queue) decouples upload receipt from pipeline execution.
- Unified REST API: Frontend single-page applications and third-party institutional clients require clean, OpenAPI-documented HTTP endpoints for uploading, polling status, fetching reports, and managing university templates.
- Audit compliance: Every view, upload, verification, and template change must be permanently recorded in an immutable `audit_log` table.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-API-01** | Complete database schema implementation (11 Design Docs tables + supporting tables) | SQLAlchemy 2.0 declarative models with Alembic migrations |
| **FR-API-02** | Asynchronous analysis pipeline orchestration and job status tracking | Job queue / background worker with status polling (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`) |
| **FR-API-03** | RESTful certificate management endpoints (Upload, Status, Details, List, Delete) | FastAPI router at `/api/v1/certificates` |
| **FR-API-04** | Institutional template and record management endpoints | FastAPI router at `/api/v1/institutions` |
| **FR-API-05** | Immutable audit logging of all system actions and verification events | Centralized audit log interceptor recording user, IP, action, timestamp |
| **NFR-03** | Scalable API performance and fast endpoint response times | Async FastAPI handlers, connection pooling, indexed queries |
| **NFR-04** | Concurrency and async background job handling | Decoupled background task execution with progress percentage |
| **NFR-08** | Modular API architecture with versioned routers | Clean v1 router aggregation and dependency injection |
| **TC-API-01** | Database migration execution and schema creation test | Chip API-12 |
| **TC-API-02** | Certificate CRUD API endpoints test | Chip API-12 |
| **TC-API-03** | Pipeline async processing and status polling test | Chip API-13 |
| **TC-API-04** | Database transaction rollbacks on pipeline errors test | Chip API-13 |
| **TC-API-05** | Audit log recording on all certificate operations test | Chip API-13 |

## 4. Inputs

- Database configuration URL from `.env` (`sqlite:///./certificate_verification.db` for dev, `postgresql://...` for prod).
- Analytical pipeline services from Phases 03 through 13.
- User authentication context from Phase 15.

## 5. Outputs

- Fully migrated database schema with 12 tables and foreign key relationships.
- Running FastAPI application with interactive Swagger documentation (`/docs`) and ReDoc (`/redoc`).
- Background worker executing the 10-stage verification pipeline asynchronously.
- Documented REST endpoints under `/api/v1/`.

## 6. Dependencies

- **Previous phases:** Phases 01 through 13 (Integrates all preceding modules).
- **Libraries:** `fastapi`, `uvicorn`, `sqlalchemy>=2.0`, `alembic`, `pydantic>=2.0`, `psycopg2-binary` (PostgreSQL), `httpx`, `pytest`.

## 7. Files and Folder Structure

```
backend/
├── alembic/
│   ├── env.py
│   └── versions/                      # Migration revisions
├── app/
│   ├── database.py                    # Engine, sessionmaker, get_db dependency
│   ├── models/
│   │   ├── __init__.py                # Imports all models for Alembic discovery
│   │   ├── institution.py             # institution table
│   │   ├── user.py                    # app_user table
│   │   ├── certificate.py             # certificate table
│   │   ├── ocr_field.py               # ocr_field table
│   │   ├── forensic_finding.py        # forensic_finding table
│   │   ├── text_consistency.py        # text_consistency_result table (supporting)
│   │   ├── template_match.py          # template_match_result table
│   │   ├── ml_prediction.py           # ml_prediction table
│   │   ├── report.py                  # verification_report table
│   │   ├── template.py                # institution_template table
│   │   ├── record.py                  # institution_record table
│   │   └── audit_log.py               # audit_log table
│   ├── schemas/                       # Pydantic request/response schemas
│   │   ├── certificate.py
│   │   ├── institution.py
│   │   └── audit.py
│   ├── services/
│   │   ├── pipeline_orchestrator.py   # Runs all 10 analysis steps sequentially
│   │   ├── certificate_service.py     # Certificate CRUD and queries
│   │   └── audit_service.py           # Writes audit log records
│   └── api/
│       └── v1/
│           ├── router.py              # Aggregates sub-routers
│           └── endpoints/
│               ├── certificates.py    # /api/v1/certificates
│               ├── institutions.py    # /api/v1/institutions
│               ├── reports.py         # /api/v1/reports
│               └── audit.py           # /api/v1/audit-logs
└── tests/
    └── integration/
        ├── test_database_migrations.py
        ├── test_certificate_endpoints.py
        ├── test_async_pipeline.py
        └── test_audit_logging.py
```

---

## 8. Implementation Chips

---

### CHIP API-01 — SQLAlchemy 2.0 Database Connection & Session Management

**Objective:** Implement the robust database connection engine, scoped session factory, and FastAPI dependency injection (`get_db`) with support for SQLite (dev) and PostgreSQL (prod) (FR-API-01).

**Why:** Enforces transactional integrity, connection pooling, and automatic session cleanup (close on request completion) to prevent connection leaks.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/database.py`

**Implementation:**
1. Configure SQLAlchemy 2.0 engine:
   ```python
   # Detect SQLite vs PostgreSQL for pool settings
   is_sqlite = settings.DATABASE_URL.startswith("sqlite")
   engine_args = (
       {"connect_args": {"check_same_thread": False}}
       if is_sqlite
       else {
           "pool_size": 20,
           "max_overflow": 10,
           "pool_pre_ping": True,
           "pool_recycle": 3600,
       }
   )
   engine = create_engine(settings.DATABASE_URL, **engine_args)
   SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
   ```
2. Implement FastAPI session dependency:
   ```python
   def get_db() -> Generator[Session, None, None]:
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```
3. Enable foreign key enforcement for SQLite via PRAGMA listener.

**Acceptance Criteria:**
- Provides thread-safe DB sessions with automatic closure and connection pooling.

---

### CHIP API-02 — Complete 12-Table Relational Schema Definition

**Objective:** Define all 11 relational tables from the Design Documents plus the supporting `text_consistency_result` table using SQLAlchemy 2.0 mapped declarative syntax (FR-API-01).

**Why:** Creates the single source of truth for the relational data layer, enforcing foreign keys, cascade rules, and indexes.

**Dependencies:** CHIP API-01.

**Files to create:**
- `backend/app/models/*.py` (all 12 model files)
- `backend/app/models/__init__.py`

**Implementation:**
1. Implement all 12 models:
   - `Institution`: `id`, `name`, `code`, `contact_email`, `is_active`, `created_at`.
   - `AppUser`: `id`, `institution_id` (FK), `email`, `password_hash`, `full_name`, `role`, `is_active`.
   - `Certificate`: `id`, `user_id` (FK), `institution_id` (FK), `file_path`, `file_hash` (indexed), `original_filename`, `file_size`, `mime_type`, `job_status`, `job_error`, `job_progress`, `preprocessed_image_path`, `created_at`.
   - `OCRField`: `id`, `certificate_id` (FK), `field_name`, `field_value`, `confidence_score`, `bounding_box`, `is_flagged`.
   - `ForensicFinding`: `id`, `certificate_id` (FK), `finding_type`, `confidence_score`, `bounding_box`, `description`, `heatmap_image_path`.
   - `TextConsistencyResult`: `id`, `certificate_id` (FK), `overall_score`, `baseline_score`, `font_size_score`, `stroke_weight_score`, `spacing_score`, `logical_score`, `anomalous_regions_json`.
   - `TemplateMatchResult`: `id`, `certificate_id` (FK), `template_id` (FK), `ssim_score`, `seal_score`, `tier_status`, `discrepancy_notes`.
   - `MLPrediction`: `id`, `certificate_id` (FK), `model_version`, `prediction_label`, `fake_probability`, `confidence_score`, `feature_vector_json`, `latency_ms`.
   - `VerificationReport`: `id`, `certificate_id` (FK), `overall_score`, `verdict`, `confidence_score`, `sub_scores_json`, `veto_applied`, `pdf_path`, `json_path`, `hmac_signature`.
   - `InstitutionTemplate`: `id`, `institution_id` (FK), `template_name`, `degree_program`, `image_path`, `feature_data_path`, `seal_roi`, `effective_years`.
   - `InstitutionRecord`: `id`, `institution_id` (FK), `student_name`, `roll_number` (indexed), `degree_name`, `passing_year`, `cgpa`.
   - `AuditLog`: `id`, `user_id` (FK), `certificate_id` (FK), `action`, `ip_address`, `details_json`, `created_at`.
2. Configure bidirectional SQLAlchemy relationships with `cascade="all, delete-orphan"` where appropriate.

**Acceptance Criteria:**
- All 12 tables mapped with proper types, indexes, and foreign keys.

---

### CHIP API-03 — Alembic Migration Engine & Baseline Migration

**Objective:** Configure Alembic for automated schema migration management and generate the initial baseline migration script (TC-API-01).

**Why:** Allows database schemas to evolve safely across development, testing, and production environments without data loss.

**Dependencies:** CHIP API-02.

**Files to create:**
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`

**Implementation:**
1. Configure `alembic/env.py` to import `Base.metadata` from `app.models`.
2. Generate baseline migration: `alembic revision --autogenerate -m "initial 12-table schema"`.
3. Verify migration script generates all tables, indexes, and foreign key constraints cleanly.
4. Test upgrade and downgrade: `alembic upgrade head` and `alembic downgrade base`.

**Acceptance Criteria:**
- Clean migration execution on both SQLite and PostgreSQL (TC-API-01).

---

### CHIP API-04 — Certificate Verification Pipeline Orchestrator Service

**Objective:** Implement the central `VerificationPipelineOrchestrator` that executes the full 10-stage analysis sequentially on an uploaded certificate, updating job progress in the database (FR-API-02).

**Why:** Coordinates the execution of all standalone modules (Ingestion -> Preprocessing -> OCR -> Text Consistency -> Forensics -> Template Matching -> ML -> DL -> Fusion -> Explainability -> Report) in a robust, error-tolerant sequence.

**Dependencies:** Phases 03 through 13.

**Files to create:**
- `backend/app/services/pipeline_orchestrator.py`

**Implementation:**
1. Implement `run_pipeline(certificate_id: UUID, db: Session) -> None`:
   - Stage 1: Load certificate record, update `job_status = "PROCESSING"`, `job_progress = 10`.
   - Stage 2: Execute Ingestion & Validation (Phase 03).
   - Stage 3: Execute Preprocessing (Phase 04) -> `job_progress = 25`.
   - Stage 4: Execute OCR & Field Extraction (Phase 05) -> `job_progress = 40`.
   - Stage 5: Parallel/Sequential execution of:
     - Text Consistency Analysis (Phase 06)
     - Image Forensics (Phase 07) -> `job_progress = 60`.
   - Stage 6: Execute Template Matching & Record Verification (Phase 08) -> `job_progress = 70`.
   - Stage 7: Execute ML Baseline & DL Visual CNN Inference (Phases 09 & 10) -> `job_progress = 80`.
   - Stage 8: Execute Multimodal Fusion & Decision Engine (Phase 11) -> `job_progress = 90`.
   - Stage 9: Generate Explainability & Unified Overlays (Phase 12).
   - Stage 10: Compile PDF and JSON Reports (Phase 13) -> `job_status = "COMPLETED"`, `job_progress = 100`.
2. Error handling:
   - If any unrecoverable exception occurs: catch error, rollback uncommitted DB transactions, record `job_status = "FAILED"`, `job_error = str(e)`, and log detailed stack trace.

**Acceptance Criteria:**
- Orchestrates complete end-to-end pipeline and updates database progress dynamically.

---

### CHIP API-05 — Asynchronous Task Runner Integration

**Objective:** Decouple pipeline execution from the HTTP request cycle using FastAPI `BackgroundTasks` (for local dev) with a pluggable adapter for Redis/Celery (for production scaling) (FR-API-02, NFR-04).

**Why:** Certificate verification takes 8–15 seconds. Running in the background allows the upload endpoint to respond immediately with HTTP 202 Accepted and a job polling ID.

**Dependencies:** CHIP API-04.

**Files to create:**
- `backend/app/services/task_runner.py`

**Implementation:**
1. Implement `AsyncTaskRunner` interface:
   ```python
   class AsyncTaskRunner(ABC):
       @abstractmethod
       def dispatch_pipeline(self, certificate_id: UUID) -> None:
           pass
   ```
2. Implement `FastAPIBackgroundTaskRunner` using `BackgroundTasks`:
   - Dispatches `run_pipeline` in a background thread using a dedicated database session.
3. Expose configuration switch: `TASK_RUNNER_BACKEND: Literal["fastapi", "redis"] = "fastapi"`.

**Acceptance Criteria:**
- HTTP upload endpoint returns immediately while pipeline runs asynchronously in the background.

---

### CHIP API-06 — Certificate Management REST Endpoints

**Objective:** Implement RESTful endpoints under `/api/v1/certificates` for uploading, polling status, fetching detailed results, listing verification history, and deleting certificates (FR-API-03).

**Why:** Core API interface used by the frontend to submit documents and display real-time verification progress.

**Dependencies:** CHIP API-05.

**Files to create:**
- `backend/app/api/v1/endpoints/certificates.py`
- `backend/app/schemas/certificate.py`

**Implementation:**
1. `POST /api/v1/certificates/upload`:
   - Accepts multipart file upload.
   - Saves file, computes SHA-256, creates `certificate` record with `job_status = "PENDING"`.
   - Dispatches background pipeline job via `AsyncTaskRunner`.
   - Returns HTTP 202 Accepted with `{"certificate_id": uuid, "status": "PENDING", "poll_url": "/api/v1/certificates/{id}/status"}`.
2. `GET /api/v1/certificates/{id}/status`:
   - Returns lightweight JSON: `{"id": uuid, "status": "PROCESSING", "progress": 60, "error": null}`.
3. `GET /api/v1/certificates/{id}`:
   - Returns comprehensive verification details once completed (fields, scores, verdict, findings).
4. `GET /api/v1/certificates`:
   - Paginated list of uploaded certificates with filtering by verdict, date range, and institution.
5. `DELETE /api/v1/certificates/{id}`:
   - Soft-deletes certificate and cleans up associated files.

**Acceptance Criteria:**
- Full CRUD operations functional with input validation and HTTP status codes (TC-API-02, TC-API-03).

---

### CHIP API-07 — Report Retrieval & Verification REST Endpoints

**Objective:** Implement public and authenticated endpoints under `/api/v1/reports` for retrieving report data, downloading PDF/JSON files, and verifying report authenticity via QR code payload (FR-REP-03).

**Why:** Allows users and employers to download reports and verify that physical reports have not been altered.

**Dependencies:** Phase 13 Report System.

**Files to create:**
- `backend/app/api/v1/endpoints/reports.py`

**Implementation:**
1. `GET /api/v1/reports/{report_id}`: Returns full JSON verification report.
2. `GET /api/v1/reports/{report_id}/pdf`: Streams downloadable PDF report with attachment header.
3. `GET /api/v1/reports/{report_id}/verify`:
   - Public endpoint (no auth required) called by QR code scanners.
   - Verifies digital HMAC signature against current database state.
   - Returns verification confirmation: `{"valid": true, "certificate_id": uuid, "verdict": "AUTHENTIC", "issued_at": timestamp}`.

**Acceptance Criteria:**
- Serves reports and verifies QR code authenticity tokens reliably.

---

### CHIP API-08 — Institution, Template & Record REST Endpoints

**Objective:** Implement CRUD endpoints under `/api/v1/institutions` for managing registered universities, uploading master certificate templates, and bulk-importing student records (FR-API-04).

**Why:** Allows university partners and administrators to onboard institutions and populate the ground-truth databases required for Tier 1 and Tier 2 matching.

**Dependencies:** Phase 08 Template & Records.

**Files to create:**
- `backend/app/api/v1/endpoints/institutions.py`
- `backend/app/schemas/institution.py`

**Implementation:**
1. `POST /api/v1/institutions`: Register new university.
2. `GET /api/v1/institutions`: List registered universities with active template counts.
3. `POST /api/v1/institutions/{id}/templates`: Upload master template image and ROI metadata.
4. `POST /api/v1/institutions/{id}/records/bulk`: Upload CSV of authorized student records.

**Acceptance Criteria:**
- Enables complete administrative onboarding of universities and verification datasets.

---

### CHIP API-09 — Centralized Audit Logging Interceptor & Service

**Objective:** Implement an automated audit logging service and FastAPI middleware/dependency that records every critical action in the `audit_log` database table (FR-API-05).

**Why:** Satisfies legal, security, and institutional compliance requirements. Every upload, verification view, report download, and template edit must have an immutable audit trail.

**Dependencies:** CHIP API-02.

**Files to create:**
- `backend/app/services/audit_service.py`
- `backend/app/api/v1/endpoints/audit.py`

**Implementation:**
1. Implement `log_action(db: Session, action: str, user_id: Optional[UUID], certificate_id: Optional[UUID], ip_address: str, details: dict) -> None`:
   - Writes record to `audit_log` table:
     `AuditLog(action=action, user_id=user_id, certificate_id=certificate_id, ip_address=ip_address, details_json=details)`.
   - Commits independently of main request transaction.
2. Trigger audit logs on:
   - `CERTIFICATE_UPLOADED`
   - `VERIFICATION_COMPLETED`
   - `REPORT_DOWNLOADED_PDF`
   - `TEMPLATE_REGISTERED`
   - `USER_LOGIN`
3. Expose `GET /api/v1/audit-logs` endpoint (restricted to Admin role).

**Acceptance Criteria:**
- Automatically logs all critical events with client IP and timestamps (TC-API-05).

---

### CHIP API-10 — Error Handling, CORS, Rate Limiting & OpenAPI Documentation

**Objective:** Configure production middleware in FastAPI: custom exception handlers with standardized error JSON, CORS for the React frontend, slowapi rate limiting, and rich OpenAPI Swagger documentation.

**Why:** Hardens the API against abuse, ensures clean frontend error communication, and provides interactive API documentation.

**Dependencies:** Phase 01 Foundation.

**Files to modify:**
- `backend/app/main.py`
- `backend/app/core/exceptions.py`

**Implementation:**
1. Standardize error JSON envelope:
   ```json
   {
     "error": {
       "code": "INSUFFICIENT_RESOLUTION",
       "message": "Image resolution 640x480 is too low. Minimum required is 800x600.",
       "status_code": 422,
       "timestamp": "2026-09-15T10:00:00Z"
     }
   }
   ```
2. Configure CORS: Allow frontend origins (`http://localhost:5173`, `http://127.0.0.1:5173`).
3. Configure rate limiting: 60 requests/minute for standard endpoints, 10 uploads/minute for certificate upload endpoint using `slowapi`.
4. Enrich OpenAPI metadata: Title, description, tags, version, and response model documentation.

**Acceptance Criteria:**
- All API errors return standardized JSON envelopes; Swagger UI displays complete API specs.

---

### CHIP API-11 — Application Health & System Status Endpoints

**Objective:** Implement comprehensive diagnostic health endpoints at `/health` and `/api/v1/health/detailed` verifying DB connectivity, disk storage, Poppler status, and model weight residency.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `backend/app/api/v1/endpoints/health.py`

**Acceptance Criteria:**
- Returns HTTP 200 and subsystem statuses when all components are operational.

---

### CHIP API-12 — Unit Tests: Database Migrations and Certificate CRUD

**Objective:** Test Alembic migration execution, table creation, and verify certificate CRUD API endpoints (TC-API-01, TC-API-02).

**Dependencies:** CHIP API-02, CHIP API-03, CHIP API-06.

**Files to create:**
- `backend/tests/integration/test_database_migrations.py`
- `backend/tests/integration/test_certificate_endpoints.py`

**Implementation:**
1. Test `test_alembic_migrations_apply_cleanly()`: Apply all migrations to fresh test SQLite/PostgreSQL DB; assert all 12 tables exist (TC-API-01).
2. Test `test_certificate_upload_and_status_polling()`: Upload test image; assert HTTP 202, valid UUID, and status polling returns valid JSON (TC-API-02).
3. Test `test_certificate_list_pagination()`: Verify pagination parameters `page` and `limit`.

**Acceptance Criteria:**
- 100% test pass rate across migration and CRUD test cases.

---

### CHIP API-13 — Unit Tests: Async Pipeline, Rollbacks & Audit Logging

**Objective:** Test async background pipeline execution, database transaction rollbacks on simulated failures, and verify audit log generation (TC-API-03, TC-API-04, TC-API-05).

**Dependencies:** CHIP API-04, CHIP API-05, CHIP API-09.

**Files to create:**
- `backend/tests/integration/test_async_pipeline.py`
- `backend/tests/integration/test_audit_logging.py`

**Implementation:**
1. Test `test_async_pipeline_executes_to_completion()`: Trigger pipeline in background; poll until `job_status == "COMPLETED"`; assert all result tables populated (TC-API-03).
2. Test `test_database_rollback_on_pipeline_error()`: Inject simulated fault in OCR; assert transaction rolls back cleanly and `job_status == "FAILED"` (TC-API-04).
3. Test `test_audit_log_persists_on_upload()`: Verify upload creates corresponding entry in `audit_log` table (TC-API-05).

**Acceptance Criteria:**
- All tests pass, validating async pipeline, failure rollbacks, and audit logging.

---

## 9. Implementation Order and Dependencies

```
CHIP API-01 (DB Connection & Session Management)
    ↓
CHIP API-02 (12-Table SQLAlchemy Models)
    ↓
CHIP API-03 (Alembic Migration Engine) ─────┐
    ↓                                      │
CHIP API-04 (Pipeline Orchestrator)        │
    ↓                                      │
CHIP API-05 (Async Task Runner)            │
    ↓                                      │
├── CHIP API-06 (Certificate CRUD Endpoints)
├── CHIP API-07 (Report REST Endpoints)    │
├── CHIP API-08 (Institution Endpoints)    │
└── CHIP API-09 (Audit Logging Service) ◄──┘
    ↓
CHIP API-10 (Error Handling, CORS, Docs)
    ↓
CHIP API-11 (Health & Diagnostics)
    ↓
CHIP API-12 & CHIP API-13 (Integration Tests)
```

---

## 10. Phase Completion Checklist

- [ ] SQLAlchemy 2.0 connection engine configured with connection pooling for SQLite and PostgreSQL.
- [ ] All 12 tables mapped with strict foreign key constraints, cascade rules, and indexes.
- [ ] Alembic migration baseline executes cleanly without schema discrepancies.
- [ ] Pipeline orchestrator coordinates all 10 analytical stages with database progress tracking.
- [ ] Asynchronous task runner decouples upload responses from 10-second pipeline execution.
- [ ] Certificate endpoints support upload, status polling, details retrieval, and pagination.
- [ ] Report endpoints support JSON data retrieval, PDF streaming, and public QR verification.
- [ ] Institution endpoints enable template registration and CSV student record bulk imports.
- [ ] Centralized audit logger permanently records all uploads, downloads, and verifications.
- [ ] CORS, rate limiting, and standardized error JSON envelopes configured.
- [ ] Test cases TC-API-01 through TC-API-05 passing with 100% success rate.
