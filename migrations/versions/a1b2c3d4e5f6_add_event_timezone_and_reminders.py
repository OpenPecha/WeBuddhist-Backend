"""add timezone column to events and event_reminders table

Revision ID: a1b2c3d4e5f6
Revises: 813cecbdd710
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists, table_exists, index_exists

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "813cecbdd710"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists("events", "timezone"):
        op.add_column(
            "events",
            sa.Column("timezone", sa.String(length=64), nullable=True),
        )

    if not table_exists("event_reminders"):
        op.create_table(
            "event_reminders",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("event_id", sa.UUID(), nullable=False),
            sa.Column("reminder_type", sa.String(length=20), nullable=False),
            sa.Column("fire_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("sqs_message_id", sa.String(length=128), nullable=True),
            sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "event_id", "reminder_type", name="uq_event_reminders_event_type"
            ),
        )

    if not index_exists("event_reminders", "idx_event_reminders_event_id"):
        op.create_index(
            "idx_event_reminders_event_id",
            "event_reminders",
            ["event_id"],
            unique=False,
        )

    if not index_exists("event_reminders", "idx_event_reminders_due"):
        op.create_index(
            "idx_event_reminders_due",
            "event_reminders",
            ["fire_at"],
            unique=False,
            postgresql_where=sa.text("dispatched_at IS NULL AND canceled_at IS NULL"),
        )


def downgrade() -> None:
    if index_exists("event_reminders", "idx_event_reminders_due"):
        op.drop_index("idx_event_reminders_due", table_name="event_reminders")
    if index_exists("event_reminders", "idx_event_reminders_event_id"):
        op.drop_index("idx_event_reminders_event_id", table_name="event_reminders")
    if table_exists("event_reminders"):
        op.drop_table("event_reminders")
    if column_exists("events", "timezone"):
        op.drop_column("events", "timezone")
