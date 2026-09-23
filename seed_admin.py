#!/usr/bin/env python3
"""
Database Seeder Script: Seed / Reset Initial Administrator Account.
Usage:
    python seed_admin.py [--email admin@certishield.ai] [--password Admin@123456] [--name "System Administrator"]
"""

import argparse
import sys
from pathlib import Path

# Setup Python paths
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import Base, engine, SessionLocal
from app.models.user import AppUserModel
from app.core.security import get_password_hash
from sqlalchemy.orm import Session


def seed_admin(
    email: str = "admin@certishield.ai",
    password: str = "Admin@123456",
    name: str = "System Administrator",
) -> None:
    """Create or update the initial platform administrator account."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    from app.database import SessionLocal

    db: Session = SessionLocal()
    try:
        normalized_email = email.strip().lower()
        pwd_hash = get_password_hash(password)

        existing_user = db.query(AppUserModel).filter_by(email=normalized_email).first()

        if existing_user:
            print(f"[*] Admin account '{normalized_email}' already exists. Updating credentials and ensuring role='admin'...")
            existing_user.full_name = name
            existing_user.password_hash = pwd_hash
            existing_user.role = "admin"
            existing_user.is_active = True
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
    parser.add_argument("--email", default="admin@certishield.ai", help="Admin email address")
    parser.add_argument("--password", default="Admin@123456", help="Admin password (min 8 chars, 1 uppercase, 1 digit, 1 special)")
    parser.add_argument("--name", default="System Administrator", help="Admin full name")
    args = parser.parse_args()

    seed_admin(email=args.email, password=args.password, name=args.name)
