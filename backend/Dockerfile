# ==============================================================================
# Multi-Stage Production Dockerfile for FastAPI Backend
# Base Image: Python 3.11 Slim Bookworm
# Hardened: Non-root execution (appuser:10001), Minimal runtime footprint
# ==============================================================================

# --- STAGE 1: Dependency Builder ---
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies for C-extensions and PostgreSQL driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and populate isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt


# --- STAGE 2: Hardened Production Runtime ---
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Install system runtime libraries (Poppler for PDF rasterization, OpenGL/GOMP for OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

# Create non-privileged user and group
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -d /app -s /bin/bash -m appuser

# Pre-create runtime storage and models directories with proper permissions
RUN mkdir -p /app/storage/uploads \
             /app/storage/preprocessed \
             /app/storage/reports \
             /app/storage/templates \
             /app/ml/models && \
    chown -R appuser:appuser /app

# Copy application source code
COPY --chown=appuser:appuser . /app

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Drop root privileges
USER appuser

EXPOSE 8000

# Health check verifying backend liveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
