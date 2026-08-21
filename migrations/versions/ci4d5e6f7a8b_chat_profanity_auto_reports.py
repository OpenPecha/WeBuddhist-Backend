"""chat profanity auto-moderation reports

Revision ID: ci4d5e6f7a8b
Revises: ch3c4d5e6f7a
Create Date: 2026-08-21 12:00:00.000000

Extends chat_message_reports so the system can auto-file reports for rejected
(profane) messages that were never stored: message_id/reporter_id become
nullable, and reported_user_id, room_id, source and message_text are added.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import column_exists, fk_exists, index_exists

# revision identifiers, used by Alembic.
revision: str = 'ci4d5e6f7a8b'
down_revision: Union[str, None] = 'ch3c4d5e6f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "chat_message_reports"
CHECK_CONSTRAINT = "ck_chat_message_reports_source_shape"


def upgrade() -> None:
    op.alter_column(TABLE, "message_id", nullable=True)
    op.alter_column(TABLE, "reporter_id", nullable=True)

    if not column_exists(TABLE, "reported_user_id"):
        op.add_column(
            TABLE,
            sa.Column("reported_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not fk_exists(TABLE, "fk_chat_message_reports_reported_user_id"):
        op.create_foreign_key(
            "fk_chat_message_reports_reported_user_id",
            TABLE,
            "users",
            ["reported_user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if not column_exists(TABLE, "room_id"):
        op.add_column(
            TABLE,
            sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not fk_exists(TABLE, "fk_chat_message_reports_room_id"):
        op.create_foreign_key(
            "fk_chat_message_reports_room_id",
            TABLE,
            "chat_rooms",
            ["room_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if not column_exists(TABLE, "source"):
        op.add_column(
            TABLE,
            sa.Column(
                "source",
                sa.String(length=16),
                nullable=False,
                server_default="MANUAL",
            ),
        )

    if not column_exists(TABLE, "message_text"):
        op.add_column(TABLE, sa.Column("message_text", sa.Text(), nullable=True))

    if not index_exists(TABLE, "idx_chat_message_reports_reported_user"):
        op.create_index(
            "idx_chat_message_reports_reported_user",
            TABLE,
            ["reported_user_id"],
            unique=False,
        )

    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = '{CHECK_CONSTRAINT}'
            ) THEN
                ALTER TABLE {TABLE} ADD CONSTRAINT {CHECK_CONSTRAINT} CHECK (
                    (source = 'MANUAL' AND message_id IS NOT NULL AND reporter_id IS NOT NULL)
                    OR (source = 'AUTOMATIC' AND reported_user_id IS NOT NULL)
                );
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS {CHECK_CONSTRAINT}")
    if index_exists(TABLE, "idx_chat_message_reports_reported_user"):
        op.drop_index("idx_chat_message_reports_reported_user", table_name=TABLE)
    # Automatic reports have no message/reporter and cannot survive the columns
    # reverting to NOT NULL.
    op.execute(f"DELETE FROM {TABLE} WHERE source = 'AUTOMATIC'")
    if column_exists(TABLE, "message_text"):
        op.drop_column(TABLE, "message_text")
    if column_exists(TABLE, "source"):
        op.drop_column(TABLE, "source")
    if fk_exists(TABLE, "fk_chat_message_reports_room_id"):
        op.drop_constraint("fk_chat_message_reports_room_id", TABLE, type_="foreignkey")
    if column_exists(TABLE, "room_id"):
        op.drop_column(TABLE, "room_id")
    if fk_exists(TABLE, "fk_chat_message_reports_reported_user_id"):
        op.drop_constraint(
            "fk_chat_message_reports_reported_user_id", TABLE, type_="foreignkey"
        )
    if column_exists(TABLE, "reported_user_id"):
        op.drop_column(TABLE, "reported_user_id")
    op.alter_column(TABLE, "reporter_id", nullable=False)
    op.alter_column(TABLE, "message_id", nullable=False)
