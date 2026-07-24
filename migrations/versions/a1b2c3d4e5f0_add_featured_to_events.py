"""add_featured_to_events

Revision ID: a1b2c3d4e5f0
Revises: f8a9b0c1d2e3
Create Date: 2026-07-24 17:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f0"
down_revision: Union[str, None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("idx_events_featured", "events", ["featured"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_events_featured", table_name="events")
    op.drop_column("events", "featured")
