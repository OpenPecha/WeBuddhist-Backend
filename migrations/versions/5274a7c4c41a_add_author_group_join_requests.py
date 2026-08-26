"""add author_group_join_requests table

Revision ID: 5274a7c4c41a
Revises: 11de7acad90f
Create Date: 2026-08-18 10:00:00.000000

Request-to-join flow for private (is_public = false) COMMUNITY groups: an app
user submits a request with an optional message, a Studio moderator approves or
rejects it. Approval calls upsert_group_join, matching a direct join.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5274a7c4c41a"
down_revision: Union[str, None] = "11de7acad90f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS_ENUM_NAME = "author_group_join_request_status"


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "PENDING",
        "APPROVED",
        "REJECTED",
        name=_STATUS_ENUM_NAME,
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "author_group_join_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="PENDING"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["authors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_author_group_join_requests_group_status",
        "author_group_join_requests",
        ["group_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_author_group_join_requests_user_status",
        "author_group_join_requests",
        ["user_id", "status"],
        unique=False,
    )
    # One open request per user per group; resolved rows never block resubmission.
    op.create_index(
        "uq_author_group_join_requests_pending_group_user",
        "author_group_join_requests",
        ["group_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDING'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_author_group_join_requests_pending_group_user",
        table_name="author_group_join_requests",
    )
    op.drop_index(
        "idx_author_group_join_requests_user_status",
        table_name="author_group_join_requests",
    )
    op.drop_index(
        "idx_author_group_join_requests_group_status",
        table_name="author_group_join_requests",
    )
    op.drop_table("author_group_join_requests")
    postgresql.ENUM(name=_STATUS_ENUM_NAME).drop(op.get_bind(), checkfirst=True)
