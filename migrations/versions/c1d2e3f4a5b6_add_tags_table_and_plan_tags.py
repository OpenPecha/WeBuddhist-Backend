"""add tags table and plan_tags association

Revision ID: c1d2e3f4a5b6
Revises: b8955f921c95
Create Date: 2026-05-21 10:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b8955f921c95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("image_key", sa.String(length=1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tags_name_unique",
        "tags",
        ["name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "plan_tags",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("tag_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_id", "tag_id"),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO tags (id, name, created_at)
            SELECT gen_random_uuid(), tag_name, NOW()
            FROM (
                SELECT MIN(trim(tag_name)) AS tag_name
                FROM plans,
                     LATERAL jsonb_array_elements_text(plans.tags) AS tag_name
                WHERE trim(tag_name) <> ''
                GROUP BY lower(trim(tag_name))
            ) AS unique_tag_names
            """
        )
    )
    connection.execute(
        sa.text(
            """
            INSERT INTO plan_tags (plan_id, tag_id)
            SELECT p.id, t.id
            FROM plans p
            CROSS JOIN LATERAL jsonb_array_elements_text(p.tags) AS tag_name
            JOIN tags t ON lower(t.name) = lower(trim(tag_name))
            WHERE t.deleted_at IS NULL
            ON CONFLICT DO NOTHING
            """
        )
    )

    op.drop_index("idx_plans_tags", table_name="plans", postgresql_using="gin")
    op.drop_index("idx_plans_discovery", table_name="plans")
    op.create_index("idx_plans_discovery", "plans", ["status"], unique=False)
    op.drop_column("plans", "tags")


def downgrade() -> None:
    op.add_column(
        "plans",
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE plans p
            SET tags = COALESCE(
                (
                    SELECT jsonb_agg(t.name ORDER BY t.name)
                    FROM plan_tags pt
                    JOIN tags t ON t.id = pt.tag_id
                    WHERE pt.plan_id = p.id AND t.deleted_at IS NULL
                ),
                '[]'::jsonb
            )
            """
        )
    )

    op.drop_index("idx_plans_discovery", table_name="plans")
    op.create_index("idx_plans_discovery", "plans", ["tags", "status"], unique=False)
    op.create_index(
        "idx_plans_tags",
        "plans",
        ["tags"],
        unique=False,
        postgresql_using="gin",
    )
    op.drop_table("plan_tags")
    op.drop_index("idx_tags_name_unique", table_name="tags")
    op.drop_table("tags")
