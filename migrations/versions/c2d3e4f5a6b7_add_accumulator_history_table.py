"""add accumulator_history table

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-06-12 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accumulator_history",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("accumulator_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["accumulator_id"], ["accumulators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_accumulator_history_accumulator_id", "accumulator_history", ["accumulator_id"], unique=False)
    op.create_index("idx_accumulator_history_user_id", "accumulator_history", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_accumulator_history_user_id", table_name="accumulator_history")
    op.drop_index("idx_accumulator_history_accumulator_id", table_name="accumulator_history")
    op.drop_table("accumulator_history")
