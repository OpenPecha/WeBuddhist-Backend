"""add_group_post_notification_dispatch

Revision ID: gp9f8e7d6c5b
Revises: ci4d5e6f7a8b
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "gp9f8e7d6c5b"
down_revision: Union[str, None] = "ci4d5e6f7a8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "group_posts",
        sa.Column("notification_sqs_message_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "group_posts",
        sa.Column("notification_dispatched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_group_posts_undispatched_notifications",
        "group_posts",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text(
            "deleted_at IS NULL AND notification_sqs_message_id IS NULL AND status = 'PUBLISHED'"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "idx_group_posts_undispatched_notifications",
        table_name="group_posts",
    )
    op.drop_column("group_posts", "notification_dispatched_at")
    op.drop_column("group_posts", "notification_sqs_message_id")
