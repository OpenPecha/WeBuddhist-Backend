"""add push_device_tokens table

Revision ID: v6w7x8y9z0a1
Revises: u5v6w7x8y9z0
Create Date: 2026-06-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import enum_exists, index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = "v6w7x8y9z0a1"
down_revision: Union[str, None] = "u5v6w7x8y9z0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PUSH_PLATFORM_ENUM = postgresql.ENUM("ANDROID", "IOS", name="push_platform", create_type=False)


def upgrade() -> None:
    if not enum_exists("push_platform"):
        op.execute("CREATE TYPE push_platform AS ENUM ('ANDROID', 'IOS')")

    if not table_exists("push_device_tokens"):
        op.create_table(
            "push_device_tokens",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("token", sa.String(length=512), nullable=False),
            sa.Column("platform", PUSH_PLATFORM_ENUM, nullable=False),
            sa.Column("device_id", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )

    if not index_exists("push_device_tokens", "idx_push_device_tokens_user_id"):
        op.create_index(
            "idx_push_device_tokens_user_id",
            "push_device_tokens",
            ["user_id"],
            unique=False,
        )

    if not index_exists("push_device_tokens", "idx_push_device_tokens_user_active"):
        op.create_index(
            "idx_push_device_tokens_user_active",
            "push_device_tokens",
            ["user_id", "is_active"],
            unique=False,
        )

    if not index_exists("push_device_tokens", "uq_push_device_tokens_user_device_id"):
        op.create_index(
            "uq_push_device_tokens_user_device_id",
            "push_device_tokens",
            ["user_id", "device_id"],
            unique=True,
            postgresql_where=sa.text("device_id IS NOT NULL"),
        )


def downgrade() -> None:
    if index_exists("push_device_tokens", "uq_push_device_tokens_user_device_id"):
        op.drop_index("uq_push_device_tokens_user_device_id", table_name="push_device_tokens")

    if index_exists("push_device_tokens", "idx_push_device_tokens_user_active"):
        op.drop_index("idx_push_device_tokens_user_active", table_name="push_device_tokens")

    if index_exists("push_device_tokens", "idx_push_device_tokens_user_id"):
        op.drop_index("idx_push_device_tokens_user_id", table_name="push_device_tokens")

    if table_exists("push_device_tokens"):
        op.drop_table("push_device_tokens")

    if enum_exists("push_platform"):
        op.execute("DROP TYPE push_platform")
