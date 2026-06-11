"""platform roles, group_id on plans/series, content transfer requests

Revision ID: 440953ec8a21
Revises: f6a7b8c9d0e1
Create Date: 2026-06-02 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "440953ec8a21"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

platform_role_enum = postgresql.ENUM(
    "SUPER_ADMIN", "REVIEWER", "CREATOR", name="platform_role", create_type=False
)
transfer_entity_type_enum = postgresql.ENUM(
    "plan", "series", name="transfer_entity_type", create_type=False
)
content_transfer_status_enum = postgresql.ENUM(
    "PENDING",
    "ACCEPTED",
    "REJECTED",
    "REVOKED",
    "EXPIRED",
    name="content_transfer_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE TYPE platform_role AS ENUM ('SUPER_ADMIN', 'REVIEWER', 'CREATOR')")
    op.execute("CREATE TYPE transfer_entity_type AS ENUM ('plan', 'series')")
    op.execute(
        "CREATE TYPE content_transfer_status AS ENUM "
        "('PENDING', 'ACCEPTED', 'REJECTED', 'REVOKED', 'EXPIRED')"
    )

    op.add_column(
        "authors",
        sa.Column("platform_role", platform_role_enum, nullable=True),
    )
    op.execute(
        """
        UPDATE authors
        SET platform_role = CASE
            WHEN is_admin = TRUE THEN 'SUPER_ADMIN'::platform_role
            ELSE 'CREATOR'::platform_role
        END
        """
    )
    op.alter_column("authors", "platform_role", nullable=False, server_default="CREATOR")
    op.drop_column("authors", "is_admin")

    op.add_column(
        "plans",
        sa.Column("group_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "series",
        sa.Column("group_id", sa.UUID(), nullable=True),
    )

    op.execute(
        """
        UPDATE plans p
        SET group_id = agp.group_id
        FROM (
            SELECT DISTINCT ON (plan_id) plan_id, group_id
            FROM author_group_plans
            ORDER BY plan_id, group_id
        ) agp
        WHERE p.id = agp.plan_id
        """
    )
    op.execute(
        """
        UPDATE series s
        SET group_id = ags.group_id
        FROM (
            SELECT DISTINCT ON (series_id) series_id, group_id
            FROM author_group_series
            ORDER BY series_id, group_id
        ) ags
        WHERE s.id = ags.series_id
        """
    )

    op.execute(
        """
        INSERT INTO author_groups (id, slug, is_public, created_at, created_by)
        SELECT gen_random_uuid(), 'workspace-' || a.id::text, FALSE, NOW(), COALESCE(a.email, 'migration@local')
        FROM authors a
        WHERE (
            EXISTS (
                SELECT 1 FROM plans p
                WHERE p.author_id = a.id AND p.group_id IS NULL
            )
            OR EXISTS (
                SELECT 1 FROM series s
                WHERE s.author_id = a.id AND s.group_id IS NULL
            )
        )
        AND NOT EXISTS (
            SELECT 1 FROM author_groups g
            WHERE g.slug = 'workspace-' || a.id::text AND g.deleted_at IS NULL
        )
        """
    )
    op.execute(
        """
        INSERT INTO author_group_metadata (id, group_id, language, title, description)
        SELECT gen_random_uuid(), g.id, 'EN', 'Default Workspace', 'Auto-created during migration'
        FROM author_groups g
        WHERE g.slug LIKE 'workspace-%'
          AND NOT EXISTS (
              SELECT 1 FROM author_group_metadata m WHERE m.group_id = g.id
          )
        """
    )
    op.execute(
        """
        INSERT INTO author_group_members (id, group_id, author_id, role, created_at, created_by)
        SELECT gen_random_uuid(), g.id, a.id, 'OWNER', NOW(), COALESCE(a.email, 'migration@local')
        FROM author_groups g
        JOIN authors a ON g.slug = 'workspace-' || a.id::text
        WHERE NOT EXISTS (
            SELECT 1 FROM author_group_members m
            WHERE m.group_id = g.id AND m.author_id = a.id
        )
        """
    )
    op.execute(
        """
        UPDATE plans p
        SET group_id = g.id
        FROM author_groups g
        JOIN authors a ON g.slug = 'workspace-' || a.id::text
        WHERE p.author_id = a.id AND p.group_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE series s
        SET group_id = g.id
        FROM author_groups g
        JOIN authors a ON g.slug = 'workspace-' || a.id::text
        WHERE s.author_id = a.id AND s.group_id IS NULL
        """
    )
    op.execute(
        """
        INSERT INTO author_groups (id, slug, is_public, created_at, created_by)
        SELECT gen_random_uuid(), 'migration-orphans', FALSE, NOW(), 'migration@local'
        WHERE (
            EXISTS (SELECT 1 FROM plans WHERE group_id IS NULL)
            OR EXISTS (SELECT 1 FROM series WHERE group_id IS NULL)
        )
        AND NOT EXISTS (
            SELECT 1 FROM author_groups g
            WHERE g.slug = 'migration-orphans' AND g.deleted_at IS NULL
        )
        """
    )
    op.execute(
        """
        INSERT INTO author_group_metadata (id, group_id, language, title, description)
        SELECT gen_random_uuid(), g.id, 'EN', 'Migration Orphans', 'Auto-created for legacy rows without a group'
        FROM author_groups g
        WHERE g.slug = 'migration-orphans'
          AND NOT EXISTS (
              SELECT 1 FROM author_group_metadata m WHERE m.group_id = g.id
          )
        """
    )
    op.execute(
        """
        UPDATE plans
        SET group_id = (
            SELECT g.id FROM author_groups g
            WHERE g.slug = 'migration-orphans' AND g.deleted_at IS NULL
            LIMIT 1
        )
        WHERE group_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE series
        SET group_id = (
            SELECT g.id FROM author_groups g
            WHERE g.slug = 'migration-orphans' AND g.deleted_at IS NULL
            LIMIT 1
        )
        WHERE group_id IS NULL
        """
    )

    op.create_foreign_key(
        "fk_plans_group_id",
        "plans",
        "author_groups",
        ["group_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_series_group_id",
        "series",
        "author_groups",
        ["group_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.alter_column("plans", "group_id", nullable=False)
    op.alter_column("series", "group_id", nullable=False)

    op.create_table(
        "content_transfer_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("entity_type", transfer_entity_type_enum, nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("from_group_id", sa.UUID(), nullable=False),
        sa.Column("to_group_id", sa.UUID(), nullable=False),
        sa.Column("status", content_transfer_status_enum, nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("responded_by", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["from_group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_content_transfer_to_group_status",
        "content_transfer_requests",
        ["to_group_id", "status"],
    )
    op.create_index(
        "idx_content_transfer_entity_status",
        "content_transfer_requests",
        ["entity_type", "entity_id", "status"],
    )

    op.drop_table("author_group_plans")
    op.drop_table("author_group_series")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION expire_pending_content_transfer_requests()
        RETURNS integer
        LANGUAGE plpgsql
        AS $$
        DECLARE
            updated_count integer;
        BEGIN
            UPDATE content_transfer_requests
            SET status = 'EXPIRED'
            WHERE status = 'PENDING'
              AND expires_at < NOW();
            GET DIAGNOSTICS updated_count = ROW_COUNT;
            RETURN updated_count;
        END;
        $$;
        """
    )
    op.execute("SELECT expire_pending_content_transfer_requests()")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS expire_pending_content_transfer_requests()")

    op.create_table(
        "author_group_series",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("series_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "series_id"),
        sa.UniqueConstraint("group_id", "series_id", name="uq_author_group_series_group_series"),
    )
    op.create_table(
        "author_group_plans",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "plan_id"),
        sa.UniqueConstraint("group_id", "plan_id", name="uq_author_group_plans_group_plan"),
    )
    op.execute(
        """
        INSERT INTO author_group_plans (group_id, plan_id)
        SELECT group_id, id FROM plans WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        INSERT INTO author_group_series (group_id, series_id)
        SELECT group_id, id FROM series WHERE deleted_at IS NULL
        """
    )

    op.drop_index("idx_content_transfer_entity_status", table_name="content_transfer_requests")
    op.drop_index("idx_content_transfer_to_group_status", table_name="content_transfer_requests")
    op.drop_table("content_transfer_requests")

    op.drop_constraint("fk_series_group_id", "series", type_="foreignkey")
    op.drop_constraint("fk_plans_group_id", "plans", type_="foreignkey")
    op.drop_column("series", "group_id")
    op.drop_column("plans", "group_id")

    op.add_column(
        "authors",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.execute(
        """
        UPDATE authors
        SET is_admin = TRUE
        WHERE platform_role = 'SUPER_ADMIN'
        """
    )
    op.drop_column("authors", "platform_role")

    op.execute("DROP TYPE IF EXISTS content_transfer_status")
    op.execute("DROP TYPE IF EXISTS transfer_entity_type")
    op.execute("DROP TYPE IF EXISTS platform_role")
