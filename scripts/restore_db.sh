#!/usr/bin/env bash
set -e

# ==============================================================================
# Database Disaster Recovery Restoration Script (CHIP DEP-08)
# Restores PostgreSQL database from a specified compressed backup archive.
# ==============================================================================

if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_backup_archive.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Specified backup file '${BACKUP_FILE}' not found."
    exit 1
fi

CONTAINER_NAME="${DB_CONTAINER:-cert_verify_db}"
DB_NAME="${POSTGRES_DB:-cert_verification_db}"
DB_USER="${POSTGRES_USER:-postgres}"

echo "WARNING: Restoring will overwrite existing tables in database '${DB_NAME}'."
read -p "Are you sure you want to proceed? [y/N]: " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Restoration cancelled by user."
    exit 0
fi

echo "Restoring database from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}"

echo "Database restoration completed successfully."
