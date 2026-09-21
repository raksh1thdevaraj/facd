# Environment Configuration & Secrets Specification

**Document ID:** SPEC-06  
**Status:** Approved / Authoritative  
**Domain:** Security, Secrets Management, Configuration Profiles  

---

## 1. Overview

This document specifies all environment variables required by the system, their default values, security implications, and profile behaviors. The application must load configuration via Pydantic `BaseSettings` (`src/core/config.py`).

---

## 2. Environment Variables Catalog (`.env.example`)

```bash
# ==============================================================================
# 1. CORE APPLICATION SETTINGS
# ==============================================================================
ENVIRONMENT=development                # 'development', 'testing', or 'production'
DEBUG=True                             # Set False in production
APP_NAME="AI Certificate Verifier"
API_V1_STR="/api/v1"
SECRET_KEY=change-this-to-a-super-secret-hex-key-minimum-32-chars
ALLOWED_ORIGINS="http://localhost:5173,http://localhost:3000"

# ==============================================================================
# 2. DATABASE CONFIGURATION (PostgreSQL)
# ==============================================================================
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=cert_verify_db
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}
DATABASE_SYNC_URL=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}

# ==============================================================================
# 3. ASYNC TASK QUEUE (Celery + Redis)
# ==============================================================================
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
USE_ASYNC_CELERY=False                 # If False, runs via FastAPI BackgroundTasks (ideal for local dev)

# ==============================================================================
# 4. AUTHENTICATION & JWT
# ==============================================================================
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==============================================================================
# 5. STORAGE & UPLOADS
# ==============================================================================
STORAGE_BACKEND=local                  # 'local' or 's3'
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
REPORTS_DIR=./data/reports
MAX_UPLOAD_SIZE_BYTES=15728640          # 15 MB

# ==============================================================================
# 6. EXTERNAL BINARY PATHS & OCR
# ==============================================================================
TESSERACT_CMD=""                       # Path to tesseract executable if not in system PATH (e.g. /opt/homebrew/bin/tesseract)
POPPLER_PATH=""                        # Path to poppler pdftoppm if not in system PATH
OCR_DEFAULT_ENGINE=pytesseract        # 'pytesseract' or 'easyocr'

# ==============================================================================
# 7. ML MODEL CHECKPOINTS & DEVICE
# ==============================================================================
MODEL_DEVICE=auto                      # 'auto', 'cpu', 'cuda', 'mps'
BASELINE_MODEL_PATH=./models/baseline_xgb.json
CNN_MODEL_PATH=./models/cnn_visual_weights.pt
FUSED_MODEL_PATH=./models/fused_multimodal.pt
```

---

## 3. Pydantic Settings Implementation Blueprint

```python
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "AI Certificate Verifier"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "default-insecure-secret-key-32-chars-long"

    ALLOWED_ORIGINS: Union[str, List[str]] = (
        "http://localhost:5173,http://localhost:3000"
    )

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cert_verify_db"
    )
    DATABASE_SYNC_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/cert_verify_db"
    )

    REDIS_URL: str = "redis://localhost:6379/0"
    USE_ASYNC_CELERY: bool = False

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "./data/uploads"
    PROCESSED_DIR: str = "./data/processed"
    REPORTS_DIR: str = "./data/reports"
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB

    TESSERACT_CMD: str = ""
    POPPLER_PATH: str = ""
    OCR_DEFAULT_ENGINE: str = "pytesseract"
    MODEL_DEVICE: str = "auto"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
```

---

## 4. Security Constraints

1. **Production Guardrail:** If `ENVIRONMENT=production`, the application must refuse to start if `SECRET_KEY` is equal to the default insecure placeholder.
2. **File Path Sanitation:** When receiving upload requests, filenames must be normalized using `werkzeug.utils.secure_filename` or replaced with unique UUIDs (`{uuid4()}{ext}`) to prevent directory traversal attacks (`../../etc/passwd`).
3. **Storage Access:** Uploaded documents contain PII and must never be served directly through unauthenticated static file routing. All file downloads must pass through authenticated FastAPI endpoints.
