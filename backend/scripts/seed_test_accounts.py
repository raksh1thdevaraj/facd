#!/usr/bin/env python3
"""
Seed backend database with test admin and user accounts.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import Base, engine, SessionLocal
from app.models.user import AppUserModel
from app.core.security import get_password_hash

test_accounts = [
    {
        "email": "admin@facd.edu",
        "password": "AdminPassword123!",
        "name": "System Administrator (VTU)",
        "role": "admin",
    },
    {
        "email": "admin@certishield.ai",
        "password": "AdminPassword123!",
        "name": "Platform Administrator",
        "role": "admin",
    },
    {
        "email": "verifier@vtu.ac.in",
        "password": "UserPassword123!",
        "name": "Dr. Ramesh Rao (VTU Examiner)",
        "role": "user",
    },
    {
        "email": "pending.user@vtu.ac.in",
        "password": "UserPassword123!",
        "name": "Pooja Sharma (New Applicant)",
        "role": "user",
    },
]

def seed_backend():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for acc in test_accounts:
            email = acc["email"].strip().lower()
            pwd_hash = get_password_hash(acc["password"])
            existing = db.query(AppUserModel).filter_by(email=email).first()
            if existing:
                existing.full_name = acc["name"]
                existing.password_hash = pwd_hash
                existing.role = acc["role"]
                existing.is_active = True
                print(f"[+] Updated backend account: {email} (role: {acc['role']})")
            else:
                new_u = AppUserModel(
                    email=email,
                    full_name=acc["name"],
                    password_hash=pwd_hash,
                    role=acc["role"],
                    is_active=True,
                )
                db.add(new_u)
                print(f"[+] Created backend account: {email} (role: {acc['role']})")
        db.commit()
        print("\nBackend database seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_backend()
