# Database Migration Guide: SQLite to Cloud Firestore

**Project:** AI-Based Detection of Fake or Manipulated Academic Certificates  

---

## 1. Migration Overview

The migration suite extracts records from the local relational SQLite database (`dev.db`) and transforms them into Firestore document collections (`users`, `certificates`, `course_verifications`, and `audit_logs`).

---

## 2. Running the Migration

### Step 1: Execute Data Export / Live Sync
```bash
.\.venv\Scripts\python.exe migration/export_sqlite_to_firestore.py
```
- If Google Cloud Application Default Credentials (`GOOGLE_APPLICATION_CREDENTIALS`) are configured, records are directly written to Cloud Firestore.
- If running offline or in restricted dev mode, records are exported to `migration/backup_export.json` for validation and batch upload.

### Step 2: Verify Parity
```bash
.\.venv\Scripts\python.exe migration/verify_migration.py
```
This script validates:
- Parity between SQLite table rows and Firestore collection documents.
- Discrepancy reporting and integrity status.
