#!/usr/bin/env bash
set -e

# ==============================================================================
# Production Deployment Smoke Test (CHIP DEP-09)
# Verifies health endpoints, gateway routing, and frontend accessibility.
# ==============================================================================

GATEWAY_URL="${TARGET_HOST:-http://localhost}"

echo ">>> Running Post-Deployment Smoke Tests against ${GATEWAY_URL}..."

# 1. Backend Health Check
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/health" || echo "000")
if [ "$HEALTH_CODE" -eq 200 ]; then
    echo "  [PASS] Backend health check (/health) responded HTTP 200"
else
    echo "  [FAIL] Backend health check (/health) returned HTTP ${HEALTH_CODE}"
    exit 1
fi

# 2. Frontend Accessibility Check
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/" || echo "000")
if [ "$FRONTEND_CODE" -eq 200 ]; then
    echo "  [PASS] Frontend application root (/) responded HTTP 200"
else
    echo "  [FAIL] Frontend application root (/) returned HTTP ${FRONTEND_CODE}"
    exit 1
fi

# 3. Interactive API Documentation
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${GATEWAY_URL}/docs" || echo "000")
if [ "$DOCS_CODE" -eq 200 ]; then
    echo "  [PASS] API documentation (/docs) responded HTTP 200"
else
    echo "  [WARN] API documentation (/docs) returned HTTP ${DOCS_CODE}"
fi

echo ">>> All critical smoke tests PASSED."
