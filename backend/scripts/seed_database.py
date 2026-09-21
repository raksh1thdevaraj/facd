"""Database seeding script initializing default institutions and test users (CHIP USR-09)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend root is in python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.rbac import UserRole  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.template import InstitutionModel  # noqa: E402
from app.models.user import AppUserModel  # noqa: E402


def seed_database() -> None:
    """Seed initial institutions and default users idempotently."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Institutions
        institutions_data = [
            {
                "id": "inst-nit-001",
                "name": "National Institute of Technology",
                "code": "NIT01",
                "domain": "nit.edu",
                "contact_email": "registrar@nit.edu",
                "address": "National Campus, Tech Corridor 1",
            },
            {
                "id": "inst-stu-002",
                "name": "State Technical University",
                "code": "STU02",
                "domain": "stu.edu",
                "contact_email": "admin@stu.edu",
                "address": "University Road, State Capital",
            },
        ]

        inst_map = {}
        for inst_dict in institutions_data:
            existing = (
                db.query(InstitutionModel)
                .filter(
                    (InstitutionModel.id == inst_dict["id"])
                    | (InstitutionModel.code == inst_dict["code"])
                )
                .first()
            )
            if not existing:
                inst = InstitutionModel(**inst_dict)
                db.add(inst)
                db.commit()
                db.refresh(inst)
                print(f"[+] Created institution: {inst.name} ({inst.code})")
                inst_map[inst.code] = inst.id
            else:
                inst_map[existing.code] = existing.id
                print(f"[*] Institution already exists: {existing.name} ({existing.code})")

        # 2. Seed Default Users
        users_data = [
            {
                "email": "admin@certverify.org",
                "full_name": "System Administrator",
                "password": "Admin@12345!",
                "role": UserRole.ADMIN.value,
                "institution_id": None,
            },
            {
                "email": "verifier@nit.edu",
                "full_name": "NIT University Registrar",
                "password": "Verifier@12345!",
                "role": UserRole.INSTITUTION_VERIFIER.value,
                "institution_id": inst_map.get("NIT01"),
            },
            {
                "email": "student@example.com",
                "full_name": "Alex Student",
                "password": "Student@12345!",
                "role": UserRole.PUBLIC_USER.value,
                "institution_id": None,
            },
        ]

        for u_data in users_data:
            existing_user = db.query(AppUserModel).filter_by(email=u_data["email"]).first()
            if not existing_user:
                new_user = AppUserModel(
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    password_hash=get_password_hash(u_data["password"]),
                    role=u_data["role"],
                    institution_id=u_data["institution_id"],
                    is_active=True,
                )
                db.add(new_user)
                db.commit()
                print(f"[+] Created user: {new_user.email} (Role: {new_user.role})")
            else:
                print(
                    f"[*] User already exists: {existing_user.email} (Role: {existing_user.role})"
                )

        print("[✓] Database seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
