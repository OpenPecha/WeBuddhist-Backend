"""add author groups domain

Revision ID: d1f3a9c2b7e4
Revises: ba8e2cb719be
Create Date: 2026-05-28 13:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d1f3a9c2b7e4"
down_revision: Union[str, None] = "ba8e2cb719be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


author_group_member_role_enum = postgresql.ENUM(
    "OWNER",
    "ADMIN",
    "EDITOR",
    "AUTHOR",
    "VIEWER",
    name="author_group_member_role",
    create_type=False,
)


def upgrade() -> None:
    author_group_member_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "author_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("avatar_key", sa.String(length=1000), nullable=True),
        sa.Column("banner_key", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_author_groups_slug",
        "author_groups",
        ["slug"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "author_group_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "language", name="uq_author_group_metadata_group_language"),
    )
    op.create_index(
        "idx_author_group_metadata_group_language",
        "author_group_metadata",
        ["group_id", "language"],
        unique=False,
    )

    op.create_table(
        "author_group_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", author_group_member_role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "author_id", name="uq_author_group_members_group_author"),
    )
    op.create_index(
        "idx_author_group_members_group_author",
        "author_group_members",
        ["group_id", "author_id"],
        unique=False,
    )

    op.create_table(
        "author_group_followers",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_author_group_followers_group_user"),
    )
    op.create_index(
        "idx_author_group_followers_group_user",
        "author_group_followers",
        ["group_id", "user_id"],
        unique=False,
    )

    op.create_table(
        "author_group_tags",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "tag_id"),
        sa.UniqueConstraint("group_id", "tag_id", name="uq_author_group_tags_group_tag"),
    )
    op.create_index("idx_author_group_tags_group_tag", "author_group_tags", ["group_id", "tag_id"], unique=False)

    op.create_table(
        "author_group_social_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "author_group_series",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "series_id"),
        sa.UniqueConstraint("group_id", "series_id", name="uq_author_group_series_group_series"),
    )
    op.create_index(
        "idx_author_group_series_group_series",
        "author_group_series",
        ["group_id", "series_id"],
        unique=False,
    )

    op.create_table(
        "author_group_plans",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "plan_id"),
        sa.UniqueConstraint("group_id", "plan_id", name="uq_author_group_plans_group_plan"),
    )
    op.create_index(
        "idx_author_group_plans_group_plan",
        "author_group_plans",
        ["group_id", "plan_id"],
        unique=False,
    )

    op.create_table(
        "author_group_invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_email", sa.String(length=255), nullable=False),
        sa.Column("role", author_group_member_role_enum, nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("uses_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("idx_author_group_invites_token_hash", "author_group_invites", ["token_hash"], unique=False)
    op.create_index("idx_author_group_invites_target_email", "author_group_invites", ["target_email"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_author_group_invites_target_email", table_name="author_group_invites")
    op.drop_index("idx_author_group_invites_token_hash", table_name="author_group_invites")
    op.drop_table("author_group_invites")

    op.drop_index("idx_author_group_plans_group_plan", table_name="author_group_plans")
    op.drop_table("author_group_plans")

    op.drop_index("idx_author_group_series_group_series", table_name="author_group_series")
    op.drop_table("author_group_series")

    op.drop_table("author_group_social_links")

    op.drop_index("idx_author_group_tags_group_tag", table_name="author_group_tags")
    op.drop_table("author_group_tags")

    op.drop_index("idx_author_group_followers_group_user", table_name="author_group_followers")
    op.drop_table("author_group_followers")

    op.drop_index("idx_author_group_members_group_author", table_name="author_group_members")
    op.drop_table("author_group_members")

    op.drop_index("idx_author_group_metadata_group_language", table_name="author_group_metadata")
    op.drop_table("author_group_metadata")

    op.drop_index("idx_author_groups_slug", table_name="author_groups")
    op.drop_table("author_groups")

    author_group_member_role_enum.drop(op.get_bind(), checkfirst=True)
