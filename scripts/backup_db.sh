#!/usr/bin/env bash
set -e

# ==============================================================================
# Automated Database Backup Script (CHIP DEP-08)
# Dumps PostgreSQL database into compressed archive with 7-day retention.
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

CONTAINER_NAME="${DB_CONTAINER:-cert_verify_db}"
DB_NAME="${POSTGRES_DB:-cert_verification_db}"
DB_USER="${POSTGRES_USER:-postgres}"

echo "Starting database backup for '${DB_NAME}' from container '${CONTAINER_NAME}'..."

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"
    echo "Backup successfully written to: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"
else
    echo "Error: Database container '${CONTAINER_NAME}' is not running."
    exit 1
fi

# Retention policy: Prune backups older than 7 days
echo "Applying 7-day retention pruning..."
find "${BACKUP_DIR}" -name "db_backup_*.sql.gz" -type f -mtime +7 -exec rm -f {} \;
echo "Backup procedure completed successfully."
