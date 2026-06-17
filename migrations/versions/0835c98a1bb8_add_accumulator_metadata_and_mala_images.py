"""add accumulator_metadata and mala_images

- mala_images: catalog of selectable mala images (url, name, default).
- accumulator_metadata: per-language name/description for an accumulator plus a
  chosen mala image (FK into mala_images). Mirrors the mantra_metadata pattern.
- Drops name/description off accumulators (now live per-language in metadata).

Revision ID: 0835c98a1bb8
Revises: 8515254497fe
Create Date: 2026-06-17 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0835c98a1bb8"
down_revision: Union[str, None] = "8515254497fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mala_images",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "accumulator_metadata",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("accumulator_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", postgresql.ENUM("EN", "BO", "ZH", name="languagecode", create_type=False), nullable=False),
        sa.Column("mala_image", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["accumulator_id"], ["accumulators.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mala_image"], ["mala_images.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_accumulator_metadata_accumulator_id",
        "accumulator_metadata",
        ["accumulator_id"],
    )

    op.drop_column("accumulators", "name")
    op.drop_column("accumulators", "description")


def downgrade() -> None:
    op.add_column(
        "accumulators",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "accumulators",
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
    )
    op.alter_column("accumulators", "name", server_default=None)

    op.drop_index("idx_accumulator_metadata_accumulator_id", table_name="accumulator_metadata")
    op.drop_table("accumulator_metadata")
    op.drop_table("mala_images")
