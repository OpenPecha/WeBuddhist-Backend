"""widen text_id-holding columns from uuid to varchar(255)

Revision ID: 11527cc6c6c4
Revises: a1d0553772e4
Create Date: 2026-08-27 00:00:00.000000

Mirrors a1d0553772e4 (sub_tasks.segment_ids) for every column that stores a
text_id: they need to hold external (pecha-style) text ids as well as
internal Text UUIDs. Data-preserving casts (uuid -> text is a direct cast),
each guarded so it only runs if the column is still uuid.

Columns widened:
- accumulators.text_id
- sub_tasks.source_text_id
- user_recitations.text_id
- recitation_collection_items.text_id
- group_recitation_collection_items.text_id
- routine_sessions.source_id (polymorphic: also holds Plan/Series/Accumulator/
  collection ids for other session types, which remain real UUIDs stored as
  their string form; only RECITATION sessions may hold a non-UUID value)
"""
from typing import Sequence, Union

from alembic import op

revision: str = '11527cc6c6c4'
down_revision: Union[str, None] = 'a1d0553772e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLUMNS = [
    ("accumulators", "text_id"),
    ("sub_tasks", "source_text_id"),
    ("user_recitations", "text_id"),
    ("recitation_collection_items", "text_id"),
    ("group_recitation_collection_items", "text_id"),
    ("routine_sessions", "source_id"),
]


def upgrade() -> None:
    for table, column in _COLUMNS:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}'
                    AND column_name = '{column}'
                    AND udt_name = 'uuid'
                ) THEN
                    ALTER TABLE {table}
                    ALTER COLUMN {column} TYPE VARCHAR(255)
                    USING {column}::text;
                END IF;
            END $$;
        """)


def downgrade() -> None:
    for table, column in reversed(_COLUMNS):
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN {column} TYPE UUID
            USING {column}::uuid
        """)
