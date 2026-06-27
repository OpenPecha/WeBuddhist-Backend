"""ensure ACCUMULATOR session type exists on sessiontype enum

Revision ID: z5a6b7c8d9e0
Revises: 64e5528d818f
Create Date: 2026-06-27 16:00:00.000000

Repair migration for databases stamped past z0a1b2c3d4e5 without running it.
"""
from typing import Sequence, Union

from alembic import op

from migrations.idempotency import enum_value_exists

revision: str = "z5a6b7c8d9e0"
down_revision: Union[str, None] = "64e5528d818f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if enum_value_exists("sessiontype", "ACCUMULATOR"):
        return
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'ACCUMULATOR'")


def downgrade() -> None:
    op.execute("DELETE FROM routine_sessions WHERE session_type = 'ACCUMULATOR'")
