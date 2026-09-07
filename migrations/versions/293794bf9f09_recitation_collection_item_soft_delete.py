"""soft delete for recitation_collection_items to preserve chant completion history

Revision ID: 293794bf9f09
Revises: 7a1c9e2f4b6d
Create Date: 2026-09-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists

revision: str = "293794bf9f09"
down_revision: Union[str, None] = "7a1c9e2f4b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ITEMS_TABLE = "recitation_collection_items"
OLD_UNIQUE = "uq_recitation_collection_items_collection_text"

# recitation_collections.items has cascade="all, delete-orphan": deleting a
# collection still hard-deletes its item rows (only single-item removal goes
# through the new soft delete). chant_id's ON DELETE CASCADE onto those item
# rows must stay in place, or a collection delete for a collection with
# completion history would fail with a foreign-key violation.


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


def _collapse_duplicate_items_for_downgrade() -> None:
    """The old schema can only hold one row per (collection_id, text_id).

    While this migration was applied, an item could be soft-deleted and the
    same text re-added, leaving two rows sharing that key (one historical,
    one active). Recreating the strict unique constraint would fail on that
    duplicate, so collapse each such group down to a single row first:
    keep the active (deleted_at IS NULL) row when one exists, otherwise keep
    the most recently soft-deleted row. The rows removed here only ever
    existed because of the soft-delete feature this migration is undoing, so
    discarding them (and, via the still-cascading FK, their completions) is
    the correct behaviour for a full rollback.
    """
    op.get_bind().execute(
        sa.text(
            """
            DELETE FROM recitation_collection_items t
            USING recitation_collection_items keeper
            WHERE t.recitation_collection_id = keeper.recitation_collection_id
              AND t.text_id = keeper.text_id
              AND t.id <> keeper.id
              AND (
                    (t.deleted_at IS NOT NULL AND keeper.deleted_at IS NULL)
                 OR (
                        t.deleted_at IS NOT NULL
                    AND keeper.deleted_at IS NOT NULL
                    AND (t.deleted_at, t.id) < (keeper.deleted_at, keeper.id)
                    )
                  )
            """
        )
    )


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


def downgrade() -> None:
    if _index_exists(ITEMS_TABLE, OLD_UNIQUE):
        op.drop_index(OLD_UNIQUE, table_name=ITEMS_TABLE)

    if not _constraint_exists(ITEMS_TABLE, OLD_UNIQUE):
        _collapse_duplicate_items_for_downgrade()
        op.create_unique_constraint(
            OLD_UNIQUE,
            ITEMS_TABLE,
            ["recitation_collection_id", "text_id"],
        )

    if column_exists(ITEMS_TABLE, "deleted_at"):
        op.drop_column(ITEMS_TABLE, "deleted_at")
