# AI Developer Rules of Engagement & Execution Guidelines

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  
**Target:** Autonomous AI Coding Assistants, LLM Agents & Pair Programmers  
**Authority:** Authoritative Project Standard  

---

## 1. Core Principles & Philosophy

As an AI developer implementing this codebase, you must adhere strictly to these principles:
1. **Zero Placeholder Code:** Never write `# TODO: implement this later`, dummy stub functions returning fake hardcoded outputs, or empty classes. Every phase must produce fully functional, tested, and robust code.
2. **Deterministic Data Contracts:** All internal pipeline models and API contracts must adhere strictly to [`docs/specs/02_PIPELINE_DATA_CONTRACTS.md`](file:///Users/apple/Codes/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/docs/specs/02_PIPELINE_DATA_CONTRACTS.md) and [`docs/specs/05_API_OPENAPI_SPEC.yaml`](file:///Users/apple/Codes/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/docs/specs/05_API_OPENAPI_SPEC.yaml). Never invent arbitrary field names or return shapes.
3. **Phased Execution Discipline:** Follow the roadmap laid out in [`development-plan/00_MASTER_DEVELOPMENT_PLAN.md`](file:///Users/apple/Codes/AI-Based-Detection-of-Fake-or-Manipulated-Academic-Certificates/development-plan/00_MASTER_DEVELOPMENT_PLAN.md) step by step. Do not skip phases or attempt to write frontend code before backend pipeline foundations are solid and tested.
4. **Graceful Degradation:** The system must run smoothly in restricted environments (e.g., standard CPU with no GPU, missing Redis, or missing optional OCR packages). Provide clean fallbacks rather than crashing.

---

## 2. Directory Layout & Architecture Enforcement

All source code must be created in the following canonical structure:

```text
.
├── backend/
│   ├── src/
│   │   ├── core/               # App configuration, security, database session
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic V2 schemas (from SPEC-02)
│   │   ├── pipeline/           # Sequential verification pipeline
│   │   │   ├── ingestion.py
│   │   │   ├── preprocessing.py
│   │   │   ├── ocr_engine.py
│   │   │   ├── text_consistency.py
│   │   │   ├── forensics.py
│   │   │   ├── template_matcher.py
│   │   │   ├── ml_classifier.py
│   │   │   └── score_fusion.py
│   │   ├── services/           # Business logic, PDF generator, report service
│   │   ├── api/                # FastAPI routers (v1 endpoints)
│   │   └── main.py             # FastAPI entrypoint
│   └── tests/                  # Pytest unit, integration, and E2E tests
├── frontend/                   # React + Vite + TypeScript web interface
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── datasets/                   # Synthetic dataset generator & samples
├── docs/                       # PRD, SRD, Design Docs, and specs/
└── AGENTS.md                   # This file
```

---

## 3. Definition of Done (DoD) per Phase

Before completing any phase from the master development plan, you must ensure:
- [ ] Code is formatted with `ruff format` and conforms to `ruff check`.
- [ ] All functions and classes contain clear docstrings explaining inputs and outputs.
- [ ] Complete type annotations are provided (strictly typed Python / TypeScript).
- [ ] Automated tests covering new functionality are added to `tests/` and pass with `pytest`.
- [ ] Edge cases (corrupt files, empty inputs, extreme skew angles, low-contrast text) are handled with appropriate error envelopes.

---

## 4. Coding Standards

### 4.1 Python Standards
- **Python Version:** 3.11+
- **Typing:** Use modern standard library types (`list[str]`, `dict[str, Any]`, `tuple[int, int]`, `Optional[str] = None`).
- **Error Handling:** Avoid bare `except:`. Catch specific exceptions (`cv2.error`, `ValueError`, `PyTesseractError`) and raise descriptive HTTPException or log structured warnings.
- **Path Handling:** Always use `pathlib.Path` instead of raw string manipulation for file paths.

### 4.2 TypeScript & React Standards
- **TypeScript:** Strict mode enabled. No `any` types; define explicit interfaces in `types/`.
- **UI Components:** Use TailwindCSS for responsive, modern design with clean dark/light contrast.
- **State Management:** Keep state close to components; use typed custom hooks for API calls and async job polling.

---

## 5. Environment & Hardware Adaptation Rules

1. **When GPU is unavailable:** Set `torch.device("cpu")` automatically; do not fail or raise device errors.
2. **When Celery/Redis is not running:** Fallback immediately to FastAPI's built-in `BackgroundTasks` if `USE_ASYNC_CELERY=False` in `.env`.
3. **When Tesseract binary is not on default PATH:** Read `TESSERACT_CMD` from environment settings. If completely unavailable during testing, rely on mock OCR token fixtures.
