"""add_chat_message_notification_dispatch

Revision ID: ch2b3c4d5e6f
Revises: ch1a2b3c4d5e, d9bcc81e67c6
Create Date: 2026-07-28 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ch2b3c4d5e6f"
down_revision: Union[str, None] = ("ch1a2b3c4d5e", "d9bcc81e67c6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_messages",
        sa.Column("notification_sqs_message_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "chat_messages",
        sa.Column("notification_dispatched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_chat_messages_undispatched_notifications",
        "chat_messages",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text(
            "deleted_at IS NULL AND notification_sqs_message_id IS NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "idx_chat_messages_undispatched_notifications",
        table_name="chat_messages",
    )
    op.drop_column("chat_messages", "notification_dispatched_at")
    op.drop_column("chat_messages", "notification_sqs_message_id")
