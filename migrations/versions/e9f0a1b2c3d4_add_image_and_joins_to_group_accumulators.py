"""add image_key and group_accumulator_joins

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-06-30 14:00:00.000000

Adds optional cover image to group accumulators and a join table so users
can explicitly enroll in a group accumulator (auto-joining the parent group).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists, index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists("group_accumulators", "image_key"):
        op.add_column(
            "group_accumulators",
            sa.Column("image_key", sa.String(length=1000), nullable=True),
        )

    if not table_exists("group_accumulator_joins"):
        op.create_table(
            "group_accumulator_joins",
            sa.Column("group_accumulator_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["group_accumulator_id"],
                ["group_accumulators.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("group_accumulator_id", "user_id"),
            sa.UniqueConstraint(
                "group_accumulator_id",
                "user_id",
                name="uq_group_accumulator_joins_accumulator_user",
            ),
        )

    if not index_exists("group_accumulator_joins", "idx_group_accumulator_joins_accumulator_user"):
        op.create_index(
            "idx_group_accumulator_joins_accumulator_user",
            "group_accumulator_joins",
            ["group_accumulator_id", "user_id"],
            unique=False,
        )
    if not index_exists("group_accumulator_joins", "idx_group_accumulator_joins_user"):
        op.create_index(
            "idx_group_accumulator_joins_user",
            "group_accumulator_joins",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    if index_exists("group_accumulator_joins", "idx_group_accumulator_joins_user"):
        op.drop_index("idx_group_accumulator_joins_user", table_name="group_accumulator_joins")
    if index_exists("group_accumulator_joins", "idx_group_accumulator_joins_accumulator_user"):
        op.drop_index(
            "idx_group_accumulator_joins_accumulator_user",
            table_name="group_accumulator_joins",
        )
    if table_exists("group_accumulator_joins"):
        op.drop_table("group_accumulator_joins")
    if column_exists("group_accumulators", "image_key"):
        op.drop_column("group_accumulators", "image_key")
