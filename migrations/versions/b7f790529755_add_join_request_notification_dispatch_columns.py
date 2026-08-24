"""add notification dispatch columns to author_group_join_requests

Revision ID: b7f790529755
Revises: 2b56ce482116
Create Date: 2026-08-21 10:00:00.000000

Mirrors the chat_messages dispatch-tracking columns so undispatched join
request notifications can be reconciled after a crash between commit and
enqueue.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7f790529755"
down_revision: Union[str, None] = "2b56ce482116"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "author_group_join_requests"


def upgrade() -> None:
    op.add_column(
        _TABLE,
        sa.Column("notification_sqs_message_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("notification_dispatched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("decision_sqs_message_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        _TABLE,
        sa.Column("decision_dispatched_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Partial index for the reconcile sweep: only rows still awaiting dispatch.
    op.create_index(
        "idx_author_group_join_requests_undispatched",
        _TABLE,
        ["created_at"],
        unique=False,
        postgresql_where=sa.text("notification_sqs_message_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_author_group_join_requests_undispatched", table_name=_TABLE)
    op.drop_column(_TABLE, "decision_dispatched_at")
    op.drop_column(_TABLE, "decision_sqs_message_id")
    op.drop_column(_TABLE, "notification_dispatched_at")
    op.drop_column(_TABLE, "notification_sqs_message_id")
