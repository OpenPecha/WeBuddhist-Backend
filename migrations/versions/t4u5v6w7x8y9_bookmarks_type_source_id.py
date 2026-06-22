"""recreate bookmarks table with type + source_id

Revision ID: t4u5v6w7x8y9
Revises: s3t4u5v6w7x8
Create Date: 2026-06-22 12:00:00.000000

The bookmarks feature is not yet released (no rows in any environment), so the
old (text_id, verse_id) shape is dropped and recreated as a uniform
(type, source_id) shape. No data migration is required.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = 't4u5v6w7x8y9'
down_revision: Union[str, None] = 's3t4u5v6w7x8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BOOKMARK_TYPE_VALUES = ("TEXT", "PLAN", "SERIES", "ACCUMULATOR", "TIMER", "VERSE")

bookmark_type_column = postgresql.ENUM(
    *BOOKMARK_TYPE_VALUES,
    name="bookmark_type",
    create_type=False,
)


def upgrade() -> None:
    if table_exists("bookmarks"):
        op.drop_table("bookmarks")

    op.execute("DROP TYPE IF EXISTS bookmark_type")
    op.execute(
        "CREATE TYPE bookmark_type AS ENUM "
        "('TEXT', 'PLAN', 'SERIES', 'ACCUMULATOR', 'TIMER', 'VERSE')"
    )

    op.create_table(
        "bookmarks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", bookmark_type_column, nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "type", "source_id", name="uq_bookmarks_user_type_source"),
    )

    if not index_exists("bookmarks", "idx_bookmarks_user_id"):
        op.create_index("idx_bookmarks_user_id", "bookmarks", ["user_id"], unique=False)
    if not index_exists("bookmarks", "idx_bookmarks_type"):
        op.create_index("idx_bookmarks_type", "bookmarks", ["type"], unique=False)


def downgrade() -> None:
    if index_exists("bookmarks", "idx_bookmarks_type"):
        op.drop_index("idx_bookmarks_type", table_name="bookmarks")
    if index_exists("bookmarks", "idx_bookmarks_user_id"):
        op.drop_index("idx_bookmarks_user_id", table_name="bookmarks")
    if table_exists("bookmarks"):
        op.drop_table("bookmarks")

    op.execute("DROP TYPE IF EXISTS bookmark_type")

    op.create_table(
        "bookmarks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("text_id", sa.UUID(), nullable=False),
        sa.Column("verse_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "text_id", "verse_id", name="uq_bookmarks_user_text_verse"),
    )
    op.create_index("idx_bookmarks_user_id", "bookmarks", ["user_id"], unique=False)
    op.create_index("idx_bookmarks_text_id", "bookmarks", ["text_id"], unique=False)
