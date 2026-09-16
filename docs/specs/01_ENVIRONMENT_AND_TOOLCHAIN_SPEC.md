# Environment & Toolchain Specification

## AI-Based Detection of Fake or Manipulated Academic Certificates

**Document ID:** SPEC-01  
**Status:** Approved / Authoritative  
**Target Runtime:** Python 3.11+ / Node.js 20 LTS  

---

## 1. Purpose & Scope

This specification provides the exact, deterministic environment, system packages, runtimes, and pinned libraries required to develop, run, and test the system. An AI developer or automated CI/CD agent must adhere strictly to these versions to prevent environment discrepancies, runtime crashes with native libraries (OpenCV, Tesseract, Poppler), or packaging incompatibilities.

---

## 2. System-Level Dependencies & Binaries

The system relies on image processing, PDF rasterization, and OCR binaries that must be installed on the host operating system before running Python code.

### 2.1 macOS (Darwin) Installation
```bash
brew update
brew install tesseract
brew install tesseract-lang  # Multi-language training data (eng, osd)
brew install poppler         # pdftoppm, pdfinfo (for pdf2image)
brew install redis           # For async task broker
brew install postgresql@15   # Core relational database
```

### 2.2 Linux / Ubuntu (Debian 12+ / Ubuntu 22.04 LTS) Installation
```bash
apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    pkg-config \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    redis-server \
    libpq-dev
```

### 2.3 Verification Commands
The AI developer must run these verification commands before executing the backend:
```bash
tesseract --version    # Expected: tesseract >= 5.3.0
pdftoppm -v            # Expected: pdftoppm version >= 22.0.0
python3 --version      # Expected: Python 3.11.x
node -v                # Expected: v20.x.x
npm -v                 # Expected: >= 10.x.x
```

---

## 3. Backend Python Environment

### 3.1 Python Version
- **Canonical Version:** `3.11.8` (Minimum: `3.11.0`, Maximum: `< 3.12.0` due to PyTorch and EasyOCR C-extension compatibility).

### 3.2 Pinned `requirements.txt` / Dependency Specification

```text
# --- Web API & Async Server ---
fastapi==0.110.0
uvicorn[standard]==0.28.0
pydantic==2.6.4
pydantic-settings==2.2.1
python-multipart==0.0.9

# --- Database & Storage ---
sqlalchemy==2.0.28
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
redis==5.0.3
celery==5.3.6

# --- Image Processing & CV ---
opencv-python-headless==4.9.0.80
pillow==10.2.0
scikit-image==0.22.0
pdf2image==1.17.0
numpy==1.26.4
scipy==1.12.0

# --- OCR Engines ---
pytesseract==0.3.10
easyocr==1.7.1

# --- Machine Learning & Forensics ---
torch==2.2.1; sys_platform != 'darwin'
torchvision==0.17.1; sys_platform != 'darwin'
# macOS Apple Silicon acceleration
torch==2.2.1; sys_platform == 'darwin'
torchvision==0.17.1; sys_platform == 'darwin'
scikit-learn==1.4.1.post1
xgboost==2.0.3
shap==0.45.0

# --- PDF Generation & Reporting ---
reportlab==4.1.0
matplotlib==3.8.3

# --- Security & Auth ---
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2

# --- Testing & Quality ---
pytest==8.1.1
pytest-asyncio==0.23.5
pytest-cov==4.1.0
httpx==0.27.0
ruff==0.3.3
mypy==1.9.0
```

---

## 4. Frontend Web Environment

### 4.1 Node & Package Manager
- **Node.js:** `20.x` LTS (`>= 20.11.0`)
- **Package Manager:** `npm` (`>= 10.2.0`)

### 4.2 Core Frontend Stack
- **Framework:** React 18 (`react: ^18.2.0`, `react-dom: ^18.2.0`)
- **Build Tool:** Vite (`vite: ^5.1.0`)
- **Language:** TypeScript (`typescript: ^5.3.3`, strict mode enabled)
- **Styling:** TailwindCSS (`tailwindcss: ^3.4.1`, `postcss: ^8.4.35`, `autoprefixer: ^10.4.18`)
- **Component & Icon Primitives:** `lucide-react: ^0.356.0`, `@radix-ui/react-dialog`, `@radix-ui/react-tabs`, `@radix-ui/react-dropdown-menu`
- **HTTP Client:** `axios: ^1.6.7`
- **Data Visualization:** `recharts: ^2.12.2`

---

## 5. Development Tooling & Linters

### 5.1 Python Code Style (Ruff & Mypy)
Create `pyproject.toml` in the backend root:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
disallow_untyped_defs = true
```

### 5.2 TypeScript Code Style
In `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

---

## 6. Docker & Containerized Environment

When running or deploying in Docker, use the following multi-stage base configurations:

### 6.1 Backend Dockerfile Base
```dockerfile
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
```

---

## 7. Graceful Degradation Protocol

When running in development or testing environments where certain hardware or binaries may be absent, the system **must** adhere to the following fallback protocols:

1. **GPU Acceleration:** Detect `torch.cuda.is_available()`, fallback to Apple Silicon `torch.backends.mps.is_available()`, and ultimately CPU inference (`torch.device("cpu")`).
2. **Celery/Redis Broker:** If `REDIS_URL` is unreachable or unconfigured, the backend must support synchronous in-process pipeline execution via FastAPI `BackgroundTasks`.
3. **Tesseract Executable:** Check if `which tesseract` exists; allow overriding via `TESSERACT_CMD` environment variable. If missing during unit tests, mock OCR response fixtures must be used.
