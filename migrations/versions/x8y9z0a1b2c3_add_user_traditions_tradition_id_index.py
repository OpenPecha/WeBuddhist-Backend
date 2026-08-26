"""add tradition_id index to user_traditions

Revision ID: x8y9z0a1b2c3
Revises: w7x8y9z0a1b2
Create Date: 2026-06-23 13:00:00.000000

Adds a standalone index on ``user_traditions.tradition_id``. Postgres does not
auto-create an index for a referencing FK column, so the existing composite
``(user_id, tradition_id)`` index cannot serve lookups keyed on ``tradition_id``
alone (wrong leading column). Without this, cascade deletes from
``tradition_list`` and any tradition-keyed query fall back to a sequential scan.

"""
from typing import Sequence, Union

from alembic import op

from migrations.idempotency import index_exists

# revision identifiers, used by Alembic.
revision: str = 'x8y9z0a1b2c3'
down_revision: Union[str, None] = 'w7x8y9z0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not index_exists("user_traditions", "idx_user_traditions_tradition_id"):
        op.create_index(
            "idx_user_traditions_tradition_id",
            "user_traditions",
            ["tradition_id"],
            unique=False,
        )


def downgrade() -> None:
    if index_exists("user_traditions", "idx_user_traditions_tradition_id"):
        op.drop_index("idx_user_traditions_tradition_id", table_name="user_traditions")
