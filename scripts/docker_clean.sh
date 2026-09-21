#!/usr/bin/env bash
set -e

# ==============================================================================
# Docker System Cleanup & Disk Pruning Utility (CHIP DEP-10)
# Safely reclaims disk space while preserving active named data volumes.
# ==============================================================================

echo "========================================================================"
echo ">>> [CertCheck AI] Docker Disk Cleanup & Pruning Utility"
echo "========================================================================"

echo "Removing stopped containers..."
docker container prune -f

echo "Removing dangling and untagged images..."
docker image prune -f

echo "Pruning stale build cache..."
docker builder prune -f

echo "Disk cleanup complete. Active database and storage volumes preserved."
