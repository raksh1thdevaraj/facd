# Phase 18 — End-to-End Integration

## 1. Purpose

Wire together all individually developed subsystems (Frontend SPA, Backend REST API, Database, Ingestion, Preprocessing, PaddleOCR, Text Consistency, Image Forensics, Template Matching, ML Baseline, DL Visual CNN, Multimodal Fusion, Explainability, and Report Generation) into a unified, resilient, production-ready system. This phase tests the complete end-to-end workflow, validates error resilience and graceful degradation under partial failures, tunes concurrent throughput, and optimizes pipeline latency to ensure complete verification finishes within $\le 15$ seconds per certificate (NFR-03).

## 2. Why This Phase Exists

Up to this point, individual modules were built and tested in relative isolation. In real-world operation:
- All 10 analytical stages must pass intermediate data tensors, bounding boxes, and database records seamlessly without type mismatches or serialization errors.
- Unhandled edge cases (e.g. an unreadable scanned seal, an unknown institution with no registered template, or an unexpected OCR character crash) must not cause the entire verification request to fail; the system must gracefully degrade and report available evidence.
- Multiple users uploading certificates simultaneously must not cause GPU out-of-memory errors, database deadlocks, or worker thread starvation.
- Latency across all stages must be profiled, optimized, and budgeted to meet the strict $\le 15$ second end-to-end turnaround requirement (NFR-03).

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-INT-01** | Seamless end-to-end workflow execution from user upload to report download | Integrated pipeline orchestrator connecting UI, API, worker, and database |
| **FR-INT-02** | Fault-tolerant graceful degradation under partial component failure | Fallback handlers ensuring report generation succeeds even if optional checks fail |
| **FR-INT-03** | End-to-end latency optimization ($\le 15$ seconds per document) | Asynchronous task scheduling, memory tensor reuse, and CPU multi-threading |
| **FR-INT-04** | Concurrency and race-condition safety under multi-user uploads | Scoped database sessions, UUID file isolation, and worker queue limits |
| **NFR-03** | Performance (Total end-to-end turnaround time $\le 15$ seconds) | Strict per-stage execution budgets and profiling |
| **NFR-04** | Scalability & Concurrency | Handled via asynchronous job dispatch and connection pooling |
| **TC-E2E-01** | Full workflow test: Genuine certificate upload to authentic verdict | Chip INT-11 |
| **TC-E2E-02** | Full workflow test: Manipulated certificate to manipulated verdict & highlights | Chip INT-11 |
| **TC-E2E-03** | Full workflow test: Multi-page PDF upload and page-1 processing | Chip INT-12 |
| **TC-E2E-04** | Graceful degradation test: Unregistered template fallback | Chip INT-12 |
| **TC-E2E-05** | Concurrent multi-user upload stress test | Chip INT-12 |

## 4. Inputs

- Frontend single-page application from Phase 16.
- Backend REST API and database from Phases 14 & 15.
- Complete analytical pipeline modules from Phases 03 through 13.
- Synthetic and real-world test certificate suites from Phase 02.

## 5. Outputs

- Fully integrated, running application with frontend connected to backend API.
- End-to-end automated integration test suite (`tests/e2e/`).
- Pipeline latency profiling report (`ml/reports/pipeline_latency_profile.json`).
- Verified graceful degradation and concurrency behavior.

## 6. Dependencies

- **Previous phases:** Phases 01 through 17 (Integrates entire project).
- **Libraries:** `pytest`, `pytest-asyncio`, `httpx`, `playwright` (or Selenium for E2E browser tests), `locust` (for concurrency load tests).

## 7. Files and Folder Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── pipeline_orchestrator.py   # Enhanced with fallbacks & stage timeouts
│   │   └── fallback_handler.py        # Graceful degradation rules
│   └── core/
│       └── profiler.py                # Per-stage execution timing profiler
└── tests/
    └── e2e/
        ├── test_full_genuine_flow.py  # End-to-end genuine workflow
        ├── test_full_forgery_flow.py  # End-to-end manipulated workflow
        ├── test_pdf_workflow.py       # Multi-page PDF handling
        ├── test_graceful_degradation.py # Fault injection & fallback recovery
        └── test_concurrent_load.py    # Multi-user concurrency testing
```

---

## 8. Implementation Chips

---

### CHIP INT-01 — Pipeline Data Bus & Shared Execution Context

**Objective:** Define a strongly-typed, memory-resident `PipelineExecutionContext` that flows through all 10 analysis stages, carrying intermediate arrays, extracted tokens, scores, and timing metrics without redundant disk re-reads.

**Why:** Reading and writing intermediate PNG images from disk between every step adds 3–5 seconds of disk I/O latency. A shared memory context allows downstream modules to read in-memory NumPy arrays directly, writing to disk only when persisting permanent artifacts.

**Dependencies:** Phases 03 through 13.

**Files to create:**
- `backend/app/services/pipeline_context.py`

**Implementation:**
1. Define `PipelineExecutionContext`:
   ```python
   @dataclass
   class PipelineExecutionContext:
       certificate_id: UUID
       user_id: Optional[UUID]
       raw_image_path: Path
       raw_image: np.ndarray
       enhanced_image: Optional[np.ndarray] = None
       binarized_image: Optional[np.ndarray] = None
       ingestion_doc: Optional[IngestedDocument] = None
       ocr_fields: Optional[ExtractedCertificateFields] = None
       ocr_tokens: List[OCRToken] = field(default_factory=list)
       text_result: Optional[TextConsistencyResult] = None
       forensic_result: Optional[ForensicAnalysisResult] = None
       template_result: Optional[TemplateMatchResult] = None
       tier_result: Optional[TierClassification] = None
       record_result: Optional[RecordVerificationResult] = None
       tabular_features: Optional[np.ndarray] = None
       tabular_prediction: Optional[PredictionResult] = None
       visual_prediction: Optional[VisualPredictionResult] = None
       final_decision: Optional[FinalVerificationDecision] = None
       explainability_report: Optional[ExplainabilityReport] = None
       final_report: Optional[FullVerificationReport] = None
       stage_timings_ms: Dict[str, float] = field(default_factory=dict)
   ```
2. Pass context sequentially through all stage processors.

**Acceptance Criteria:**
- Eliminates redundant image re-reading; accelerates pipeline throughput.

---

### CHIP INT-02 — Stage Timeout Guards & Fault Isolation

**Objective:** Wrap every individual pipeline stage in a dedicated timeout guard (e.g. max 4.0s for OCR, max 3.0s for forensics) and exception boundary to prevent a slow or failing module from freezing the entire verification job.

**Why:** If an external library encounters an infinite loop or high-order polynomial explosion on an adversarial image, the stage must abort cleanly within its budget rather than hanging the worker thread indefinitely.

**Dependencies:** CHIP INT-01.

**Files to modify:**
- `backend/app/services/pipeline_orchestrator.py`

**Implementation:**
1. Implement stage wrapper:
   ```python
   def execute_stage(
       stage_name: str,
       timeout_seconds: float,
       stage_fn,
       context: PipelineExecutionContext,
       *args,
       **kwargs,
   ):
       start_time = time.perf_counter()
       try:
           # Execute with timeout guard
           result = run_with_timeout(stage_fn, timeout_seconds, context, *args, **kwargs)
           context.stage_timings_ms[stage_name] = (
               time.perf_counter() - start_time
           ) * 1000.0
           return result
       except TimeoutError:
           logger.warning(
               f"Stage '{stage_name}' timed out after {timeout_seconds}s. Proceeding with fallback."
           )
           context.stage_timings_ms[stage_name] = timeout_seconds * 1000.0
           return get_fallback_result(stage_name, context)
       except Exception as e:
           logger.error(f"Stage '{stage_name}' failed with error: {e}. Applying fallback.")
           return get_fallback_result(stage_name, context)
   ```

**Acceptance Criteria:**
- Isolates stage faults and enforces strict per-stage execution time limits.

---

### CHIP INT-03 — Graceful Degradation & Fallback Strategy Engine

**Objective:** Implement intelligent fallback logic that enables the verification system to produce a valid, helpful assessment report even when optional subsystems fail or lack data (FR-INT-02, TC-E2E-04).

**Why:** In the real world, templates are not registered for every college, and some mobile photos lack EXIF data. The system must adapt dynamically:
- If Template Matching fails (unknown university) -> Fallback to Tier 2/3 classification based solely on visual CNN, forensic ELA, and typography checks.
- If Deep Learning Visual model fails -> Fallback to ML Baseline tabular score.
- If SIFT Copy-Move detection encounters too few keypoints -> Mark clone score as neutral (1.0) and proceed with ELA.
- If OCR fails to parse candidate name -> Flag field as unextracted, but continue visual tampering analysis.

**Dependencies:** CHIP INT-02.

**Files to create:**
- `backend/app/services/fallback_handler.py`

**Implementation:**
1. Implement `get_fallback_result(stage_name, context)` returning calibrated neutral defaults.
2. In `FinalVerificationDecision`, append an explicit system advisory note:
   `"Notice: Verification completed with degraded confidence due to missing institutional master template. Results reflect visual and textual forensics only."`

**Acceptance Criteria:**
- System produces complete verification reports even under partial component failures (TC-E2E-04).

---

### CHIP INT-04 — End-to-End Latency Budget & Profiling Optimization

**Objective:** Profile execution time across all 10 stages on representative certificate images, optimizing bottlenecks to guarantee total end-to-end turnaround is strictly $\le 15$ seconds (FR-INT-03, NFR-03).

**Why:** Enforces the core performance requirement (NFR-03). A verification taking 30–40 seconds degrades user experience and exhausts server thread pools.

**Dependencies:** CHIP INT-01.

**Implementation:**
1. Establish stage time budgets:
   - Stage 1: Ingestion & Validation: $\le 1.0$s
   - Stage 2: Preprocessing (Deskew/CLAHE): $\le 2.5$s
   - Stage 3: OCR Extraction (PaddleOCR): $\le 3.5$s
   - Stage 4: Text Consistency Analysis: $\le 1.5$s
   - Stage 5: Image Forensics (ELA & SIFT): $\le 2.5$s
   - Stage 6: Template & Record Matching: $\le 1.0$s
   - Stage 7: ML & DL Model Inference: $\le 0.8$s
   - Stage 8: Multimodal Fusion & Decision: $\le 0.2$s
   - Stage 9: Explainability & Overlays: $\le 1.0$s
   - Stage 10: PDF/JSON Report Compilation: $\le 1.0$s
   - **Total Budget:** $\le 15.0$ seconds (Target typical: $8–12$ seconds).
2. Optimizations applied:
   - Run Stage 4 (Text Consistency) and Stage 5 (Forensics) concurrently in separate threads (`concurrent.futures.ThreadPoolExecutor`).
   - Pre-scale images before SIFT keypoint matching.
   - Use MKL-DNN acceleration for PaddleOCR.
   - Use dynamic INT8 quantized weights for Visual CNN.

**Acceptance Criteria:**
- Total end-to-end turnaround time on 300 DPI A4 certificate is $< 12.0$ seconds (well within $\le 15$s budget).

---

### CHIP INT-05 — Concurrency, Session Scoping & Deadlock Prevention

**Objective:** Harden database transactions, thread-local sessions, and temporary file paths to support multiple simultaneous certificate verifications without race conditions or memory corruption (FR-INT-04, NFR-04).

**Why:** When multiple users upload certificates at the same moment, shared database sessions or global variable mutations can cause data crossover (User A sees User B's certificate report) or SQLite locking deadlocks.

**Dependencies:** Phase 14 Backend API.

**Files to modify:**
- `backend/app/services/pipeline_orchestrator.py`

**Implementation:**
1. Thread safety rules:
   - Every background job instantiates its own dedicated `SessionLocal()` database session.
   - All filesystem operations write exclusively to UUID-isolated paths: `storage/{category}/{certificate_id}_*.ext`.
   - Never mutate global configuration or model objects in inference threads.
2. Connection pool sizing:
   - Configure SQLAlchemy connection pool with `max_overflow = 10` and `pool_timeout = 30`.

**Acceptance Criteria:**
- Successfully processes 5 concurrent uploads simultaneously with zero cross-talk or lock contention (TC-E2E-05).

---

### CHIP INT-06 — Frontend-Backend Integration & Error Boundary Wiring

**Objective:** Wire all frontend services, React Query / hooks, and error boundaries to live backend API endpoints, testing real network roundtrips across all user flows.

**Why:** Ensures API schemas, JSON payload naming (snake_case vs camelCase), HTTP status codes, and network error handling match perfectly between browser and server.

**Dependencies:** Phase 14 Backend, Phase 16 Frontend.

**Files to modify:**
- `frontend/src/services/api.ts`
- `frontend/src/App.tsx`

**Implementation:**
1. Global React Error Boundary: Catch unhandled UI errors and display a recovery screen with "Reload" and "Report Issue" buttons.
2. Network error toast notifications: Display friendly messages on connection loss or 500 server errors.
3. Verify all routes end-to-end: `/` -> `/upload` -> `/results/:id` -> `/history` -> `/admin`.

**Acceptance Criteria:**
- Complete frontend UI navigates and updates in real-time against live backend server.

---

### CHIP INT-07 — Automated End-to-End Test Suite Setup

**Objective:** Set up an automated end-to-end testing harness using `pytest` and `httpx.AsyncClient` that executes complete verification lifecycles from upload to report download.

**Why:** Guarantees regressions in any individual module are caught immediately by full-lifecycle automated tests.

**Dependencies:** CHIP INT-01 through CHIP INT-06.

**Files to create:**
- `backend/tests/e2e/conftest.py`

**Implementation:**
1. Configure test fixtures:
   - Clean temporary test database.
   - Pre-loaded genuine certificate sample image.
   - Pre-loaded manipulated certificate sample image (altered name and grade).
   - Test admin and verifier JWT authentication tokens.

**Acceptance Criteria:**
- Test harness provides isolated, reproducible test environments for end-to-end tests.

---

### CHIP INT-08 — Pipeline Latency Profiling Tool

**Objective:** Build a diagnostic profiling script (`backend/scripts/profile_pipeline.py`) that benchmarks and logs millisecond execution times for all 10 stages across 20 test certificate samples.

**Why:** Enables engineers to identify performance regressions during CI/CD builds and optimize slow stages.

**Dependencies:** CHIP INT-04.

**Files to create:**
- `backend/scripts/profile_pipeline.py`

**Acceptance Criteria:**
- Generates detailed JSON latency profile and prints execution breakdown table.

---

### CHIP INT-09 — System Verification Smoke Test Script

**Objective:** Create a standalone shell script (`backend/scripts/smoke_test.sh`) that verifies API health, database migrations, model loading, and runs a test certificate verification in $< 30$ seconds.

**Why:** Gives developers and system administrators a 1-command verification that the entire integrated stack is operational.

**Dependencies:** CHIP INT-06.

**Files to create:**
- `backend/scripts/smoke_test.sh`

**Acceptance Criteria:**
- Shell script exits with code 0 only if all subsystems pass verification checks.

---

### CHIP INT-10 — Orphan File Garbage Collection Background Routine

**Objective:** Implement a daily background cleanup task that purges temporary scratch files and uncompleted uploads older than 48 hours to prevent disk exhaustion.

**Dependencies:** Phase 14 Backend API.

**Files to create:**
- `backend/app/services/cleanup_service.py`

**Acceptance Criteria:**
- Removes orphaned scratch files without affecting completed certificate records.

---

### CHIP INT-11 — End-to-End Tests: Full Genuine & Forgery Workflows

**Objective:** Execute complete end-to-end automated verification workflows on both a pristine genuine certificate and a manipulated certificate, verifying outputs from upload to PDF report (TC-E2E-01, TC-E2E-02).

**Dependencies:** CHIP INT-07.

**Files to create:**
- `backend/tests/e2e/test_full_genuine_flow.py`
- `backend/tests/e2e/test_full_forgery_flow.py`

**Implementation:**
1. Test `test_genuine_certificate_e2e_workflow()` (TC-E2E-01):
   - Upload genuine certificate via `POST /certificates/upload`.
   - Poll status until `COMPLETED`.
   - Assert final verdict is `AUTHENTIC`.
   - Assert authenticity score $\ge 0.85$.
   - Assert PDF report generated and downloadable.
2. Test `test_manipulated_certificate_e2e_workflow()` (TC-E2E-02):
   - Upload tampered certificate with spliced name and altered CGPA.
   - Poll status until `COMPLETED`.
   - Assert final verdict is `MANIPULATED`.
   - Assert authenticity score $< 0.60$.
   - Assert anomaly bounding boxes contain tampered name coordinates.
   - Assert Grad-CAM and forensic heatmaps generated.

**Acceptance Criteria:**
- Both workflows execute to completion and assign correct verdicts (TC-E2E-01, TC-E2E-02).

---

### CHIP INT-12 — End-to-End Tests: Multi-Page PDF, Fallback & Concurrency

**Objective:** Test multi-page PDF processing, graceful degradation under partial failures, and multi-user concurrent upload execution (TC-E2E-03, TC-E2E-04, TC-E2E-05).

**Dependencies:** CHIP INT-07.

**Files to create:**
- `backend/tests/e2e/test_pdf_workflow.py`
- `backend/tests/e2e/test_graceful_degradation.py`
- `backend/tests/e2e/test_concurrent_load.py`

**Implementation:**
1. Test `test_multipage_pdf_workflow()`: Upload 3-page PDF transcript; assert page 1 rasterized at 300 DPI and analyzed successfully (TC-E2E-03).
2. Test `test_unregistered_template_graceful_fallback()`: Upload certificate from unregistered college; assert pipeline completes successfully with Tier 2/3 classification and advisory note (TC-E2E-04).
3. Test `test_concurrent_multi_user_uploads()`: Submit 5 simultaneous certificate uploads asynchronously; assert all 5 complete successfully without errors or cross-contamination (TC-E2E-05, NFR-04).
4. Assert total turnaround time for each verification is $\le 15$ seconds (NFR-03).

**Acceptance Criteria:**
- All integration and stress tests pass with 100% success rate.

---

## 9. Implementation Order and Dependencies

```
CHIP INT-01 (Shared Pipeline Context)
    ↓
CHIP INT-02 (Stage Timeout Guards)
    ↓
CHIP INT-03 (Graceful Degradation Engine)
    ↓
CHIP INT-04 (Latency Optimization Budget) ──┐
    ↓                                      │
CHIP INT-05 (Concurrency & Thread Safety) │
    ↓                                      │
CHIP INT-06 (Frontend-Backend Wiring)      │
    ↓                                      │
CHIP INT-07 (E2E Test Harness Setup) ◄─────┘
    ↓
CHIP INT-08 (Profiler Tool) & CHIP INT-09 (Smoke Test)
    ↓
CHIP INT-10 (Garbage Collection)
    ↓
CHIP INT-11 & CHIP INT-12 (Full End-to-End Automated Tests)
```

---

## 10. Phase Completion Checklist

- [ ] Shared pipeline context eliminates redundant disk I/O, passing in-memory arrays across stages.
- [ ] Individual stage timeout guards isolate faults and prevent worker thread hangs.
- [ ] Graceful degradation engine ensures valid report generation even if optional modules fail.
- [ ] Total end-to-end verification latency profiled and optimized to $< 12.0$s (well below $\le 15$s budget).
- [ ] Thread safety and UUID isolation tested under 5 concurrent simultaneous uploads.
- [ ] Frontend SPA seamlessly connects to live backend API across all routes.
- [ ] Full genuine certificate workflow achieves `AUTHENTIC` verdict and downloads PDF report.
- [ ] Full manipulated certificate workflow detects tampering, assigns `MANIPULATED`, and highlights evidence.
- [ ] Multi-page PDFs rasterize and process page 1 accurately at 300 DPI.
- [ ] Smoke test script verifies entire integrated system health in $< 30$ seconds.
- [ ] Test cases TC-E2E-01 through TC-E2E-05 passing with 100% success rate.
