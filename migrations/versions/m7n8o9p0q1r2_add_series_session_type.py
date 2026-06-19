"""add SERIES session type and migrate plan sessions in series

Revision ID: m7n8o9p0q1r2
Revises: l5m6n7o8p9q0
Create Date: 2026-06-18 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "m7n8o9p0q1r2"
down_revision: Union[str, None] = "l5m6n7o8p9q0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'SERIES'")

    op.execute(
        """
        UPDATE routine_sessions rs
        SET session_type = 'SERIES',
            source_id = p.series_id
        FROM plans p
        WHERE rs.session_type = 'PLAN'
          AND rs.source_id = p.id
          AND p.series_id IS NOT NULL
        """
    )

    op.execute(
        """
        DELETE FROM routine_sessions rs
        USING (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY time_block_id, source_id
                       ORDER BY display_order ASC, created_at ASC
                   ) AS rn
            FROM routine_sessions
            WHERE session_type = 'SERIES'
        ) ranked
        WHERE rs.id = ranked.id
          AND ranked.rn > 1
        """
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is not supported: SERIES sessions cannot be reliably "
        "restored to their original PLAN source_id values. Running downgrade "
        "would permanently delete routine session data."
    )
