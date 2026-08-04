"""add_group_post_likes_table

Revision ID: gp5e6f7g8h9i
Revises: b7c4e2a91d33
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "gp5e6f7g8h9i"
down_revision: Union[str, None] = "b7c4e2a91d33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_post_likes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["group_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_group_post_likes_post_user"),
    )
    op.create_index(
        "idx_group_post_likes_post_id",
        "group_post_likes",
        ["post_id"],
        unique=False,
    )
    op.create_index(
        "idx_group_post_likes_user_id",
        "group_post_likes",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_group_post_likes_user_id", table_name="group_post_likes")
    op.drop_index("idx_group_post_likes_post_id", table_name="group_post_likes")
    op.drop_table("group_post_likes")
