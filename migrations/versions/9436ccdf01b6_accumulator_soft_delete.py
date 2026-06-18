"""add deleted_at to accumulators and drop history cascade

Revision ID: 9436ccdf01b6
Revises: d7e8f9a0b1c2
Create Date: 2026-06-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9436ccdf01b6"
down_revision: Union[str, None] = "d7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HISTORY_FK = "accumulator_history_accumulator_id_fkey"


def upgrade() -> None:
    op.add_column(
        "accumulators",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Drop the ON DELETE CASCADE so a (future) hard delete can never wipe a
    # user's accumulation history. Soft-delete keeps the row anyway, so the
    # recreated FK has no cascade behaviour.
    op.drop_constraint(HISTORY_FK, "accumulator_history", type_="foreignkey")
    op.create_foreign_key(
        HISTORY_FK,
        "accumulator_history",
        "accumulators",
        ["accumulator_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(HISTORY_FK, "accumulator_history", type_="foreignkey")
    op.create_foreign_key(
        HISTORY_FK,
        "accumulator_history",
        "accumulators",
        ["accumulator_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_column("accumulators", "deleted_at")
