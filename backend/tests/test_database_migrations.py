"""Integration test for Alembic migrations and 12-table schema creation (TC-API-01)."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

import app.models  # noqa: F401
from alembic import command


def test_alembic_migrations_apply_cleanly(tmp_path: Path):
    """Verify Alembic applies all migrations and creates all 12 tables (TC-API-01)."""
    db_path = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_path}"

    alembic_ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    # 1. Run Upgrade Head
    command.upgrade(alembic_cfg, "head")

    # 2. Inspect created tables
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected_tables = {
        "institutions",
        "app_users",
        "certificates",
        "ocr_fields",
        "forensic_findings",
        "text_consistency_results",
        "institution_templates",
        "institution_records",
        "template_match_results",
        "ml_predictions",
        "verification_reports",
        "audit_logs",
    }

    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    # 3. Test Downgrade and Re-upgrade
    command.downgrade(alembic_cfg, "base")
    inspector_post_down = inspect(engine)
    tables_post_down = set(inspector_post_down.get_table_names())
    assert len(expected_tables.intersection(tables_post_down)) == 0

    command.upgrade(alembic_cfg, "head")
    inspector_post_reup = inspect(engine)
    tables_post_reup = set(inspector_post_reup.get_table_names())
    assert expected_tables.issubset(tables_post_reup)
