#!/usr/bin/env bash
set -e

# ==============================================================================
# Master Single-Command Production Deployment Script (CHIP DEP-09)
# Validates prerequisites, pulls changes, builds containers, and executes smoke tests.
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "========================================================================"
echo ">>> [CertCheck AI] Starting Production Stack Deployment"
echo "========================================================================"

# Check Docker and Docker Compose prerequisites
command -v docker >/dev/null 2>&1 || { echo "Error: docker is required but not installed."; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Error: docker compose v2 is required."; exit 1; }

# Check environment configuration
if [ ! -f ".env" ] && [ ! -f ".env.production" ]; then
    echo "Notice: Neither .env nor .env.production found. Creating from .env.production.example..."
    cp .env.production.example .env.production
    echo "Created .env.production. Please edit it with real secrets before running in production!"
fi

# Ensure storage directories exist locally
mkdir -p storage/uploads storage/preprocessed storage/reports storage/templates ml/models nginx/ssl backups

# Execute Docker Compose production build and startup
echo "Building and launching containers..."
if [ -f "docker-compose.prod.yml" ]; then
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans
else
    docker compose up -d --build --remove-orphans
fi

echo "Waiting for services to become healthy..."
sleep 10

# Execute smoke tests
if [ -f "scripts/smoke_test.sh" ]; then
    bash scripts/smoke_test.sh
fi

echo "========================================================================"
echo ">>> [CertCheck AI] Stack Deployed Successfully!"
echo "    Gateway (HTTP): http://localhost"
echo "    Backend Health: http://localhost/health"
echo "    API Docs:       http://localhost/docs"
echo "========================================================================"
