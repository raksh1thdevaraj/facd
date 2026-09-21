"""initial 12-table schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-20 23:30:00.000000

"""

from typing import Sequence, Union

import app.models  # noqa: F401 - ensure all 12 models registered
from alembic import op
from app.database import Base

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all 12 database tables, foreign keys, and indexes."""
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Drop all tables."""
    Base.metadata.drop_all(bind=op.get_bind())
