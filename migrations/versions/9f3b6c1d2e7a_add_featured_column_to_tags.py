"""add featured column to tags

Revision ID: 9f3b6c1d2e7a
Revises: ba8e2cb719be
Create Date: 2026-05-28 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9f3b6c1d2e7a"
down_revision: Union[str, None] = "ba8e2cb719be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tags",
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
    )
    op.create_index(
        "idx_tags_featured",
        "tags",
        ["featured"],
        unique=False,
        postgresql_where=sa.text("featured = TRUE AND deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_tags_featured", table_name="tags")
    op.drop_column("tags", "featured")
