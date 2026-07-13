"""add china_restricted_items table for China timezone content exclusions

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e7
Create Date: 2026-07-05 12:00:00.000000

Items listed in this table are hidden from clients whose X-Timezone header
matches a Chinese IANA timezone (see pecha_api/assets/chinese_timezone.json).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import index_exists, table_exists

revision: str = "g2h3i4j5k6l7"
down_revision: Union[str, None] = "f1a2b3c4d5e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

china_restricted_item_type = postgresql.ENUM(
    "MANTRA",
    "ACCUMULATOR",
    "GROUP_ACCUMULATOR",
    "PLAN",
    "SERIES",
    "GROUP",
    "RECITATION",
    "RECITATION_COLLECTION",
    name="china_restricted_item_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE china_restricted_item_type AS ENUM (
                'MANTRA',
                'ACCUMULATOR',
                'GROUP_ACCUMULATOR',
                'PLAN',
                'SERIES',
                'GROUP',
                'RECITATION',
                'RECITATION_COLLECTION'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    if not table_exists("china_restricted_items"):
        op.create_table(
            "china_restricted_items",
            sa.Column(
                "id",
                sa.UUID(),
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("item_type", china_restricted_item_type, nullable=False),
            sa.Column("item_id", sa.UUID(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "item_type",
                "item_id",
                name="uq_china_restricted_items_type_id",
            ),
        )

    if not index_exists("china_restricted_items", "idx_china_restricted_items_item_type"):
        op.create_index(
            "idx_china_restricted_items_item_type",
            "china_restricted_items",
            ["item_type"],
            unique=False,
        )
    if not index_exists("china_restricted_items", "idx_china_restricted_items_item_id"):
        op.create_index(
            "idx_china_restricted_items_item_id",
            "china_restricted_items",
            ["item_id"],
            unique=False,
        )


def downgrade() -> None:
    if index_exists("china_restricted_items", "idx_china_restricted_items_item_id"):
        op.drop_index("idx_china_restricted_items_item_id", table_name="china_restricted_items")
    if index_exists("china_restricted_items", "idx_china_restricted_items_item_type"):
        op.drop_index("idx_china_restricted_items_item_type", table_name="china_restricted_items")
    if table_exists("china_restricted_items"):
        op.drop_table("china_restricted_items")
    op.execute("DROP TYPE IF EXISTS china_restricted_item_type")
