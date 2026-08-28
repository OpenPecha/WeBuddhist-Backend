"""widen sub_tasks.segment_ids from uuid[] to varchar(255)[]

Revision ID: a1d0553772e4
Revises: pm2b3c4d5e6f
Create Date: 2026-08-27 00:00:00.000000

segment_ids needs to hold external (pecha-style) segment ids as well as
internal Segment UUIDs, so the column can no longer be UUID-only. This is a
data-preserving cast (uuid -> text is a direct cast), guarded so it only
runs if the column is still uuid[].
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1d0553772e4'
down_revision: Union[str, None] = 'pm2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sub_tasks'
                AND column_name = 'segment_ids'
                AND udt_name = '_uuid'
            ) THEN
                ALTER TABLE sub_tasks
                ALTER COLUMN segment_ids TYPE VARCHAR(255)[]
                USING segment_ids::text[];
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE sub_tasks
        ALTER COLUMN segment_ids TYPE UUID[]
        USING segment_ids::uuid[]
    """)
