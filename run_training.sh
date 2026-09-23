#!/bin/bash
# Multi-Modal Lightweight Certificate Fraud Detection Training Script
# Executes data indexing, SMOTE resampling, MobileNetV2 transfer learning, and report export.

set -e

echo "================================================================================"
echo "Starting Academic Certificate Fraud Detection Training Pipeline"
echo "================================================================================"

export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1

# Use virtual environment python if present
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON_BIN=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="python"
fi

echo "[*] Using Python: $PYTHON_BIN"

# Execute master training script
$PYTHON_BIN train_all.py "$@"

echo "================================================================================"
echo "Pipeline finished successfully. All models exported to ./models/ and ./reports/"
echo "================================================================================"
