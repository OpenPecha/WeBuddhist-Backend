"""add GROUP_RECITATION_COLLECTION to bookmark_type

Revision ID: bk1a2b3c4d5e
Revises: 11de7acad90f, fb9e0aa857d0
Create Date: 2026-08-19 12:00:00.000000

Allows users to bookmark group recitation (chant) collections, alongside the
existing TEXT/PLAN/SERIES/ACCUMULATOR/TIMER/VERSE bookmark types. Also merges
the event-recurrence and tradition-catalog heads.

"""
from typing import Sequence, Union

from alembic import op

from migrations.idempotency import enum_value_exists

# revision identifiers, used by Alembic.
revision: str = 'bk1a2b3c4d5e'
down_revision: Union[str, Sequence[str], None] = ('11de7acad90f', 'fb9e0aa857d0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if enum_value_exists("bookmark_type", "GROUP_RECITATION_COLLECTION"):
        return
    # ADD VALUE cannot run inside a transaction block
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE bookmark_type ADD VALUE IF NOT EXISTS 'GROUP_RECITATION_COLLECTION'"
        )


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly.
    # For safety, we leave the enum value in place during downgrade and keep
    # any GROUP_RECITATION_COLLECTION bookmarks users have created.
    pass
