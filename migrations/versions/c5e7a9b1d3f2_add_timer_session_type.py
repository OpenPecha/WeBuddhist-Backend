"""add TIMER session type to routine sessions

Revision ID: c5e7a9b1d3f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-04 11:00:00.000000

Adds TIMER to the sessiontype enum and makes routine_sessions support timer
sessions: source_id becomes nullable (a timer references no plan/text) and a
new duration_ms column stores the timer length in milliseconds.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5e7a9b1d3f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ADD VALUE cannot run inside a transaction block
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'TIMER'")

    op.add_column(
        "routine_sessions",
        sa.Column("duration_ms", sa.Integer(), nullable=True),
    )
    op.alter_column(
        "routine_sessions",
        "source_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("DELETE FROM routine_sessions WHERE session_type = 'TIMER'")
    op.alter_column(
        "routine_sessions",
        "source_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_column("routine_sessions", "duration_ms")

    op.execute("ALTER TYPE sessiontype RENAME TO sessiontype_old")
    op.execute("CREATE TYPE sessiontype AS ENUM ('PLAN', 'RECITATION')")
    op.execute(
        "ALTER TABLE routine_sessions ALTER COLUMN session_type TYPE sessiontype "
        "USING session_type::text::sessiontype"
    )
    op.execute("DROP TYPE sessiontype_old")
