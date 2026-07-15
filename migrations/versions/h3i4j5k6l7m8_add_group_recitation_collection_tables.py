"""add group_recitation_collection tables

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2026-07-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import index_exists, table_exists

revision: str = "h3i4j5k6l7m8"
down_revision: Union[str, None] = "g2h3i4j5k6l7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists("group_recitation_collections"):
        op.create_table(
            "group_recitation_collections",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("img_url", sa.String(length=1000), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["group_id"],
                ["author_groups.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not index_exists("group_recitation_collections", "idx_group_recitation_collections_group_id"):
        op.create_index(
            "idx_group_recitation_collections_group_id",
            "group_recitation_collections",
            ["group_id"],
            unique=False,
        )

    if not table_exists("group_recitation_collection_items"):
        op.create_table(
            "group_recitation_collection_items",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("group_recitation_collection_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("text_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["group_recitation_collection_id"],
                ["group_recitation_collections.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "group_recitation_collection_id",
                "text_id",
                name="uq_group_recitation_collection_items_collection_text",
                postgresql_where=sa.text("deleted_at IS NULL"),
            ),
        )

    if not index_exists("group_recitation_collection_items", "idx_group_recitation_collection_items_collection_id"):
        op.create_index(
            "idx_group_recitation_collection_items_collection_id",
            "group_recitation_collection_items",
            ["group_recitation_collection_id"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        "idx_group_recitation_collection_items_collection_id",
        table_name="group_recitation_collection_items",
    )
    op.drop_table("group_recitation_collection_items")

    op.drop_index(
        "idx_group_recitation_collections_group_id",
        table_name="group_recitation_collections",
    )
    op.drop_table("group_recitation_collections")
