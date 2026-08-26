"""add user_traditions table

Revision ID: w7x8y9z0a1b2
Revises: v6w7x8y9z0a1
Create Date: 2026-06-23 12:00:00.000000

Links users to the traditions they follow (many traditions per user).
``user_id`` references ``users.id`` and ``tradition_id`` references
``tradition_list.id``; both cascade on delete so the link is removed when
either side goes away. ``(user_id, tradition_id)`` is unique so a user cannot
follow the same tradition twice.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = 'w7x8y9z0a1b2'
down_revision: Union[str, None] = 'v6w7x8y9z0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists("user_traditions"):
        op.create_table(
            "user_traditions",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("tradition_id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"],
                name="fk_user_traditions_user_id",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["tradition_id"], ["tradition_list.id"],
                name="fk_user_traditions_tradition_id",
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "user_id", "tradition_id",
                name="uq_user_traditions_user_tradition",
            ),
        )

    if not index_exists("user_traditions", "idx_user_traditions_user_id"):
        op.create_index("idx_user_traditions_user_id", "user_traditions", ["user_id"], unique=False)


def downgrade() -> None:
    if index_exists("user_traditions", "idx_user_traditions_user_id"):
        op.drop_index("idx_user_traditions_user_id", table_name="user_traditions")
    if table_exists("user_traditions"):
        op.drop_table("user_traditions")
