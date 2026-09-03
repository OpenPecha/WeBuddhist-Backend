"""widen china_restricted_items.item_id from uuid to varchar(255)

Revision ID: 4adfb8cfd7e5
Revises: 11527cc6c6c4
Create Date: 2026-08-28 00:00:00.000000

Mirrors 11527cc6c6c4 (text_id-holding columns): china_restricted_items.item_id
is checked against RestrictedItemType.RECITATION text_ids, which are now
external (pecha-style) strings as well as internal Text UUIDs. Widened the
same conditional, data-preserving way so existing UUID rows for other item
types (plans, series, accumulators, etc.) are unaffected.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '4adfb8cfd7e5'
down_revision: Union[str, None] = '11527cc6c6c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'china_restricted_items'
                AND column_name = 'item_id'
                AND udt_name = 'uuid'
            ) THEN
                ALTER TABLE china_restricted_items
                ALTER COLUMN item_id TYPE VARCHAR(255)
                USING item_id::text;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE china_restricted_items
        ALTER COLUMN item_id TYPE UUID
        USING item_id::uuid
    """)
