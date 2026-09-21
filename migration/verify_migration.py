"""Verification script: Compares SQLite record counts against Firestore documents."""

import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.firebase import get_firestore_client
from app.database import SessionLocal
from app.models.certificate import CertificateModel
from app.models.course_verification import CourseCertificateVerificationModel
from app.models.user import AppUserModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_migration")


def verify_migration():
    db = SessionLocal()
    fs = get_firestore_client()

    sqlite_users_count = db.query(AppUserModel).count()
    sqlite_certs_count = db.query(CertificateModel).count()
    sqlite_course_count = db.query(CourseCertificateVerificationModel).count()

    print("=" * 60)
    print("MIGRATION INTEGRITY REPORT")
    print("=" * 60)
    print(f"SQLite Records:")
    print(f"  - App Users:            {sqlite_users_count}")
    print(f"  - Certificates:         {sqlite_certs_count}")
    print(f"  - Course Verifications: {sqlite_course_count}")

    if not fs:
        print("\n[NOTE] Direct Cloud Firestore client requires GOOGLE_APPLICATION_CREDENTIALS in environment.")
        print("Backup JSON was generated for offline review in migration/backup_export.json.")
        db.close()
        return

    try:
        fs_users = len(list(fs.collection("users").stream()))
        fs_certs = len(list(fs.collection("certificates").stream()))
        fs_course = len(list(fs.collection("course_verifications").stream()))

        print(f"\nFirestore Collections:")
        print(f"  - users:                {fs_users}")
        print(f"  - certificates:         {fs_certs}")
        print(f"  - course_verifications: {fs_course}")

        print("\nDiscrepancy Check:")
        print(f"  - Users Delta:          {sqlite_users_count - fs_users}")
        print(f"  - Certificates Delta:   {sqlite_certs_count - fs_certs}")
        print(f"  - Course Recs Delta:    {sqlite_course_count - fs_course}")
    except Exception as exc:
        print(f"\nCould not stream collections from Firestore: {exc}")

    db.close()


if __name__ == "__main__":
    verify_migration()
