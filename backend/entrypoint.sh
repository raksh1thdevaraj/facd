#!/usr/bin/env bash
set -e

echo "=== [CertCheck Backend] Starting Production Runtime ==="

# Execute database migrations if alembic configuration is present
if [ -f "/app/alembic.ini" ]; then
    echo "Running database migrations via Alembic..."
    alembic upgrade head || echo "Notice: Alembic migrations skipped or already current."
fi

# Ensure storage runtime directories exist
mkdir -p /app/storage/uploads /app/storage/preprocessed /app/storage/reports /app/storage/templates

# Determine worker count (default to 4 or CPU count)
WORKERS=${WEB_CONCURRENCY:-4}

echo "Launching Uvicorn server on port 8000 with ${WORKERS} worker(s)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${WORKERS}" --proxy-headers --forwarded-allow-ips='*'
