# Phase 01 — Project Foundation

## 1. Purpose

Set up the complete development environment, project structure, version control, configuration management, and base infrastructure that all subsequent phases depend on. By the end of this phase, a developer should have a running (empty) FastAPI server, a connected database, a React frontend shell, and a reproducible development environment.

## 2. Why This Phase Exists

Every subsequent phase depends on a consistent project structure, working development tooling, and base configurations. Without this foundation, each phase would need to independently set up infrastructure, leading to inconsistencies. This phase ensures:

- Reproducible environment (venv, `.env`, dependencies)
- Consistent project layout that all chips reference
- Working backend server accepting requests
- Working frontend dev server rendering a shell
- Database connection ready for schema creation
- Git repository with proper `.gitignore`

## 3. Requirements Covered

| Requirement | How |
|---|---|
| NFR-08 (Maintainability / Modular pipeline) | Modular folder structure with separate module directories |
| NFR-09 (Portability / Cross-browser web app) | React + Vite setup with modern browser targets |
| **Supporting Requirement** | Project structure, environment config, dev tooling — not explicitly in SRD but technically required for all implementation |

## 4. Inputs

- Master Development Plan (this document)
- Technology stack decisions
- Project structure specification

## 5. Outputs

- Initialized Git repository with `.gitignore`
- Backend project with FastAPI running on `localhost:8000`
- Frontend project with React/Vite running on `localhost:5173`
- Database connection configuration (SQLite for initial development)
- Environment configuration via `.env`
- CI-ready project structure
- `README.md` with setup instructions

## 6. Dependencies

- **Previous phases:** None (this is the first phase)
- **External tools:** Python 3.11+, Node.js 18+, npm, Git
- **Libraries:** See chip-level details

## 7. Files and Folder Structure

```
AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/
├── .gitignore
├── .env.example
├── README.md
│
├── backend/
│   ├── pyproject.toml                 # Project metadata + dependencies
│   ├── requirements.txt              # Pip-installable dependencies
│   ├── .env.example                  # Backend-specific env vars
│   ├── alembic.ini                   # Alembic config
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                 # Migration files
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── config.py                 # Pydantic Settings for env config
│   │   ├── database.py               # SQLAlchemy engine, session, Base
│   │   ├── models/                   # SQLAlchemy ORM models (empty init)
│   │   │   └── __init__.py
│   │   ├── schemas/                  # Pydantic schemas (empty init)
│   │   │   └── __init__.py
│   │   ├── api/                      # API routers
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── router.py         # Main v1 router aggregator
│   │   ├── services/                 # Business logic (empty init)
│   │   │   └── __init__.py
│   │   ├── modules/                  # Analysis pipeline modules (empty dirs)
│   │   │   ├── __init__.py
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
│   │   ├── core/                     # Auth, security, shared exceptions
│   │   │   ├── __init__.py
│   │   │   └── exceptions.py         # Base exception classes
│   │   └── utils/                    # Shared utility functions
│   │       ├── __init__.py
│   │       └── file_utils.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py               # Shared fixtures
│       └── test_health.py            # Health check test
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── services/
│       │   └── api.ts                # Axios instance
│       ├── types/
│       └── utils/
│
├── ml/
│   ├── data/                         # .gitignore'd
│   ├── notebooks/
│   ├── scripts/
│   ├── models/                       # .gitignore'd
│   └── configs/
│
└── storage/                          # .gitignore'd — uploaded files
    ├── uploads/
    ├── preprocessed/
    └── reports/
```

### File Responsibilities

| File | Responsibility |
|---|---|
| `backend/app/main.py` | Create FastAPI app instance, include routers, configure CORS, add health check endpoint |
| `backend/app/config.py` | Load environment variables using Pydantic `BaseSettings` — DB URL, secret key, storage paths, etc. |
| `backend/app/database.py` | Create SQLAlchemy engine, session factory, and declarative Base class |
| `backend/app/core/exceptions.py` | Define base exception classes: `AppException`, `NotFoundError`, `ValidationError`, `UnauthorizedError` |
| `backend/app/api/v1/router.py` | Aggregate all v1 sub-routers into a single router with `/api/v1` prefix |
| `backend/tests/conftest.py` | Shared pytest fixtures: test client, test database session, test settings |
| `frontend/src/services/api.ts` | Create configured Axios instance with base URL, interceptors, error handling |
| `frontend/src/App.tsx` | Root component with React Router setup, basic layout shell |

---

## 8. Implementation Chips

---

### CHIP FND-01 — Initialize Git Repository

**Objective:** Create the Git repository with a comprehensive `.gitignore`.

**Why:** Version control is foundational. The `.gitignore` must exclude model artifacts, datasets, uploaded files, environment files, and build outputs from the start.

**Dependencies:** Git installed on the system.

**Files to create:**
- `.gitignore`

**Files to modify:** None

**Implementation:**
1. Run `git init` in the project root (if not already initialized).
2. Create `.gitignore` covering:
   - Python: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `*.egg-info/`, `dist/`, `build/`
   - Node: `node_modules/`, `dist/`
   - Environment: `.env`, `.env.local`
   - Storage: `storage/`, `ml/data/`, `ml/models/`
   - IDE: `.vscode/`, `.idea/`
   - OS: `.DS_Store`, `Thumbs.db`
   - Database: `*.db`, `*.sqlite3`
3. Make initial commit: `git commit -m "chore: initialize repository with .gitignore"`

**Inputs:** None

**Outputs:** Initialized Git repository with `.gitignore`

**Edge Cases:**
- Repository may already exist with some history — preserve existing commits
- Existing files may need to be untracked if already committed

**Error Handling:** N/A

**Logging:** N/A

**Security:** Ensure `.env` files are in `.gitignore` before any secrets are added.

**Testing:** Verify `.gitignore` is working: create a test `.env` file and confirm `git status` does not show it.

**Acceptance Criteria:**
- Git repository initialized
- `.gitignore` excludes all specified patterns
- Initial commit exists

**Definition of Done:** Repository initialized, `.gitignore` committed, `git status` clean.

---

### CHIP FND-02 — Create Root Configuration Files

**Objective:** Create the root-level project configuration files: `.env.example` and `README.md`.

**Why:** `.env.example` documents required environment variables so any developer can set up the project. `README.md` provides project overview and setup instructions.

**Dependencies:** CHIP FND-01

**Files to create:**
- `.env.example`
- `README.md` (update existing)

**Files to modify:** None

**Implementation:**

1. Create `.env.example` with documented variables:
   ```
   # Database
   DATABASE_URL=sqlite:///./dev.db
   
   # Security
   SECRET_KEY=your-secret-key-here
   
   # Storage
   UPLOAD_DIR=./storage/uploads
   PREPROCESSED_DIR=./storage/preprocessed
   REPORT_DIR=./storage/reports
   
   # OCR
   OCR_ENGINE=paddleocr
   
   # Model
   MODEL_DIR=./ml/models
   MODEL_VERSION=v1.0
   
   # Server
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8000
   FRONTEND_URL=http://localhost:5173
   ```

2. Update `README.md` with:
   - Project title and description
   - Prerequisites (Python 3.11+, Node.js 18+, Git)
   - Quick start instructions (backend + frontend)
   - Project structure overview
   - Link to development plan

**Inputs:** Technology stack decisions from Master Plan

**Outputs:** `.env.example`, `README.md`

**Data Structures:** N/A

**Edge Cases:**
- Different OS path separators — use forward slashes (works on all platforms)

**Error Handling:** N/A

**Logging:** N/A

**Security:** `.env.example` must NOT contain real secrets — only placeholder values.

**Testing:** Verify `.env.example` is readable and all variables are documented.

**Acceptance Criteria:**
- `.env.example` contains all required variables with placeholder values
- `README.md` contains setup instructions

**Definition of Done:** Both files created, committed.

---

### CHIP FND-03 — Set Up Python Backend Project

**Objective:** Create the Python backend project structure with `pyproject.toml` and `requirements.txt`.

**Why:** Establishes the dependency management and project metadata for the backend. All subsequent backend chips depend on this.

**Dependencies:** CHIP FND-01, Python 3.11+ installed

**Files to create:**
- `backend/pyproject.toml`
- `backend/requirements.txt`
- `backend/.env.example`

**Files to modify:** None

**Implementation:**

1. Create `backend/pyproject.toml`:
   ```toml
   [project]
   name = "certificate-verification-backend"
   version = "0.1.0"
   description = "AI-Based Certificate Authenticity Assessment System — Backend"
   requires-python = ">=3.11"
   
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   asyncio_mode = "auto"
   
   [tool.ruff]
   line-length = 100
   target-version = "py311"
   ```

2. Create `backend/requirements.txt` with Phase 01 dependencies only:
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   pydantic==2.5.0
   pydantic-settings==2.1.0
   sqlalchemy==2.0.23
   alembic==1.13.0
   python-dotenv==1.0.0
   python-multipart==0.0.6
   httpx==0.25.2
   pytest==7.4.3
   pytest-asyncio==0.23.2
   ```

3. Create `backend/.env.example` (backend-specific copy).

**Inputs:** Technology stack from Master Plan

**Outputs:** Backend project metadata and dependency files

**Edge Cases:**
- Dependency version conflicts — pin exact versions
- Platform-specific dependencies (e.g., uvloop on Linux only) — use optional extras

**Error Handling:** N/A

**Logging:** N/A

**Security:** N/A

**Testing:** Run `pip install -r requirements.txt` in a fresh venv and verify no errors.

**Acceptance Criteria:**
- `requirements.txt` installs without errors
- All Phase 01 dependencies are listed
- Future phase dependencies are NOT yet included

**Definition of Done:** Files created, dependencies installable.

---

### CHIP FND-04 — Create Python Virtual Environment

**Objective:** Create and document the Python virtual environment setup.

**Why:** Isolates project dependencies from the system Python installation.

**Dependencies:** CHIP FND-03

**Files to create:** None (venv is not committed)

**Files to modify:**
- `README.md` — add venv setup instructions

**Implementation:**

1. Create virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

2. Add to `README.md`:
   ```markdown
   ## Backend Setup
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your values
   uvicorn app.main:app --reload
   ```

**Inputs:** `requirements.txt`

**Outputs:** Working virtual environment

**Edge Cases:**
- Python version mismatch — document minimum version requirement
- `venv` already exists — instruct to delete and recreate

**Error Handling:** N/A

**Logging:** N/A

**Security:** venv directory must be in `.gitignore`

**Testing:** `python --version` shows 3.11+, `pip list` shows installed packages.

**Acceptance Criteria:**
- Virtual environment created
- All dependencies installed
- `README.md` updated with instructions

**Definition of Done:** venv works, dependencies installed, documented.

---

### CHIP FND-05 — Create FastAPI Application Entry Point

**Objective:** Create `backend/app/main.py` with a FastAPI application instance, CORS configuration, and a health check endpoint.

**Why:** This is the entry point that all API routers will be attached to. The health check verifies the server is running. CORS is needed for the frontend to communicate with the backend.

**Dependencies:** CHIP FND-03, CHIP FND-04

**Files to create:**
- `backend/app/__init__.py`
- `backend/app/main.py`

**Files to modify:** None

**Implementation:**

Create `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Certificate Verification API",
    description="AI-Based Academic Certificate Authenticity Assessment System",
    version="0.1.0",
)

# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
```

**Inputs:** None

**Outputs:** Running FastAPI server responding to `GET /health`

**Data Structures:**
```json
// GET /health response
{
  "status": "healthy",
  "version": "0.1.0"
}
```

**Edge Cases:**
- Port 8000 already in use — document how to change port
- CORS origin mismatch — configurable via environment variable

**Error Handling:** FastAPI default error handling for 404, 422, 500.

**Logging:** FastAPI/Uvicorn default request logging.

**Security:** CORS origins should be configurable, not hardcoded in production.

**Testing:**
```bash
uvicorn app.main:app --reload
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"0.1.0"}
```

**Acceptance Criteria:**
- Server starts without errors on `uvicorn app.main:app --reload`
- `GET /health` returns 200 with expected JSON
- CORS allows requests from `http://localhost:5173`

**Definition of Done:** Server runs, health check responds, CORS configured.

---

### CHIP FND-06 — Create Configuration Management

**Objective:** Create `backend/app/config.py` using Pydantic `BaseSettings` to manage all environment variables with validation and defaults.

**Why:** Centralizes configuration, validates environment variables at startup, provides typed access to settings throughout the application. Prevents scattered `os.getenv()` calls.

**Dependencies:** CHIP FND-05

**Files to create:**
- `backend/app/config.py`

**Files to modify:** None

**Implementation:**

Create `backend/app/config.py`:
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./dev.db"
    
    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    
    # Storage paths
    upload_dir: Path = Path("./storage/uploads")
    preprocessed_dir: Path = Path("./storage/preprocessed")
    report_dir: Path = Path("./storage/reports")
    
    # OCR
    ocr_engine: str = "paddleocr"
    
    # Model
    model_dir: Path = Path("./ml/models")
    model_version: str = "v1.0"
    
    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    return Settings()
```

**Inputs:** `.env` file (or environment variables)

**Outputs:** `Settings` object accessible throughout the application

**Data Structures:**
```python
Settings(
    database_url="sqlite:///./dev.db",
    secret_key="...",
    upload_dir=Path("./storage/uploads"),
    # ... etc
)
```

**Edge Cases:**
- `.env` file missing — Pydantic falls back to defaults + environment variables
- Invalid values — Pydantic raises `ValidationError` at startup (fail fast)
- Relative paths — resolve relative to backend directory

**Error Handling:** Pydantic validation errors surface at application startup, not at runtime.

**Logging:** Log loaded configuration (excluding secrets) at startup.

**Security:**
- `secret_key` must be overridden in production
- Do not log `secret_key` or `database_url` containing passwords

**Testing:**
```python
def test_settings_defaults():
    settings = Settings()
    assert settings.database_url == "sqlite:///./dev.db"
    assert settings.ocr_engine == "paddleocr"
```

**Acceptance Criteria:**
- `Settings` class loads from `.env`
- All variables have sensible defaults
- Invalid values cause startup failure with clear error message

**Definition of Done:** Config module created, tested with defaults, documented.

---

### CHIP FND-07 — Create Database Connection Module

**Objective:** Create `backend/app/database.py` with SQLAlchemy engine, session factory, and declarative Base.

**Why:** All ORM models and database operations depend on these foundational objects. The session dependency will be injected into FastAPI route handlers.

**Dependencies:** CHIP FND-06

**Files to create:**
- `backend/app/database.py`

**Files to modify:** None

**Implementation:**

Create `backend/app/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Inputs:** `DATABASE_URL` from config

**Outputs:** `engine`, `SessionLocal`, `Base`, `get_db` dependency

**Edge Cases:**
- SQLite requires `check_same_thread=False` for FastAPI async usage
- PostgreSQL URL format differs from SQLite — handled by SQLAlchemy
- Database file not found (SQLite) — engine creates it automatically

**Error Handling:**
- Connection failure raises `OperationalError` — should be caught at startup

**Logging:** SQLAlchemy `echo=True` in debug mode for SQL query logging.

**Security:** Database URL may contain credentials — do not log it.

**Testing:**
```python
def test_database_connection():
    from app.database import engine
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

**Acceptance Criteria:**
- `engine` connects to configured database
- `get_db()` yields a working session
- SQLite works out of the box with no extra configuration

**Definition of Done:** Database module created, connection tested.

---

### CHIP FND-08 — Initialize Alembic for Database Migrations

**Objective:** Set up Alembic for database schema migrations.

**Why:** As tables are added in later phases, migrations ensure the database schema evolves consistently. Alembic tracks schema versions.

**Dependencies:** CHIP FND-07

**Files to create:**
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/` (empty directory)

**Files to modify:** None

**Implementation:**

1. Run `alembic init alembic` in the `backend/` directory.
2. Edit `alembic.ini` — set `sqlalchemy.url` to read from environment:
   ```ini
   sqlalchemy.url = sqlite:///./dev.db
   ```
3. Edit `alembic/env.py` to import the application's `Base` and `engine`:
   ```python
   from app.database import Base, engine
   target_metadata = Base.metadata
   ```

**Inputs:** Database configuration

**Outputs:** Alembic configuration ready for generating migrations

**Edge Cases:**
- `alembic/versions/` must exist even if empty
- Database URL in `alembic.ini` must match the app config

**Error Handling:** Alembic errors on invalid `env.py` — fix import paths.

**Logging:** Alembic has built-in logging for migrations.

**Security:** N/A

**Testing:**
```bash
cd backend
alembic check  # Should report no pending migrations (no models yet)
```

**Acceptance Criteria:**
- Alembic initialized
- `alembic/env.py` correctly imports app `Base`
- `alembic check` runs without errors

**Definition of Done:** Alembic configured and tested.

---

### CHIP FND-09 — Create Base Exception Classes

**Objective:** Define reusable exception classes for the application.

**Why:** Consistent error handling across all modules. FastAPI exception handlers will map these to appropriate HTTP responses.

**Dependencies:** CHIP FND-05

**Files to create:**
- `backend/app/core/__init__.py`
- `backend/app/core/exceptions.py`

**Files to modify:**
- `backend/app/main.py` — register exception handlers

**Implementation:**

Create `backend/app/core/exceptions.py`:
```python
class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)

class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=422)

class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, status_code=401)

class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=403)

class FileProcessingError(AppException):
    def __init__(self, message: str = "File processing failed"):
        super().__init__(message=message, status_code=500)
```

Register handlers in `main.py`:
```python
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )
```

**Inputs:** N/A

**Outputs:** Exception classes usable across all modules

**Data Structures:**
```json
// Error response format
{
  "error": "Resource not found"
}
```

**Edge Cases:**
- Unhandled exceptions should still return 500 with generic message
- Pydantic validation errors should be left to FastAPI's default handler

**Error Handling:** These ARE the error handling infrastructure.

**Logging:** Exception handlers should log the error before returning the response.

**Security:** Do not expose internal error details (stack traces) in production responses.

**Testing:**
```python
def test_not_found_error():
    err = NotFoundError("Certificate not found")
    assert err.status_code == 404
    assert err.message == "Certificate not found"
```

**Acceptance Criteria:**
- All base exception classes defined
- Exception handler registered in FastAPI app
- Error responses follow consistent JSON format

**Definition of Done:** Exception classes created, handler registered, tested.

---

### CHIP FND-10 — Create Storage Directories and Utilities

**Objective:** Create the storage directory structure and a utility module for file path management.

**Why:** Uploaded certificates, preprocessed images, and generated reports need organized storage. Path management prevents scattered path construction.

**Dependencies:** CHIP FND-06

**Files to create:**
- `backend/app/utils/__init__.py`
- `backend/app/utils/file_utils.py`
- `storage/uploads/.gitkeep`
- `storage/preprocessed/.gitkeep`
- `storage/reports/.gitkeep`

**Files to modify:** None

**Implementation:**

Create `backend/app/utils/file_utils.py`:
```python
import os
import uuid
from pathlib import Path
from app.config import get_settings

def ensure_storage_dirs():
    """Create storage directories if they don't exist."""
    settings = get_settings()
    for dir_path in [settings.upload_dir, settings.preprocessed_dir, settings.report_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename preserving the original extension."""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"

def get_upload_path(filename: str) -> Path:
    """Get the full path for an uploaded file."""
    settings = get_settings()
    return settings.upload_dir / filename

def get_preprocessed_path(filename: str) -> Path:
    """Get the full path for a preprocessed image."""
    settings = get_settings()
    return settings.preprocessed_dir / filename

def get_report_path(filename: str) -> Path:
    """Get the full path for a generated report."""
    settings = get_settings()
    return settings.report_dir / filename
```

**Inputs:** Configuration settings

**Outputs:** Storage directories exist; path utility functions available

**Edge Cases:**
- Directories already exist — `exist_ok=True` handles this
- Filename collisions — UUID-based naming prevents collisions
- Filenames with special characters — UUID replacement handles this

**Error Handling:**
- `PermissionError` if storage path is not writable — fail at startup

**Logging:** Log storage directory creation at startup.

**Security:** Storage directories should not be web-accessible directly.

**Testing:**
```python
def test_generate_unique_filename():
    name = generate_unique_filename("test.pdf")
    assert name.endswith(".pdf")
    assert len(name) == 36  # 32 hex chars + ".pdf"
```

**Acceptance Criteria:**
- Storage directories created on startup
- Unique filename generation works for all supported extensions
- Path utilities return correct paths

**Definition of Done:** File utilities created, directories exist, tested.

---

### CHIP FND-11 — Create API Router Structure

**Objective:** Set up the versioned API router structure (`/api/v1/`) and a placeholder health endpoint.

**Why:** All API endpoints will be organized under `/api/v1/`. Setting up the router structure now prevents refactoring later.

**Dependencies:** CHIP FND-05

**Files to create:**
- `backend/app/api/__init__.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/api/v1/router.py`

**Files to modify:**
- `backend/app/main.py` — include the v1 router

**Implementation:**

Create `backend/app/api/v1/router.py`:
```python
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Sub-routers will be included here as they are created:
# api_router.include_router(certificates.router, tags=["certificates"])
# api_router.include_router(auth.router, tags=["auth"])
# etc.
```

Modify `backend/app/main.py` to include:
```python
from app.api.v1.router import api_router
app.include_router(api_router)
```

**Inputs:** None

**Outputs:** `/api/v1/` prefix ready for sub-routers

**Edge Cases:** None at this stage.

**Error Handling:** N/A

**Logging:** N/A

**Security:** N/A

**Testing:**
```bash
curl http://localhost:8000/api/v1/  # Should return 404 (no endpoints yet, but no error)
```

**Acceptance Criteria:**
- API router structure exists
- Router is included in the main app
- Swagger docs at `/docs` show the API prefix

**Definition of Done:** Router structure created and integrated.

---

### CHIP FND-12 — Create Test Infrastructure

**Objective:** Set up pytest configuration with shared fixtures for the test client and test database.

**Why:** Every subsequent test depends on consistent test infrastructure: a test client for API testing and a separate test database to avoid polluting development data.

**Dependencies:** CHIP FND-05, CHIP FND-07

**Files to create:**
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/test_health.py`

**Files to modify:** None

**Implementation:**

Create `backend/tests/conftest.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Create `backend/tests/test_health.py`:
```python
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
```

**Inputs:** FastAPI app, database configuration

**Outputs:** Working test suite with `pytest` execution

**Edge Cases:**
- Test database cleanup between tests — handled by `drop_all` in fixture
- Parallel test execution — each test gets its own session

**Error Handling:** N/A

**Logging:** pytest output

**Security:** Test database is separate from development database.

**Testing:**
```bash
cd backend
pytest tests/test_health.py -v
# Expected: 1 passed
```

**Acceptance Criteria:**
- `pytest` runs without errors
- Health check test passes
- Test database is created and cleaned up per test

**Definition of Done:** Test infrastructure works, health check test passes.

---

### CHIP FND-13 — Initialize React Frontend Project

**Objective:** Create the React + Vite + TypeScript frontend project with Tailwind CSS.

**Why:** The frontend provides the web UI for certificate upload, results viewing, and administration. Setting up the build tooling now ensures all frontend chips have a consistent base.

**Dependencies:** CHIP FND-01, Node.js 18+ installed

**Files to create:** (via Vite scaffolding)
- `frontend/` directory with all Vite + React + TypeScript boilerplate

**Files to modify:** None

**Implementation:**

1. Create the frontend project:
   ```bash
   npx -y create-vite@latest frontend -- --template react-ts
   cd frontend
   npm install
   ```

2. Install Tailwind CSS:
   ```bash
   npm install -D tailwindcss @tailwindcss/vite
   ```

3. Configure Tailwind in `vite.config.ts`:
   ```typescript
   import { defineConfig } from 'vite'
   import react from '@vitejs/plugin-react'
   import tailwindcss from '@tailwindcss/vite'
   
   export default defineConfig({
     plugins: [react(), tailwindcss()],
     server: {
       port: 5173,
       proxy: {
         '/api': 'http://localhost:8000',
       },
     },
   })
   ```

4. Add Tailwind import to `src/index.css`:
   ```css
   @import "tailwindcss";
   ```

5. Install additional dependencies:
   ```bash
   npm install react-router-dom axios
   npm install -D @types/react-router-dom
   ```

**Inputs:** None

**Outputs:** Running Vite dev server at `http://localhost:5173`

**Edge Cases:**
- Port 5173 already in use — configure alternative port
- npm version compatibility — use npm 9+

**Error Handling:** N/A

**Logging:** Vite dev server logs

**Security:** API proxy in Vite config avoids CORS issues in development.

**Testing:**
```bash
cd frontend
npm run dev
# Visit http://localhost:5173 — should see React page
```

**Acceptance Criteria:**
- `npm run dev` starts without errors
- Page renders at `http://localhost:5173`
- Tailwind CSS classes work
- API proxy to backend works

**Definition of Done:** Frontend project running with Tailwind CSS and React Router.

---

### CHIP FND-14 — Create Frontend Application Shell

**Objective:** Create the base application layout with routing, navigation header, and placeholder pages.

**Why:** Provides the navigation structure that all frontend chips will add pages to. Users need to navigate between upload, results, history, and admin sections.

**Dependencies:** CHIP FND-13

**Files to create:**
- `frontend/src/App.tsx` (overwrite default)
- `frontend/src/pages/HomePage.tsx`
- `frontend/src/pages/NotFoundPage.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/components/Navbar.tsx`
- `frontend/src/services/api.ts`

**Files to modify:**
- `frontend/src/main.tsx`

**Implementation:**

1. Create `Layout.tsx` — full-page layout with navigation bar and content area.
2. Create `Navbar.tsx` — navigation links: Home, Upload, History, Admin.
3. Create `App.tsx` with React Router:
   ```tsx
   <BrowserRouter>
     <Routes>
       <Route element={<Layout />}>
         <Route path="/" element={<HomePage />} />
         {/* More routes added in later phases */}
         <Route path="*" element={<NotFoundPage />} />
       </Route>
     </Routes>
   </BrowserRouter>
   ```
4. Create `api.ts` — Axios instance:
   ```typescript
   import axios from 'axios';
   
   const api = axios.create({
     baseURL: '/api/v1',
     headers: { 'Content-Type': 'application/json' },
   });
   
   export default api;
   ```

**Inputs:** None

**Outputs:** Navigable application shell with placeholder pages

**Edge Cases:**
- Unknown routes show 404 page
- Navigation works without full page reload (SPA)

**Error Handling:** 404 page for unknown routes

**Logging:** N/A

**Security:** N/A at this stage (auth added in Phase 15/16)

**Testing:** Manual: navigate between pages, verify no console errors.

**Acceptance Criteria:**
- Application shell renders with navigation
- Router navigates between pages
- 404 page shows for unknown routes
- Axios instance configured with correct base URL

**Definition of Done:** Shell application running with navigation.

---

### CHIP FND-15 — Create Module Directory Stubs

**Objective:** Create empty `__init__.py` files for all pipeline module directories so they are recognized as Python packages.

**Why:** Later phases will add implementation files to these directories. Having the package structure in place prevents import errors and establishes the modular architecture from the start (NFR-08).

**Dependencies:** CHIP FND-03

**Files to create:**
- `backend/app/modules/__init__.py`
- `backend/app/modules/ingestion/__init__.py`
- `backend/app/modules/preprocessing/__init__.py`
- `backend/app/modules/ocr/__init__.py`
- `backend/app/modules/text_consistency/__init__.py`
- `backend/app/modules/forensics/__init__.py`
- `backend/app/modules/template_matching/__init__.py`
- `backend/app/modules/ml_classifier/__init__.py`
- `backend/app/modules/score_fusion/__init__.py`
- `backend/app/modules/explainability/__init__.py`
- `backend/app/modules/report_generator/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/services/__init__.py`
- `ml/scripts/.gitkeep`
- `ml/notebooks/.gitkeep`
- `ml/configs/.gitkeep`

**Files to modify:** None

**Implementation:** Create empty `__init__.py` in each directory. Each file can contain a module-level docstring:
```python
"""Preprocessing module — image cleaning and normalization for OCR/CV/ML."""
```

**Inputs:** Project structure specification

**Outputs:** All module directories exist as importable Python packages

**Edge Cases:** None

**Error Handling:** N/A

**Logging:** N/A

**Security:** N/A

**Testing:** `from app.modules.preprocessing import *` should not raise `ImportError`.

**Acceptance Criteria:**
- All module directories created with `__init__.py`
- All directories importable as Python packages
- ML workspace directories created

**Definition of Done:** All directories exist, imports work.

---

## Chip Dependency Graph

```
FND-01 (Git init)
   ↓
FND-02 (Root config files)
   ↓
   ├──→ FND-03 (Python backend project)
   │       ↓
   │    FND-04 (Virtual environment)
   │       ↓
   │    FND-05 (FastAPI entry point)
   │       ↓
   │       ├──→ FND-06 (Config management)
   │       │       ↓
   │       │    FND-07 (Database connection)
   │       │       ↓
   │       │    FND-08 (Alembic migrations)
   │       │
   │       ├──→ FND-09 (Exception classes)
   │       │
   │       ├──→ FND-11 (API router structure)
   │       │
   │       └──→ FND-12 (Test infrastructure)
   │
   ├──→ FND-10 (Storage directories) ← depends on FND-06
   │
   ├──→ FND-13 (React frontend project)
   │       ↓
   │    FND-14 (Frontend shell)
   │
   └──→ FND-15 (Module directory stubs) ← depends on FND-03
```

### Parallel Development Opportunities

- FND-13/FND-14 (frontend) can be developed in parallel with FND-06–FND-12 (backend)
- FND-09 (exceptions) and FND-11 (router) can be developed in parallel
- FND-10 (storage) and FND-12 (testing) can be developed in parallel

---

## Phase Completion Checklist

```
[ ] FND-01: Git repository initialized with .gitignore
[ ] FND-02: .env.example and README.md created
[ ] FND-03: Python project with pyproject.toml and requirements.txt
[ ] FND-04: Virtual environment working with all dependencies
[ ] FND-05: FastAPI server running, health check responding
[ ] FND-06: Configuration management via Pydantic Settings
[ ] FND-07: Database connection module (SQLite for dev)
[ ] FND-08: Alembic initialized for migrations
[ ] FND-09: Base exception classes defined and handlers registered
[ ] FND-10: Storage directories and file utilities created
[ ] FND-11: API v1 router structure in place
[ ] FND-12: Pytest infrastructure with test client and test DB
[ ] FND-13: React + Vite + TypeScript + Tailwind project running
[ ] FND-14: Frontend shell with navigation and routing
[ ] FND-15: All module directory stubs created
[ ] All unit tests passing
[ ] Git commit(s) created
```

## Phase Acceptance Criteria

- `uvicorn app.main:app --reload` starts the backend server at `localhost:8000` without errors.
- `GET /health` returns `{"status": "healthy", "version": "0.1.0"}` with HTTP 200.
- `GET /docs` shows the Swagger UI with the health endpoint documented.
- `npm run dev` in `frontend/` starts the Vite dev server at `localhost:5173`.
- Frontend renders a navigation shell with placeholder pages.
- `pytest tests/test_health.py` passes.
- All module directories exist and are importable.
- `.env.example` documents all required environment variables.
- `README.md` contains setup instructions for both backend and frontend.

## Recommended Git Commits

```
chore: initialize repository with .gitignore
feat: create root configuration files
feat: set up Python backend project structure
feat: create FastAPI application with health check
feat: add configuration management and database connection
feat: add Alembic migrations, exceptions, and storage utilities
feat: create API router structure and test infrastructure
feat: initialize React frontend with Tailwind CSS
feat: create frontend application shell with routing
feat: add module directory stubs for pipeline architecture
```
