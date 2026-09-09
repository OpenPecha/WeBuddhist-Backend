"""add user_notification_preferences table

Revision ID: np1a2b3c4d5e
Revises: tb1c2d3e4f5a
Create Date: 2026-09-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import enum_exists, index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = "np1a2b3c4d5e"
down_revision: Union[str, None] = "tb1c2d3e4f5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOTIFICATION_TYPE_VALUES = (
    "CHAT_MESSAGE",
    "GROUP_POST",
    "EVENT",
    "EVENT_REMINDER",
    "ACCUMULATION",
    "SERIES",
    "GROUP_INVITE",
    "GROUP_JOIN_REQUEST",
    "VERSE_OF_DAY",
    "ROUTINE_REMINDER",
)
NOTIFICATION_CHANNEL_VALUES = ("PUSH", "IN_APP", "EMAIL")
NOTIFICATION_SCOPE_VALUES = ("GLOBAL", "GROUP")

NOTIFICATION_TYPE_ENUM = postgresql.ENUM(
    *NOTIFICATION_TYPE_VALUES, name="notification_type", create_type=False
)
NOTIFICATION_CHANNEL_ENUM = postgresql.ENUM(
    *NOTIFICATION_CHANNEL_VALUES, name="notification_channel", create_type=False
)
NOTIFICATION_SCOPE_ENUM = postgresql.ENUM(
    *NOTIFICATION_SCOPE_VALUES, name="notification_scope", create_type=False
)


def _create_enum(name: str, values: Sequence[str]) -> None:
    if not enum_exists(name):
        rendered = ", ".join(f"'{value}'" for value in values)
        op.execute(f"CREATE TYPE {name} AS ENUM ({rendered})")


def upgrade() -> None:
    _create_enum("notification_type", NOTIFICATION_TYPE_VALUES)
    _create_enum("notification_channel", NOTIFICATION_CHANNEL_VALUES)
    _create_enum("notification_scope", NOTIFICATION_SCOPE_VALUES)

    if not table_exists("user_notification_preferences"):
        op.create_table(
            "user_notification_preferences",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("notification_type", NOTIFICATION_TYPE_ENUM, nullable=False),
            sa.Column(
                "channel",
                NOTIFICATION_CHANNEL_ENUM,
                nullable=False,
                server_default="PUSH",
            ),
            sa.Column(
                "scope_type",
                NOTIFICATION_SCOPE_ENUM,
                nullable=False,
                server_default="GLOBAL",
            ),
            sa.Column("scope_id", sa.UUID(), nullable=True),
            sa.Column(
                "enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column("muted_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            # Written as an equivalence so new scope values need no constraint change
            sa.CheckConstraint(
                "(scope_type = 'GLOBAL') = (scope_id IS NULL)",
                name="ck_user_notif_pref_scope",
            ),
        )

    # Postgres does not dedupe NULLs, so global and scoped rows need separate
    # partial unique indexes.
    if not index_exists("user_notification_preferences", "uq_user_notif_pref_global"):
        op.create_index(
            "uq_user_notif_pref_global",
            "user_notification_preferences",
            ["user_id", "notification_type", "channel"],
            unique=True,
            postgresql_where=sa.text("scope_id IS NULL"),
        )

    if not index_exists("user_notification_preferences", "uq_user_notif_pref_scoped"):
        op.create_index(
            "uq_user_notif_pref_scoped",
            "user_notification_preferences",
            ["user_id", "notification_type", "channel", "scope_type", "scope_id"],
            unique=True,
            postgresql_where=sa.text("scope_id IS NOT NULL"),
        )

    if not index_exists("user_notification_preferences", "idx_user_notif_pref_lookup"):
        op.create_index(
            "idx_user_notif_pref_lookup",
            "user_notification_preferences",
            ["notification_type", "channel", "user_id"],
            unique=False,
        )


def downgrade() -> None:
    for index_name in (
        "idx_user_notif_pref_lookup",
        "uq_user_notif_pref_scoped",
        "uq_user_notif_pref_global",
    ):
        if index_exists("user_notification_preferences", index_name):
            op.drop_index(index_name, table_name="user_notification_preferences")

    if table_exists("user_notification_preferences"):
        op.drop_table("user_notification_preferences")

    for enum_name in ("notification_scope", "notification_channel", "notification_type"):
        if enum_exists(enum_name):
            op.execute(f"DROP TYPE {enum_name}")
