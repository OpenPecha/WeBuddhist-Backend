"""soft delete for recitation_collection_items to preserve chant completion history

Revision ID: 293794bf9f09
Revises: 7a1c9e2f4b6d
Create Date: 2026-09-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists, fk_exists

revision: str = "293794bf9f09"
down_revision: Union[str, None] = "7a1c9e2f4b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ITEMS_TABLE = "recitation_collection_items"
OLD_UNIQUE = "uq_recitation_collection_items_collection_text"
COMPLETIONS_TABLE = "recitation_collection_chant_completions"
CHANT_FK = "recitation_collection_chant_completions_chant_id_fkey"


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    result = op.get_bind().execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM pg_constraint
            WHERE conname = :name
              AND conrelid = CAST(:table AS regclass)
            """
        ),
        {"name": constraint_name, "table": table_name},
    )
    return result.scalar() > 0


def _index_exists(table_name: str, index_name: str) -> bool:
    result = op.get_bind().execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE tablename = :table AND indexname = :name"),
        {"table": table_name, "name": index_name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    if not column_exists(ITEMS_TABLE, "deleted_at"):
        op.add_column(
            ITEMS_TABLE,
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    # Replace the plain unique constraint with a partial unique index that
    # only applies to non-deleted rows, so a soft-deleted text_id can be
    # re-added to the same collection later.
    if _constraint_exists(ITEMS_TABLE, OLD_UNIQUE):
        op.drop_constraint(OLD_UNIQUE, ITEMS_TABLE, type_="unique")

    if not _index_exists(ITEMS_TABLE, OLD_UNIQUE):
        op.create_index(
            OLD_UNIQUE,
            ITEMS_TABLE,
            ["recitation_collection_id", "text_id"],
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL"),
        )

    # Drop the ON DELETE CASCADE so a (future) hard delete of an item can
    # never wipe a user's chant completion history. Deletion is soft now, so
    # the recreated FK simply drops the cascade behaviour.
    if fk_exists(COMPLETIONS_TABLE, CHANT_FK):
        op.drop_constraint(CHANT_FK, COMPLETIONS_TABLE, type_="foreignkey")
        op.create_foreign_key(
            CHANT_FK,
            COMPLETIONS_TABLE,
            ITEMS_TABLE,
            ["chant_id"],
            ["id"],
        )


def downgrade() -> None:
    if fk_exists(COMPLETIONS_TABLE, CHANT_FK):
        op.drop_constraint(CHANT_FK, COMPLETIONS_TABLE, type_="foreignkey")
        op.create_foreign_key(
            CHANT_FK,
            COMPLETIONS_TABLE,
            ITEMS_TABLE,
            ["chant_id"],
            ["id"],
            ondelete="CASCADE",
        )

    if _index_exists(ITEMS_TABLE, OLD_UNIQUE):
        op.drop_index(OLD_UNIQUE, table_name=ITEMS_TABLE)

    if not _constraint_exists(ITEMS_TABLE, OLD_UNIQUE):
        op.create_unique_constraint(
            OLD_UNIQUE,
            ITEMS_TABLE,
            ["recitation_collection_id", "text_id"],
        )

    if column_exists(ITEMS_TABLE, "deleted_at"):
        op.drop_column(ITEMS_TABLE, "deleted_at")
