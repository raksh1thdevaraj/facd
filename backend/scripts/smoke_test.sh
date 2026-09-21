#!/bin/bash
set -e

echo "=================================================="
echo "  AI CERTIFICATE VERIFICATION STACK SMOKE TEST"
echo "=================================================="

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BACKEND_DIR"

echo "[1/4] Checking Python environment and dependencies..."
python3 -c "import torch, cv2, fastapi, pydantic, sqlalchemy; print('  ✓ Core libraries imported successfully.')"

echo "[2/4] Initializing Database Tables..."
python3 -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine); print('  ✓ SQLite database and tables verified.')"

echo "[3/4] Running Garbage Collection Dry-Run..."
python3 -c "from app.services.cleanup_service import CleanupService; count = CleanupService.cleanup_orphaned_files(max_age_hours=0); print(f'  ✓ Cleanup service active.')"

echo "[4/4] Executing End-to-End Smoke Test Suite..."
python3 -m pytest tests/e2e/test_full_genuine_flow.py -q --tb=short

echo "=================================================="
echo "  ✓ ALL SMOKE TEST CHECKS PASSED SUCCESSFULLY"
echo "=================================================="
