#!/usr/bin/env bash
# ==============================================================================
# Automated All-In-One Test & Evaluation Script (Phase 19 - CHIP TST-10)
# ==============================================================================
set -e

echo "=== [1/5] Running Requirements Traceability Audit ==="
python backend/scripts/verify_traceability.py

echo "=== [2/5] Running Backend Unit, Integration & E2E Test Suite ==="
pytest backend/tests/ -v --cov=backend/app --cov-config=backend/.coveragerc --cov-report=term-missing

echo "=== [3/5] Running Model Evaluation Benchmark ==="
python ml/evaluation/benchmark_runner.py

echo "=== [4/5] Rendering Publication-Grade Charts ==="
python ml/evaluation/chart_generator.py

echo "=== [5/5] Synthesizing Formal Evaluation Report ==="
python ml/evaluation/report_writer.py

echo "=== All Tests & Scientific Benchmarks Completed Successfully! ==="
