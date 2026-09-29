#!/usr/bin/env python3
"""
Database Seeder Script: Seed / Reset Initial Administrator Account.
Usage:
    python backend/scripts/seed_admin.py [--email admin@certishield.ai] [--password Admin@123456] [--name "System Administrator"]
"""

import argparse
import sys
from pathlib import Path

# Setup Python paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import Base, engine, SessionLocal
from app.models.user import AppUserModel
from app.core.security import get_password_hash
from sqlalchemy.orm import Session


def seed_admin(
    email: str = "admin",
    password: str = "12345678",
    name: str = "admin",
) -> None:
    """Create or update the initial platform administrator account."""
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        normalized_email = email.strip().lower()
        pwd_hash = get_password_hash(password)

        existing_user = db.query(AppUserModel).filter_by(email=normalized_email).first()

        if existing_user:
            print(f"[*] Admin account '{normalized_email}' already exists. Updating credentials and ensuring role='admin'...")
            setattr(existing_user, "full_name", name)
            setattr(existing_user, "password_hash", pwd_hash)
            setattr(existing_user, "role", "admin")
            setattr(existing_user, "is_active", True)
            db.commit()
            db.refresh(existing_user)
            print(f"[+] Successfully updated Admin account: {existing_user.email} (ID: {existing_user.id})")
        else:
            new_admin = AppUserModel(
                email=normalized_email,
                full_name=name,
                password_hash=pwd_hash,
                role="admin",
                is_active=True,
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print(f"[+] Successfully created initial Admin account: {new_admin.email} (ID: {new_admin.id})")

        print("=" * 60)
        print("  ADMIN CREDENTIALS FOR TESTING & DEMO AUDITS")
        print("=" * 60)
        print(f"  Email:    {normalized_email}")
        print(f"  Password: {password}")
        print(f"  Role:     admin")
        print(f"  Access:   /admin (Supervisory Forensics Console)")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed initial admin user account for CertiShield AI.")
    parser.add_argument("--email", default="admin", help="Admin username or email address")
    parser.add_argument("--password", default="12345678", help="Admin password")
    parser.add_argument("--name", default="admin", help="Admin display name")
    args = parser.parse_args()

    seed_admin(email=args.email, password=args.password, name=args.name)
