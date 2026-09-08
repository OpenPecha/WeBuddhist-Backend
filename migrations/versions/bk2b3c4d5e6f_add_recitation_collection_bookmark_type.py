"""add RECITATION_COLLECTION to bookmark_type

Revision ID: bk2b3c4d5e6f
Revises: bk1a2b3c4d5e
Create Date: 2026-08-19 13:00:00.000000

Allows users to bookmark their personal recitation collections, alongside the
GROUP_RECITATION_COLLECTION type added in bk1a2b3c4d5e.

"""
from typing import Sequence, Union

from alembic import op

from migrations.idempotency import enum_exists, enum_value_exists

# revision identifiers, used by Alembic.
revision: str = 'bk2b3c4d5e6f'
down_revision: Union[str, None] = 'bk1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not enum_exists("bookmark_type"):
        # Environments stamped past t4u5v6w7x8y9 without executing it never got
        # the type; create it here with the full value set instead of altering.
        op.execute(
            "CREATE TYPE bookmark_type AS ENUM "
            "('TEXT', 'PLAN', 'SERIES', 'ACCUMULATOR', 'TIMER', 'VERSE', "
            "'GROUP_RECITATION_COLLECTION', 'RECITATION_COLLECTION')"
        )
        return
    if enum_value_exists("bookmark_type", "RECITATION_COLLECTION"):
        return
    # ADD VALUE cannot run inside a transaction block
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE bookmark_type ADD VALUE IF NOT EXISTS 'RECITATION_COLLECTION'"
        )


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly.
    # For safety, we leave the enum value in place during downgrade and keep
    # any RECITATION_COLLECTION bookmarks users have created.
    pass
