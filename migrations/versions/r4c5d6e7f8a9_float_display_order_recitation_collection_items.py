"""float display_order on recitation_collection_items

Revision ID: r4c5d6e7f8a9
Revises: np1a2b3c4d5e
Create Date: 2026-09-10 16:10:00.000000

Lets clients patch a single item to a fractional order (e.g. 1.4) so it can
sit between neighbors without rewriting every row. Active items in a
collection cannot share a display_order.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import index_exists

revision: str = "r4c5d6e7f8a9"
down_revision: Union[str, None] = "np1a2b3c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ITEMS_TABLE = "recitation_collection_items"
UNIQUE_INDEX = "uq_recitation_collection_items_collection_display_order"


def _column_udt_name(table_name: str, column_name: str) -> str | None:
    result = op.get_bind().execute(
        sa.text(
            """
            SELECT udt_name
            FROM information_schema.columns
            WHERE table_name = :table AND column_name = :column
            """
        ),
        {"table": table_name, "column": column_name},
    )
    return result.scalar()


def upgrade() -> None:
    if _column_udt_name(ITEMS_TABLE, "display_order") == "int4":
        op.alter_column(
            ITEMS_TABLE,
            "display_order",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=False,
            postgresql_using="display_order::double precision",
        )

    # Existing integer rows can share an order if they were written before
    # uniqueness was enforced. Nudge later duplicates by a tiny fraction so
    # the unique index can be created without dropping data.
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY recitation_collection_id, display_order
                        ORDER BY id
                    ) AS rn
                FROM recitation_collection_items
                WHERE deleted_at IS NULL
            )
            UPDATE recitation_collection_items AS items
            SET display_order = items.display_order + ((ranked.rn - 1) * 0.0001)
            FROM ranked
            WHERE items.id = ranked.id AND ranked.rn > 1
            """
        )
    )

    if not index_exists(ITEMS_TABLE, UNIQUE_INDEX):
        op.create_index(
            UNIQUE_INDEX,
            ITEMS_TABLE,
            ["recitation_collection_id", "display_order"],
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL"),
        )


def downgrade() -> None:
    if index_exists(ITEMS_TABLE, UNIQUE_INDEX):
        op.drop_index(UNIQUE_INDEX, table_name=ITEMS_TABLE)

    if _column_udt_name(ITEMS_TABLE, "display_order") == "float8":
        op.alter_column(
            ITEMS_TABLE,
            "display_order",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="ROUND(display_order)::integer",
        )
