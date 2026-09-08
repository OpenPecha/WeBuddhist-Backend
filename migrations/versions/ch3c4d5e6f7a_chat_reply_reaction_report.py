"""chat message replies, reactions, and reports

Revision ID: ch3c4d5e6f7a
Revises: bk2b3c4d5e6f
Create Date: 2026-08-20 12:00:00.000000

Adds parent_message_id to chat_messages (replies), plus the
chat_message_reactions and chat_message_reports tables.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import column_exists, index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = 'ch3c4d5e6f7a'
down_revision: Union[str, None] = 'bk2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists("chat_messages", "parent_message_id"):
        op.add_column(
            "chat_messages",
            sa.Column("parent_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_chat_messages_parent_message_id",
            "chat_messages",
            "chat_messages",
            ["parent_message_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not table_exists("chat_message_reactions"):
        op.create_table(
            "chat_message_reactions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("emoji", sa.String(length=16), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint(
                "message_id",
                "user_id",
                "emoji",
                name="uq_chat_message_reactions_message_user_emoji",
            ),
        )
    if not index_exists("chat_message_reactions", "idx_chat_message_reactions_message_id"):
        op.create_index(
            "idx_chat_message_reactions_message_id",
            "chat_message_reactions",
            ["message_id"],
            unique=False,
        )

    if not table_exists("chat_message_reports"):
        op.create_table(
            "chat_message_reports",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reporter_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("reason", sa.String(length=32), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint(
                "message_id",
                "reporter_id",
                name="uq_chat_message_reports_message_reporter",
            ),
        )
    if not index_exists("chat_message_reports", "idx_chat_message_reports_message_id"):
        op.create_index(
            "idx_chat_message_reports_message_id",
            "chat_message_reports",
            ["message_id"],
            unique=False,
        )
    if not index_exists("chat_message_reports", "idx_chat_message_reports_unresolved"):
        op.create_index(
            "idx_chat_message_reports_unresolved",
            "chat_message_reports",
            ["created_at"],
            unique=False,
            postgresql_where=sa.text("resolved_at IS NULL"),
        )


def downgrade() -> None:
    if table_exists("chat_message_reports"):
        op.drop_table("chat_message_reports")
    if table_exists("chat_message_reactions"):
        op.drop_table("chat_message_reactions")
    if column_exists("chat_messages", "parent_message_id"):
        op.drop_constraint(
            "fk_chat_messages_parent_message_id", "chat_messages", type_="foreignkey"
        )
        op.drop_column("chat_messages", "parent_message_id")
