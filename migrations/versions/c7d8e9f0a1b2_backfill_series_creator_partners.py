"""backfill series creator group into series_partner

Revision ID: c7d8e9f0a1b2
Revises: a6b7c8d9e0f1
Create Date: 2026-06-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import table_exists

revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists("series_partner") or not table_exists("series"):
        return

    op.execute(
        sa.text(
            """
            INSERT INTO series_partner (id, series_id, group_id, created_at, updated_at)
            SELECT gen_random_uuid(), s.id, s.group_id, NOW(), NOW()
            FROM series s
            WHERE s.deleted_at IS NULL
              AND NOT EXISTS (
                SELECT 1
                FROM series_partner sp
                WHERE sp.series_id = s.id
                  AND sp.group_id = s.group_id
              )
            """
        )
    )


def downgrade() -> None:
    pass
