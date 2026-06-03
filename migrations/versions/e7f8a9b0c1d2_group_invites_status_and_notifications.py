"""group invites status and notifications table

Revision ID: e7f8a9b0c1d2
Revises: c2653fe6f9de
Create Date: 2026-05-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, None] = "c2653fe6f9de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

invite_status_enum = postgresql.ENUM(
    "PENDING",
    "ACCEPTED",
    "REJECTED",
    "REVOKED",
    "EXPIRED",
    name="author_group_invite_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    invite_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "author_group_invites",
        sa.Column(
            "status",
            invite_status_enum,
            nullable=True,
        ),
    )
    op.add_column(
        "author_group_invites",
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "author_group_invites",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        """
        UPDATE author_group_invites
        SET status = CASE
            WHEN revoked_at IS NOT NULL THEN 'REVOKED'
            WHEN expires_at < NOW() THEN 'EXPIRED'
            WHEN uses_count >= max_uses THEN 'ACCEPTED'
            ELSE 'PENDING'
        END::author_group_invite_status
        """
    )

    op.alter_column("author_group_invites", "status", nullable=False)

    op.drop_index("idx_author_group_invites_token_hash", table_name="author_group_invites")
    op.drop_constraint("author_group_invites_token_hash_key", "author_group_invites", type_="unique")
    op.drop_column("author_group_invites", "token_hash")
    op.drop_column("author_group_invites", "max_uses")
    op.drop_column("author_group_invites", "uses_count")

    op.create_index(
        "idx_author_group_invites_group_status",
        "author_group_invites",
        ["group_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_author_group_invites_target_email_status",
        "author_group_invites",
        ["target_email", "status"],
        unique=False,
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("reference_type", sa.String(length=100), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("action_1_label", sa.String(length=100), nullable=True),
        sa.Column("action_1_method", sa.String(length=10), nullable=True),
        sa.Column("action_1_path", sa.String(length=500), nullable=True),
        sa.Column("action_2_label", sa.String(length=100), nullable=True),
        sa.Column("action_2_method", sa.String(length=10), nullable=True),
        sa.Column("action_2_path", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["recipient_author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_notifications_recipient_read",
        "notifications",
        ["recipient_author_id", "is_read"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_reference",
        "notifications",
        ["reference_type", "reference_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_notifications_reference", table_name="notifications")
    op.drop_index("idx_notifications_recipient_read", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("idx_author_group_invites_target_email_status", table_name="author_group_invites")
    op.drop_index("idx_author_group_invites_group_status", table_name="author_group_invites")

    op.add_column(
        "author_group_invites",
        sa.Column("token_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "author_group_invites",
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "author_group_invites",
        sa.Column("uses_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        """
        UPDATE author_group_invites
        SET token_hash = md5(id::text),
            uses_count = CASE WHEN status = 'ACCEPTED' THEN 1 ELSE 0 END
        """
    )
    op.alter_column("author_group_invites", "token_hash", nullable=False)
    op.create_unique_constraint("author_group_invites_token_hash_key", "author_group_invites", ["token_hash"])
    op.create_index(
        "idx_author_group_invites_token_hash",
        "author_group_invites",
        ["token_hash"],
        unique=False,
    )

    op.drop_column("author_group_invites", "rejected_at")
    op.drop_column("author_group_invites", "accepted_at")
    op.drop_column("author_group_invites", "status")

    invite_status_enum.drop(op.get_bind(), checkfirst=True)
