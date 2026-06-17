"""move mala_image from accumulator_metadata to accumulators

The mala image is one picture per accumulator (not per language), so it moves
off the per-language accumulator_metadata rows onto the accumulators table.
Existing values are carried over (one metadata row's image per accumulator).

Revision ID: 2d3e4f5a6b7c
Revises: 1c2d3e4f5a6b
Create Date: 2026-06-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2d3e4f5a6b7c"
down_revision: Union[str, None] = "1c2d3e4f5a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "accumulators",
        sa.Column("mala_image", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_accumulators_mala_image",
        "accumulators",
        "mala_images",
        ["mala_image"],
        ["id"],
        ondelete="SET NULL",
    )

    # Carry over any existing image: pick one metadata row's mala_image per
    # accumulator (they were typically the same across languages anyway).
    op.execute(
        """
        UPDATE accumulators a
        SET mala_image = sub.mala_image
        FROM (
            SELECT DISTINCT ON (accumulator_id) accumulator_id, mala_image
            FROM accumulator_metadata
            WHERE mala_image IS NOT NULL
            ORDER BY accumulator_id, id
        ) AS sub
        WHERE a.id = sub.accumulator_id
        """
    )

    op.drop_constraint(
        "accumulator_metadata_mala_image_fkey",
        "accumulator_metadata",
        type_="foreignkey",
    )
    op.drop_column("accumulator_metadata", "mala_image")


def downgrade() -> None:
    op.add_column(
        "accumulator_metadata",
        sa.Column("mala_image", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "accumulator_metadata_mala_image_fkey",
        "accumulator_metadata",
        "mala_images",
        ["mala_image"],
        ["id"],
        ondelete="SET NULL",
    )

    # Restore the image onto every metadata row of each accumulator.
    op.execute(
        """
        UPDATE accumulator_metadata m
        SET mala_image = a.mala_image
        FROM accumulators a
        WHERE m.accumulator_id = a.id
          AND a.mala_image IS NOT NULL
        """
    )

    op.drop_constraint(
        "fk_accumulators_mala_image",
        "accumulators",
        type_="foreignkey",
    )
    op.drop_column("accumulators", "mala_image")
