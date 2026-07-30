"""add_user_chant_completion_table

Revision ID: d537d7dae9ad
Revises: a1b2c3d4e5f0
Create Date: 2026-07-29 15:34:36.381772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import index_exists, table_exists


# revision identifiers, used by Alembic.
revision: str = 'd537d7dae9ad'
down_revision: Union[str, None] = 'a1b2c3d4e5f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists("user_chant_completion"):
        op.create_table(
            "user_chant_completion",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("chant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("chant_collection_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("completion_date", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["chant_id"],
                ["group_recitation_collection_items.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["chant_collection_id"],
                ["group_recitation_collections.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "chant_id",
                "completion_date",
                name="uq_user_chant_completion_user_chant_date",
            ),
        )

    if not index_exists("user_chant_completion", "idx_user_chant_completion_user_date"):
        op.create_index(
            "idx_user_chant_completion_user_date",
            "user_chant_completion",
            ["user_id", "completion_date"],
            unique=False,
        )

    if not index_exists("user_chant_completion", "idx_user_chant_completion_collection"):
        op.create_index(
            "idx_user_chant_completion_collection",
            "user_chant_completion",
            ["chant_collection_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        "idx_user_chant_completion_collection",
        table_name="user_chant_completion",
    )
    op.drop_index(
        "idx_user_chant_completion_user_date",
        table_name="user_chant_completion",
    )
    op.drop_table("user_chant_completion")
