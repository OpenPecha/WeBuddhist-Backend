"""add_event_notification_dispatch

Revision ID: ev1a2b3c4d5e
Revises: gp9f8e7d6c5b
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ev1a2b3c4d5e"
down_revision: Union[str, None] = "gp9f8e7d6c5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("notification_sqs_message_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "events",
        sa.Column("notification_dispatched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_events_undispatched_notifications",
        "events",
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("notification_sqs_message_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "idx_events_undispatched_notifications",
        table_name="events",
    )
    op.drop_column("events", "notification_dispatched_at")
    op.drop_column("events", "notification_sqs_message_id")
