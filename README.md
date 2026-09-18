# AI-Based Detection of Fake or Manipulated Academic Certificates

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3118/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com)

An AI-assisted, multi-stage authenticity assessment platform for verifying academic degrees, transcripts, and credentials through a combination of optical character recognition (OCR), forensic image error level analysis (ELA), copy-move cloning detection, text consistency rules, and multimodal machine learning score fusion.

---

## Architecture Overview

```text
Certificate Upload (JPG/PNG/PDF)
        ↓
   File Validation & Ingestion
        ↓
   Image Preprocessing (Deskew, Denoise, Contrast Enhancement)
        ↓
   OCR Extraction & Field Parsing
        ↓
   ┌─────────────────────── Parallel Analysis ───────────────────────┐
   │                                                                 │
   │  Text Consistency Analysis           Image Forensics            │
   │  • Date chronological logic          • Error Level Analysis     │
   │  • Grade format checks               • Copy-move tampering      │
   │  • Certificate number regex          • Font & noise anomalies   │
   │                                                                 │
   └───────────────────────────────┬─────────────────────────────────┘
                                   ↓
                  Template & Student Record Matching
                                   ↓
                  Multimodal ML/DL Risk Classification
                                   ↓
                  Weighted Score Fusion & Explainability (SHAP)
                                   ↓
                  Downloadable Verification Report & Overlays
```

---

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/             # REST endpoints (health, ingestion, verification, admin)
│   │   ├── core/               # App configuration, security, base exceptions
│   │   ├── database.py         # SQLAlchemy 2.0 engine & session dependency
│   │   ├── models/             # SQLAlchemy ORM database models
│   │   ├── modules/            # Analysis pipeline processing modules
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
│   │   ├── schemas/            # Canonical Pydantic V2 data contracts
│   │   ├── services/           # Business logic & background task services
│   │   ├── main.py             # FastAPI entrypoint & lifecycle manager
│   │   └── config.py           # Environment settings manager
│   ├── tests/                  # Pytest test suite
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # View pages (Upload, Results, History, Admin)
│   │   ├── services/           # Axios API services
│   │   ├── types/              # TypeScript pipeline interfaces
│   │   ├── App.tsx             # Root React shell
│   │   └── main.tsx            # Vite entrypoint
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── ml/                         # Machine learning models, training scripts & notebooks
├── storage/                    # Local runtime storage (uploads, preprocessed, reports)
├── datasets/                   # Synthetic dataset generator & benchmark datasets
├── development-plan/           # Comprehensive 22-phase implementation roadmap
└── docs/                       # PRD, SRD, Design Docs, and Technical Specifications
```

---

## Quick Start

### 1. Prerequisites
- **Python:** 3.11+
- **Node.js:** 18+ (20 LTS recommended)
- **uv:** (Recommended for Python environment) or standard `python3 -m venv`

### 2. Backend Setup
```bash
# Create virtual environment with Python 3.11
uv venv --python 3.11 .venv
source .venv/bin/activate

# Install backend dependencies
uv pip install -r backend/requirements.txt

# Run test suite
pytest backend/tests/ -v

# Start backend server
uvicorn backend.app.main:app --reload --port 8000
```
- API Swagger Documentation: `http://localhost:8000/docs`
- Service Health Check: `http://localhost:8000/health`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:5173`

---

## Verification & Quality Assurance
- Python Linting: `ruff check backend/`
- Python Formatting: `ruff format backend/`
- Test Suite: `pytest backend/tests/ -v --cov=backend/app`