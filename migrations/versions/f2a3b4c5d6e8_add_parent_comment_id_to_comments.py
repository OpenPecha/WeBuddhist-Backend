"""add parent comment id to group post comments

Revision ID: f2a3b4c5d6e8
Revises: e1f2a3b4c5d6
Create Date: 2026-07-30 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a3b4c5d6e8"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "group_post_comments",
        sa.Column("parent_comment_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "group_post_comments_parent_comment_id_fkey",
        "group_post_comments",
        "group_post_comments",
        ["parent_comment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "idx_group_post_comments_parent_comment_id",
        "group_post_comments",
        ["parent_comment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_group_post_comments_parent_comment_id",
        table_name="group_post_comments",
    )
    op.drop_constraint(
        "group_post_comments_parent_comment_id_fkey",
        "group_post_comments",
        type_="foreignkey",
    )
    op.drop_column("group_post_comments", "parent_comment_id")
