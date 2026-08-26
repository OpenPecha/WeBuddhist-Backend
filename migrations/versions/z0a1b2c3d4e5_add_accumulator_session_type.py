"""add ACCUMULATOR session type to routine sessions

Revision ID: z0a1b2c3d4e5
Revises: y9z0a1b2c3d4
Create Date: 2026-06-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

from migrations.idempotency import enum_value_exists

revision: str = "z0a1b2c3d4e5"
down_revision: Union[str, None] = "y9z0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if enum_value_exists("sessiontype", "ACCUMULATOR"):
        return
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'ACCUMULATOR'")


def downgrade() -> None:
    op.execute("DELETE FROM routine_sessions WHERE session_type = 'ACCUMULATOR'")
