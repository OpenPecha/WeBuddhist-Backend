"""add author group type column

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-06-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

author_group_type_enum = sa.Enum("PAGE", "COMMUNITY", name="author_group_type")


def upgrade() -> None:
    author_group_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "author_groups",
        sa.Column(
            "group_type",
            author_group_type_enum,
            nullable=False,
            server_default="PAGE",
        ),
    )
    op.create_index(
        "idx_author_groups_type_public",
        "author_groups",
        ["group_type", "is_public"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_author_groups_type_public", table_name="author_groups")
    op.drop_column("author_groups", "group_type")
    author_group_type_enum.drop(op.get_bind(), checkfirst=True)
