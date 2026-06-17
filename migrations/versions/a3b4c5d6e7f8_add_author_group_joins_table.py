"""add author group joins table

Revision ID: a3b4c5d6e7f8
Revises: 4721283b22a9
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "4721283b22a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "author_group_joins",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_author_group_joins_group_user"),
    )
    op.create_index(
        "idx_author_group_joins_group_user",
        "author_group_joins",
        ["group_id", "user_id"],
        unique=False,
    )
    op.create_index(
        "idx_author_group_joins_user",
        "author_group_joins",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_author_group_joins_user", table_name="author_group_joins")
    op.drop_index("idx_author_group_joins_group_user", table_name="author_group_joins")
    op.drop_table("author_group_joins")
