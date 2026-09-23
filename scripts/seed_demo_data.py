"""
Database Seed Script: Populates realistic academic certificate scans,
course credentials, and registrar behavioral access logs.
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add repo root and backend directory to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.database import SessionLocal, engine, Base
from app.models.course_verification import CourseCertificateVerificationModel
from app.models.user import AppUserModel
from app.api.v1.endpoints.verification_hub import RECENT_SCANS_CACHE
from src.behavioral_monitor import BehavioralMonitor


def seed_data():
    print("[*] Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Default Admin User if not present
        admin_user = db.query(AppUserModel).filter(AppUserModel.email == "admin@certishield.ai").first()
        if not admin_user:
            admin_user = AppUserModel(
                id=str(uuid.uuid4()),
                email="admin@certishield.ai",
                full_name="System Administrator & Forensic Lead",
                role="admin",
                is_active=True,
                password_hash="mock_admin_pbkdf2_hash",
            )
            db.add(admin_user)
            print("[+] Seeded Admin user: admin@certishield.ai / admin123")

        # 2. Seed Realistic Certificate Verification Scans
        sample_scans = [
            {
                "id": str(uuid.uuid4()),
                "filename": "heritage_univ_btech_cse_aarav_sharma.pdf",
                "cert_type": "marks_card",
                "status": "VERIFIED",
                "score": 0.985,
                "latency": 118.4,
                "payload": "https://certishield.edu/records/HTU2022-CS-041|Aarav Sharma|HTU2022-CS-041",
            },
            {
                "id": str(uuid.uuid4()),
                "filename": "stanford_deep_learning_spec_priya_nair.png",
                "cert_type": "course_certificate",
                "status": "VERIFIED",
                "score": 0.978,
                "latency": 94.2,
                "payload": "https://coursera.org/verify/specialization/CRS-DL-889102",
            },
            {
                "id": str(uuid.uuid4()),
                "filename": "spliced_marks_card_sem6_tampered.png",
                "cert_type": "marks_card",
                "status": "REJECTED",
                "score": 0.384,
                "latency": 142.1,
                "payload": "https://certishield.edu/records/TAMPERED-001",
                "reasons": [
                    "Text baseline horizontal variance (4.82px > 1.2px) indicates spliced grades",
                    "Discrepancy detected between document text and QR cryptographic payload",
                ],
            },
            {
                "id": str(uuid.uuid4()),
                "filename": "fakeed_academy_cyber_security_forgery.pdf",
                "cert_type": "course_certificate",
                "status": "REJECTED",
                "score": 0.312,
                "latency": 131.6,
                "payload": "https://phish-certs.ru/verify/fake-991",
                "reasons": [
                    "QR code destination points to an unaccredited or untrusted domain: phish-certs.ru",
                    "DIAR-AI structural template mismatch (SSIM: 0.64 < 0.85)",
                ],
            },
            {
                "id": str(uuid.uuid4()),
                "filename": "borderline_scan_low_contrast_marks.jpg",
                "cert_type": "marks_card",
                "status": "SUSPICIOUS",
                "score": 0.792,
                "latency": 164.8,
                "payload": None,
                "warnings": [
                    "No institutional QR code found for cryptographic cross-verification",
                    "Borderline structural similarity (SSIM: 0.812)",
                ],
            },
        ]

        now = datetime.now(timezone.utc)
        for i, s in enumerate(sample_scans):
            t_offset = now - timedelta(hours=i * 4, minutes=i * 12)
            existing = db.query(CourseCertificateVerificationModel).filter(
                CourseCertificateVerificationModel.original_filename == s["filename"]
            ).first()

            if not existing:
                record = CourseCertificateVerificationModel(
                    id=s["id"],
                    uploaded_file_path=f"storage/uploads/verify/{s['filename']}",
                    file_hash=uuid.uuid4().hex,
                    original_filename=s["filename"],
                    file_size=1024 * (120 + i * 45),
                    mime_type="application/pdf" if s["filename"].endswith(".pdf") else "image/png",
                    job_status="COMPLETED",
                    final_status=s["status"],
                    authenticity_score=s["score"],
                    fraud_risk_score=round(1.0 - s["score"], 3),
                    verification_url=s["payload"],
                    qr_data_json={
                        "qr_detected": bool(s["payload"]),
                        "domain_valid": bool(s["status"] == "VERIFIED"),
                        "url": s["payload"],
                    },
                    evidence_summary_json={
                        "rejection_reasons": s.get("reasons", []),
                        "warnings": s.get("warnings", []),
                        "latency_ms": s["latency"],
                    },
                )
                db.add(record)

            # Also populate in-memory scan cache
            RECENT_SCANS_CACHE.append({
                "id": s["id"],
                "filename": s["filename"],
                "certificate_type": s["cert_type"],
                "final_status": s["status"],
                "verdict_badge": s["status"],
                "color": "emerald" if s["status"] == "VERIFIED" else ("amber" if s["status"] == "SUSPICIOUS" else "red"),
                "is_authentic": s["status"] == "VERIFIED",
                "confidence_score": s["score"],
                "latency_ms": s["latency"],
                "rejection_reasons": s.get("reasons", []),
                "warnings": s.get("warnings", []),
                "timestamp": t_offset.isoformat(),
            })

        db.commit()
        print(f"[+] Successfully seeded {len(sample_scans)} verification scans into database and cache.")

    except Exception as exc:
        db.rollback()
        print(f"[!] Error seeding data: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
