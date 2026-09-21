# Phase 20 — Deployment & Security

## 1. Purpose

Implement the production containerization, infrastructure orchestration, security hardening, and Continuous Integration (CI/CD) automation. This subsystem packages the FastAPI backend (with Poppler, PaddleOCR, and PyTorch runtimes), the React frontend (compiled and served via an optimized Nginx web server), the PostgreSQL 15 database, and Redis into an orchestrated multi-container architecture via Docker Compose. It applies production security headers, enforces non-root container isolation, isolates secrets, and sets up GitHub Actions automated CI pipelines.

## 2. Why This Phase Exists

A complex multi-technology AI application (Python + PyTorch + PaddleOCR + Poppler + Node + PostgreSQL + Redis) cannot rely on "it works on my machine":
- System libraries like `poppler-utils` and `libgl1` have varying package names and paths across macOS, Ubuntu, and Windows. Containerizing with Docker guarantees identical runtime environments across all systems.
- Production security requires running as non-root users, setting Content-Security-Policy (CSP) and HTTP Strict Transport Security (HSTS) headers, restricting CORS, and managing database credentials through isolated environment files.
- Nginx provides reverse proxying, client upload buffering (enforcing 10MB limit at the network edge), SSL termination, and static asset caching.
- Continuous Integration (CI) automatically runs linters, unit tests, coverage checks, and container builds on every commit.

## 3. Requirements Covered

| Requirement | Description | Implementation in this Phase |
|---|---|---|
| **FR-DEP-01** | Production multi-stage Dockerfiles for backend and frontend | Multi-stage Dockerfiles optimizing image size and runtime dependencies |
| **FR-DEP-02** | Multi-container orchestration using Docker Compose | `docker-compose.yml` coordinating backend, frontend, PostgreSQL, and Redis |
| **FR-DEP-03** | Nginx reverse proxy configuration with security headers and SSL | Nginx config with HSTS, CSP, X-Frame-Options, and 10MB upload limit |
| **FR-DEP-04** | Secrets management and environment configuration | `.env.production` isolation, zero hardcoded credentials, non-root users |
| **FR-DEP-05** | Automated Continuous Integration (CI) pipeline via GitHub Actions | GitHub Actions workflow executing linting, tests, coverage, and Docker builds |
| **NFR-02** | Production Security & Hardening | Non-root containers, secure headers, CORS restriction, token revocation |
| **NFR-08** | Maintainability & Reproducible Deployment | One-command startup via `docker compose up --build` |
| **TC-DEP-01** | Docker container builds test (backend, frontend, database) | Chip DEP-11 |
| **TC-DEP-02** | Docker compose orchestration and service communication test | Chip DEP-11 |
| **TC-DEP-03** | Nginx reverse proxy and security headers test | Chip DEP-12 |
| **TC-DEP-04** | Secrets isolation and environment configuration test | Chip DEP-12 |
| **TC-DEP-05** | CI/CD GitHub Actions workflow test | Chip DEP-12 |

## 4. Inputs

- Backend application codebase from Phase 14.
- Frontend application codebase from Phase 16.
- Production environment variable definitions (`.env.example`).
- Model weight checkpoints from Phases 09, 10, and 11.

## 5. Outputs

- Backend Dockerfile (`backend/Dockerfile`).
- Frontend Dockerfile (`frontend/Dockerfile`) & Nginx configuration (`frontend/nginx.conf`).
- Docker Compose configuration (`docker-compose.yml` and `docker-compose.prod.yml`).
- Nginx gateway configuration (`nginx/nginx.conf`).
- GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- One-command deployment scripts (`scripts/deploy.sh`, `scripts/docker_clean.sh`).

## 6. Dependencies

- **Previous phases:** Phases 01 through 19.
- **External tools:** Docker Engine 24+, Docker Compose v2, GitHub Actions.

## 7. Files and Folder Structure

```
.
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI workflow
├── docker-compose.yml                 # Local development & full-stack composition
├── docker-compose.prod.yml            # Production deployment overrides
├── nginx/
│   ├── nginx.conf                     # Production reverse proxy gateway
│   └── ssl/                           # Self-signed dev certs / Let's Encrypt mount
├── backend/
│   ├── Dockerfile                     # Multi-stage Python 3.11 container
│   ├── .dockerignore
│   └── entrypoint.sh                  # Database migration & server startup
├── frontend/
│   ├── Dockerfile                     # Multi-stage Node build -> Nginx
│   ├── .dockerignore
│   └── nginx.conf                     # SPA routing & static asset caching
└── scripts/
    ├── deploy.sh                      # Production deployment launcher
    └── init_ssl.sh                    # SSL certificate setup helper
```

---

## 8. Implementation Chips

---

### CHIP DEP-01 — Backend Multi-Stage Production Dockerfile

**Objective:** Build a multi-stage, production-hardened Dockerfile for the Python/FastAPI backend that installs system dependencies (`poppler-utils`, `libgl1`, `libgomp1`), caches Python dependencies, runs as a non-root user, and packages model weights (FR-DEP-01).

**Why:** Minimizes final Docker image size, speeds up build caching, and satisfies container security best practices by eliminating root execution vulnerabilities.

**Dependencies:** Phase 01 (Foundation), Phase 14 (Backend).

**Files to create:**
- `backend/Dockerfile`
- `backend/.dockerignore`
- `backend/entrypoint.sh`

**Implementation:**
1. Stage 1: Builder
   - Base image: `python:3.11-slim-bookworm`
   - Install build tools: `gcc`, `g++`, `libpq-dev`.
   - Install Python dependencies into virtual environment `/opt/venv` using `pip install --no-cache-dir -r requirements.txt`.
2. Stage 2: Runtime
   - Base image: `python:3.11-slim-bookworm`
   - Install system runtimes: `poppler-utils`, `libgl1`, `libglib2.0-0`, `libgomp1`, `libpq5`, `curl`.
   - Copy virtual environment from builder: `COPY --from=builder /opt/venv /opt/venv`.
   - Create non-root user: `appuser` (UID 10001).
   - Create storage directories (`/app/storage/{uploads,preprocessed,reports}`) with ownership `appuser:appuser`.
   - Copy application code: `COPY --chown=appuser:appuser . /app`.
   - Set environment: `PATH="/opt/venv/bin:$PATH"`, `PYTHONUNBUFFERED=1`.
   - Switch user: `USER appuser`.
   - Expose port: `8000`.
   - `ENTRYPOINT ["/app/entrypoint.sh"]` (Runs `alembic upgrade head` and starts `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`).

**Acceptance Criteria:**
- Builds clean Docker image; runs as non-root user; starts server with Poppler available (TC-DEP-01).

---

### CHIP DEP-02 — Frontend Multi-Stage Production Dockerfile & Nginx Conf

**Objective:** Build a multi-stage Dockerfile for the React/Vite frontend that compiles TypeScript assets using Node 18 and serves static files using an optimized Nginx Alpine image (FR-DEP-01).

**Why:** Produces a featherweight container (< 30MB) that serves pre-compressed static assets at ultra-high throughput without keeping Node.js in the production runtime.

**Dependencies:** Phase 16 Frontend.

**Files to create:**
- `frontend/Dockerfile`
- `frontend/.dockerignore`
- `frontend/nginx.conf`

**Implementation:**
1. Stage 1: Build
   - Base image: `node:18-alpine`
   - Install dependencies: `npm ci`.
   - Build production bundle: `npm run build` -> outputs to `/app/dist`.
2. Stage 2: Production Web Server
   - Base image: `nginx:1.25-alpine`
   - Copy compiled assets: `COPY --from=build /app/dist /usr/share/nginx/html`.
   - Copy custom Nginx configuration: `COPY nginx.conf /etc/nginx/conf.d/default.conf`.
3. Configure `frontend/nginx.conf`:
   - SPA fallback routing: `try_files $uri $uri/ /index.html;` (prevents 404 on page refresh).
   - Gzip compression for JS, CSS, JSON, SVG assets.
   - Long-term caching headers (`Cache-Control: public, max-age=31536000, immutable`) for hashed assets.
   - Expose port `80`.

**Acceptance Criteria:**
- Builds static bundle into Nginx container; handles client-side routing cleanly (TC-DEP-01).

---

### CHIP DEP-03 — Multi-Container Docker Compose Orchestration

**Objective:** Create `docker-compose.yml` orchestrating all 4 core services: `backend`, `frontend`, `db` (PostgreSQL 15), and `redis` (Redis 7) with network isolation, health checks, and persistent volumes (FR-DEP-02).

**Why:** Allows any developer, examiner, or evaluator to spin up the entire multi-tier system with a single command: `docker compose up --build`.

**Dependencies:** CHIP DEP-01, CHIP DEP-02.

**Files to create:**
- `docker-compose.yml`
- `docker-compose.prod.yml`

**Implementation:**
1. Service `db`:
   - Image: `postgres:15-alpine`
   - Persistent volume: `postgres_data:/var/lib/postgresql/data`
   - Health check: `pg_isready -U ${POSTGRES_USER}`
2. Service `redis`:
   - Image: `redis:7-alpine`
   - Persistent volume: `redis_data:/data`
3. Service `backend`:
   - Depends on `db` and `redis` with `condition: service_healthy`.
   - Persistent volume: `storage_data:/app/storage` (preserves uploaded files and generated reports).
   - Environment variables injected from `.env`.
4. Service `frontend`:
   - Depends on `backend`.
   - Ports: `80:80` (or `5173:80`).
5. Shared internal network: `cert_verify_network`.

**Acceptance Criteria:**
- All 4 services start, pass health checks, and communicate over internal Docker network (TC-DEP-02).

---

### CHIP DEP-04 — Nginx Reverse Proxy Gateway & Security Headers

**Objective:** Configure a production Nginx gateway routing `/api/*` to the FastAPI backend, `/` to the React frontend, enforcing a 10MB upload limit and applying strict HTTP security headers (FR-DEP-03, NFR-02).

**Why:** Provides a single unified entry point (port 80/443), prevents CORS complexities, enforces file upload size limits at the edge, and hardens the application against cross-site scripting and clickjacking.

**Dependencies:** CHIP DEP-03.

**Files to create:**
- `nginx/nginx.conf`

**Implementation:**
1. Reverse proxy routing:
   - `location /api/`: `proxy_pass http://backend:8000;`, set `X-Real-IP`, `X-Forwarded-For`, `Host`.
   - `location /`: `proxy_pass http://frontend:80;`.
2. Upload size limit:
   - `client_max_body_size 10M;` (Enforces 10MB limit at the gateway before hitting Python).
3. Security headers (NFR-02):
   - `X-Frame-Options: DENY` (Clickjacking protection)
   - `X-Content-Type-Options: nosniff` (MIME sniffing protection)
   - `X-XSS-Protection: 1; mode=block`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Content-Security-Policy: default-src 'self'; img-src 'self' data: blob:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self';`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HSTS for HTTPS)

**Acceptance Criteria:**
- Nginx routes API and frontend traffic; blocks uploads $> 10$MB with HTTP 413; returns all security headers (TC-DEP-03).

---

### CHIP DEP-05 — Secrets Management & Production Environment Isolation

**Objective:** Implement strict environment variable management ensuring no passwords, JWT secrets, or cryptographic keys are committed to Git, documenting all variables in `.env.example` (FR-DEP-04, NFR-02).

**Why:** Prevents credential leaks and ensures reproducible configuration across dev, staging, and production environments.

**Dependencies:** Phase 01 Foundation.

**Files to create:**
- `.env.production.example`
- `scripts/generate_secrets.py`

**Implementation:**
1. Implement secret generator script:
   - Generates secure random 64-character hex keys for `SECRET_KEY` and `REPORT_SIGNING_KEY` using `secrets.token_hex(32)`.
2. Enforce `.gitignore`: Confirm `.env`, `.env.local`, and `.env.production` are strictly ignored.
3. Validate settings at startup in `backend/app/config.py`:
   - Raise fatal configuration error if default placeholder secrets (`change_me`) are detected in production mode.

**Acceptance Criteria:**
- All secrets loaded from environment; server refuses to start if insecure defaults are used in production (TC-DEP-04).

---

### CHIP DEP-06 — Automated CI Pipeline via GitHub Actions

**Objective:** Create `.github/workflows/ci.yml` running code formatting checks (Ruff), backend unit and integration tests, code coverage assertions ($\ge 80\%$), frontend build checks, and Docker container builds on every push and pull request (FR-DEP-05).

**Why:** Guarantees continuous quality assurance and prevents breaking changes from reaching the main branch.

**Dependencies:** Phase 19 Testing.

**Files to create:**
- `.github/workflows/ci.yml`

**Implementation:**
1. Define GitHub Actions workflow jobs:
   - **Job 1: Lint & Code Quality:**
     - Runs `ruff check .` and `ruff format --check .` for Python.
     - Runs `npm run lint` for TypeScript.
   - **Job 2: Backend Tests & Coverage:**
     - Sets up Python 3.11 with Poppler and dependencies.
     - Runs `pytest --cov=app --cov-fail-under=80`.
     - Uploads coverage artifact to Codecov / GitHub Actions summary.
   - **Job 3: Frontend Build Verification:**
     - Sets up Node 18.
     - Runs `npm ci` and `npm run build`.
   - **Job 4: Docker Build Test:**
     - Tests building `backend/Dockerfile` and `frontend/Dockerfile`.

**Acceptance Criteria:**
- GitHub Actions workflow runs cleanly across all 4 jobs on push (TC-DEP-05).

---

### CHIP DEP-07 — SSL / TLS Certificate Automation Script

**Objective:** Provide setup scripts and Nginx SSL configuration for both local HTTPS testing (using self-signed mkcert) and production HTTPS (using Let's Encrypt / Certbot).

**Why:** High-stakes verification systems require end-to-end encryption (HTTPS) in transit to protect student documents and credentials.

**Dependencies:** CHIP DEP-04.

**Files to create:**
- `scripts/init_ssl.sh`
- `nginx/ssl_support.conf`

**Acceptance Criteria:**
- Generates valid SSL certificates and binds HTTPS to port 443 with automatic HTTP -> HTTPS redirect.

---

### CHIP DEP-08 — Database Backup & Disaster Recovery Automation

**Objective:** Implement automated database backup and restore scripts for PostgreSQL (`scripts/backup_db.sh` and `scripts/restore_db.sh`).

**Why:** Protects against data loss and provides disaster recovery procedures for institutional records and audit logs.

**Dependencies:** CHIP DEP-03.

**Files to create:**
- `scripts/backup_db.sh`
- `scripts/restore_db.sh`

**Implementation:**
1. `backup_db.sh`:
   - Runs `pg_dump` via docker compose into compressed archive `backups/db_backup_{timestamp}.sql.gz`.
   - Retains last 7 daily backups, purging older archives.
2. `restore_db.sh`:
   - Safely restores PostgreSQL database from specified backup archive.

**Acceptance Criteria:**
- Successfully dumps and restores database tables cleanly.

---

### CHIP DEP-09 — Single-Command Production Deployment Script

**Objective:** Create master deployment script `scripts/deploy.sh` executing environment validation, pulling code, building containers, running database migrations, and executing post-deployment smoke tests.

**Why:** Standardizes the production deployment procedure into a repeatable, zero-downtime workflow.

**Dependencies:** CHIP DEP-03, CHIP DEP-04.

**Files to create:**
- `scripts/deploy.sh`

**Implementation:**
1. Script steps:
   - Check Docker and Docker Compose prerequisites.
   - Verify `.env` configuration exists.
   - Execute `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.
   - Wait for services to pass health checks.
   - Run smoke test script (`scripts/smoke_test.sh`).
   - Print system access URLs and status.

**Acceptance Criteria:**
- Deploys full stack and reports successful startup status.

---

### CHIP DEP-10 — Docker System Cleanup & Disk Pruning Utility

**Objective:** Create utility script `scripts/docker_clean.sh` to safely prune unused container layers, orphaned volumes, and stale build caches.

**Dependencies:** CHIP DEP-03.

**Files to create:**
- `scripts/docker_clean.sh`

**Acceptance Criteria:**
- Reclaims disk space without removing active database volumes or storage data.

---

### CHIP DEP-11 — Unit Tests: Docker Builds and Service Inter-Communication

**Objective:** Test Dockerfile builds and verify that backend, frontend, PostgreSQL, and Redis containers start and communicate over internal networks (TC-DEP-01, TC-DEP-02).

**Dependencies:** CHIP DEP-01, CHIP DEP-02, CHIP DEP-03.

**Files to create:**
- `tests/deployment/test_docker_builds.py`

**Implementation:**
1. Test `test_backend_dockerfile_builds()`: Verify backend Docker image builds without errors (TC-DEP-01).
2. Test `test_frontend_dockerfile_builds()`: Verify frontend Docker image builds without errors (TC-DEP-01).
3. Test `test_docker_compose_services_healthy()`: Spin up compose stack in CI/test environment; assert all 4 services report healthy status (TC-DEP-02).

**Acceptance Criteria:**
- 100% test pass rate across container build and orchestration tests.

---

### CHIP DEP-12 — Unit Tests: Security Headers, Upload Limits and Secrets

**Objective:** Test Nginx security headers, 10MB upload limit enforcement, and secrets isolation (TC-DEP-03, TC-DEP-04, TC-DEP-05).

**Dependencies:** CHIP DEP-04, CHIP DEP-05, CHIP DEP-06.

**Files to create:**
- `tests/deployment/test_security_hardening.py`

**Implementation:**
1. Test `test_security_headers_present()`: Request `GET /` via Nginx; assert presence of `X-Frame-Options`, `X-Content-Type-Options`, and `Content-Security-Policy` (TC-DEP-03).
2. Test `test_gateway_blocks_oversized_uploads()`: Send 12MB payload to `/api/v1/certificates/upload`; assert Nginx immediately responds with 413 Request Entity Too Large (TC-DEP-03).
3. Test `test_insecure_default_secret_rejected()`: Assert application raises startup error if `SECRET_KEY == "change_me"` in production mode (TC-DEP-04).

**Acceptance Criteria:**
- All security header, upload limit, and secrets tests pass.

---

## 9. Implementation Order and Dependencies

```
CHIP DEP-01 (Backend Multi-Stage Dockerfile)
    ↓
CHIP DEP-02 (Frontend Multi-Stage Dockerfile)
    ↓
CHIP DEP-03 (Docker Compose Orchestration) ──┐
    ↓                                        │
CHIP DEP-04 (Nginx Reverse Proxy & Headers) │
    ↓                                        │
CHIP DEP-05 (Secrets & Environment Isolation)│
    ↓                                        │
CHIP DEP-06 (GitHub Actions CI Workflow) ◄───┘
    ↓
CHIP DEP-07 (SSL / TLS Automation)
    ↓
CHIP DEP-08 (Database Backup / Restore)
    ↓
CHIP DEP-09 (Master Deployment Script) & CHIP DEP-10 (Cleanup Utility)
    ↓
CHIP DEP-11 & CHIP DEP-12 (Deployment & Security Tests)
```

---

## 10. Phase Completion Checklist

- [x] Multi-stage backend Dockerfile runs as non-root user with Poppler, OpenCV, and PyTorch.
- [x] Multi-stage frontend Dockerfile compiles React app and serves via lightweight Nginx.
- [x] Docker Compose orchestrates backend, frontend, PostgreSQL, and Redis with health checks.
- [x] Nginx gateway enforces 10MB upload limit and injects HSTS, CSP, and X-Frame-Options headers.
- [x] Secrets and database credentials isolated via `.env.production` with random 64-char keys.
- [x] GitHub Actions CI pipeline tests linting, pytest ($\ge 80\%$ coverage), and Docker builds.
- [x] Automated database backup and restore scripts tested and functional.
- [x] Single-command deployment script `deploy.sh` spins up verified production stack.
- [x] Test cases TC-DEP-01 through TC-DEP-05 passing with 100% success rate.
