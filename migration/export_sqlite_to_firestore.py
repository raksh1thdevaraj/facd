"""Migration script: Export existing SQLite records to Cloud Firestore collections."""

import json
import logging
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.core.firebase import get_firestore_client
from app.database import SessionLocal
from app.models.certificate import CertificateModel
from app.models.course_verification import CourseCertificateVerificationModel
from app.models.report import VerificationReportModel
from app.models.template import InstitutionModel
from app.models.user import AppUserModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")


def export_sqlite_to_firestore():
    logger.info("Initializing SQLite session and Firestore client...")
    db = SessionLocal()
    fs = get_firestore_client()

    if not fs:
        logger.warning(
            "Firestore client could not be initialized directly. "
            "Exporting records to migration/backup_export.json for offline or CLI import."
        )
        backup_data = {"users": [], "institutions": [], "certificates": [], "course_verifications": []}
        for u in db.query(AppUserModel).all():
            backup_data["users"].append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "institution_id": u.institution_id,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            })
        for c in db.query(CertificateModel).all():
            backup_data["certificates"].append({
                "id": c.id,
                "user_id": c.user_id,
                "file_hash": c.file_hash,
                "original_filename": c.original_filename,
                "file_size": c.file_size,
                "mime_type": c.mime_type,
                "job_status": c.job_status,
                "job_progress": c.job_progress,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
        for cv in db.query(CourseCertificateVerificationModel).all():
            backup_data["course_verifications"].append({
                "id": cv.id,
                "user_id": cv.user_id,
                "file_hash": cv.file_hash,
                "original_filename": cv.original_filename,
                "issuer": cv.issuer,
                "authenticity_score": cv.authenticity_score,
                "fraud_risk_score": cv.fraud_risk_score,
                "final_status": cv.final_status,
                "created_at": cv.created_at.isoformat() if cv.created_at else None,
            })

        out_path = Path(__file__).resolve().parent / "backup_export.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2)
        logger.info("Exported %d users, %d certificates, %d course verifications to %s",
                    len(backup_data["users"]), len(backup_data["certificates"]), len(backup_data["course_verifications"]), out_path)
        return

    # Direct migration to live Firestore
    # 1. Users
    users = db.query(AppUserModel).all()
    logger.info("Migrating %d users to 'users' collection...", len(users))
    for user in users:
        doc_data = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "institution_id": user.institution_id,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        fs.collection("users").document(user.id).set(doc_data, merge=True)

    # 2. Certificates
    certs = db.query(CertificateModel).all()
    logger.info("Migrating %d certificates to 'certificates' collection...", len(certs))
    for cert in certs:
        doc_data = {
            "id": cert.id,
            "user_id": cert.user_id,
            "file_hash": cert.file_hash,
            "original_filename": cert.original_filename,
            "file_size": cert.file_size,
            "mime_type": cert.mime_type,
            "job_status": cert.job_status,
            "job_progress": cert.job_progress,
            "created_at": cert.created_at.isoformat() if cert.created_at else None,
        }
        fs.collection("certificates").document(cert.id).set(doc_data, merge=True)

    # 3. Course Verifications
    course_records = db.query(CourseCertificateVerificationModel).all()
    logger.info("Migrating %d course verifications to 'course_verifications' collection...", len(course_records))
    for rec in course_records:
        doc_data = {
            "id": rec.id,
            "user_id": rec.user_id,
            "file_hash": rec.file_hash,
            "original_filename": rec.original_filename,
            "issuer": rec.issuer,
            "authenticity_score": rec.authenticity_score,
            "fraud_risk_score": rec.fraud_risk_score,
            "final_status": rec.final_status,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
        }
        fs.collection("course_verifications").document(rec.id).set(doc_data, merge=True)

    logger.info("Migration to Cloud Firestore completed successfully!")
    db.close()


if __name__ == "__main__":
    export_sqlite_to_firestore()
