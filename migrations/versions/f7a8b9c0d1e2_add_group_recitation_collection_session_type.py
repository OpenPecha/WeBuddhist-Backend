"""add GROUP_RECITATION_COLLECTION session type to routine sessions

Revision ID: f7a8b9c0d1e2
Revises: b0c1d2e3f4a5
Create Date: 2026-07-23 09:50:00.000000

"""
from typing import Sequence, Union

from alembic import op

from migrations.idempotency import enum_value_exists

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "b0c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if enum_value_exists("sessiontype", "GROUP_RECITATION_COLLECTION"):
        return
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'GROUP_RECITATION_COLLECTION'"
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM routine_sessions WHERE session_type = 'GROUP_RECITATION_COLLECTION'"
    )
