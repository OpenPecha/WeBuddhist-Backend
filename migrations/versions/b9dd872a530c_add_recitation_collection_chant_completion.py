"""add_recitation_collection_chant_completion_table

Revision ID: b9dd872a530c
Revises: a8b9c0d1e2f3
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import index_exists, table_exists


# revision identifiers, used by Alembic.
revision: str = 'b9dd872a530c'
down_revision: Union[str, None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists("recitation_collection_chant_completions"):
        op.create_table(
            "recitation_collection_chant_completions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("chant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("completion_date", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["chant_id"],
                ["recitation_collection_items.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["collection_id"],
                ["recitation_collections.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "user_id",
                "chant_id",
                "completion_date",
                name="uq_recitation_collection_chant_completion_user_chant_date",
            ),
        )

    if not index_exists("recitation_collection_chant_completions", "idx_recitation_collection_chant_completion_user_date"):
        op.create_index(
            "idx_recitation_collection_chant_completion_user_date",
            "recitation_collection_chant_completions",
            ["user_id", "completion_date"],
            unique=False,
        )

    if not index_exists("recitation_collection_chant_completions", "idx_recitation_collection_chant_completion_collection"):
        op.create_index(
            "idx_recitation_collection_chant_completion_collection",
            "recitation_collection_chant_completions",
            ["collection_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        "idx_recitation_collection_chant_completion_collection",
        table_name="recitation_collection_chant_completions",
    )
    op.drop_index(
        "idx_recitation_collection_chant_completion_user_date",
        table_name="recitation_collection_chant_completions",
    )
    op.drop_table("recitation_collection_chant_completions")
