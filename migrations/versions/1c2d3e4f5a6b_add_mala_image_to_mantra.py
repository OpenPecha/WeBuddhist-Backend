"""add mala_image to mantra

Adds a default mala image (FK into mala_images) to the mantra table. When a
user creates an accumulator from a preset, the new accumulator's mala image
defaults to its mantra's mala_image (falling back to the preset metadata's
own mala image).

Revision ID: 1c2d3e4f5a6b
Revises: 0835c98a1bb8
Create Date: 2026-06-17 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1c2d3e4f5a6b"
down_revision: Union[str, None] = "0835c98a1bb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mantra",
        sa.Column("mala_image", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_mantra_mala_image",
        "mantra",
        "mala_images",
        ["mala_image"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_mantra_mala_image", "mantra", type_="foreignkey")
    op.drop_column("mantra", "mala_image")
