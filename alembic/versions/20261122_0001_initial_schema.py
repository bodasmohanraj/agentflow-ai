"""Create missing application tables without replacing existing data.

Revision ID: 20261122_0001
Revises:
Create Date: 2026-11-22
"""
from alembic import op

from backend.app.db.session import Base
from backend.app.models import models  # noqa: F401 - registers model metadata

revision = "20261122_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # checkfirst keeps pre-existing tables and their data intact when adopting
    # an existing database into Alembic management.
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    # This baseline can adopt databases that predate Alembic, so dropping
    # tables here could destroy data that this revision did not create.
    pass
