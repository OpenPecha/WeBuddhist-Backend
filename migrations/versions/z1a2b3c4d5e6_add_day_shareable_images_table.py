"""add day_shareable_images table

Revision ID: z1a2b3c4d5e6
Revises: y9z0a1b2c3d4
Create Date: 2026-06-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "z1a2b3c4d5e6"
down_revision: Union[str, None] = "y9z0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _day_shareable_images_exists() -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'day_shareable_images'"
            )
        ).fetchone()
    )


def upgrade() -> None:
    if _day_shareable_images_exists():
        return

    op.create_table(
        "day_shareable_images",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("plan_item_id", sa.UUID(), nullable=False),
        sa.Column("thumbnail_key", sa.String(length=1000), nullable=True),
        sa.Column("shareable_image_key", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["plan_item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_item_id"),
    )

    op.create_index(
        "idx_day_shareable_images_plan_item_id",
        "day_shareable_images",
        ["plan_item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_day_shareable_images_plan_item_id",
        table_name="day_shareable_images",
    )
    op.drop_table("day_shareable_images")
