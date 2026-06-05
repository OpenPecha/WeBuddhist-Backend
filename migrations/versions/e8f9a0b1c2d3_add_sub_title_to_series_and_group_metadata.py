"""add sub_title to series and group metadata

Revision ID: e8f9a0b1c2d3
Revises: 020fc79d15bf
Create Date: 2026-06-05 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "020fc79d15bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "series_metadata",
        sa.Column("sub_title", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "author_group_metadata",
        sa.Column("sub_title", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("author_group_metadata", "sub_title")
    op.drop_column("series_metadata", "sub_title")
