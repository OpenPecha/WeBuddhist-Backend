"""add tradition_list and tradition_metadata tables

Revision ID: u5v6w7x8y9z0
Revises: t4u5v6w7x8y9
Create Date: 2026-06-22 13:00:00.000000

Stores the Buddhist tradition taxonomy used by onboarding. ``tradition_list``
holds the self-referential hierarchy (parent_id) plus regions; per-language
names live in ``tradition_metadata`` (one row per tradition per language), with
the FK on the metadata side so a tradition can have many language rows.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = 'u5v6w7x8y9z0'
down_revision: Union[str, None] = 't4u5v6w7x8y9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# The languagecode enum already exists (created by earlier migrations and
# extended with HI/NE/MN), so reference it without re-creating the type.
language_column = postgresql.ENUM(
    "EN", "BO", "ZH", "HI", "NE", "MN",
    name="languagecode",
    create_type=False,
)


def upgrade() -> None:
    if not table_exists("tradition_list"):
        op.create_table(
            "tradition_list",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("parent_id", sa.UUID(), nullable=True),
            sa.Column("regions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["parent_id"], ["tradition_list.id"],
                name="fk_tradition_list_parent_id",
                ondelete="SET NULL",
            ),
        )

    if not table_exists("tradition_metadata"):
        op.create_table(
            "tradition_metadata",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("tradition_id", sa.UUID(), nullable=False),
            sa.Column("language", language_column, nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("other_names", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["tradition_id"], ["tradition_list.id"],
                name="fk_tradition_metadata_tradition_id",
                ondelete="CASCADE",
            ),
        )

    if not index_exists("tradition_list", "idx_tradition_list_parent_id"):
        op.create_index("idx_tradition_list_parent_id", "tradition_list", ["parent_id"], unique=False)
    if not index_exists("tradition_metadata", "idx_tradition_metadata_tradition_id"):
        op.create_index("idx_tradition_metadata_tradition_id", "tradition_metadata", ["tradition_id"], unique=False)
    if not index_exists("tradition_metadata", "idx_tradition_metadata_language"):
        op.create_index("idx_tradition_metadata_language", "tradition_metadata", ["language"], unique=False)


def downgrade() -> None:
    if index_exists("tradition_metadata", "idx_tradition_metadata_language"):
        op.drop_index("idx_tradition_metadata_language", table_name="tradition_metadata")
    if index_exists("tradition_metadata", "idx_tradition_metadata_tradition_id"):
        op.drop_index("idx_tradition_metadata_tradition_id", table_name="tradition_metadata")
    if index_exists("tradition_list", "idx_tradition_list_parent_id"):
        op.drop_index("idx_tradition_list_parent_id", table_name="tradition_list")

    if table_exists("tradition_metadata"):
        op.drop_table("tradition_metadata")
    if table_exists("tradition_list"):
        op.drop_table("tradition_list")
