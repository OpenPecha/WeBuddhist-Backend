"""add group_accumulator tables

Revision ID: z1a2b3c4d5e6
Revises: ffca36f72f3f
Create Date: 2026-06-26 16:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "z1a2b3c4d5e6"
down_revision: Union[str, None] = "ffca36f72f3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create group_accumulators table
    op.create_table(
        "group_accumulators",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("mantra_id", sa.UUID(), nullable=True),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("target_count", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["mantra_id"], ["mantra.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_group_accumulators_group_id", "group_accumulators", ["group_id"], unique=False)
    op.create_index("idx_group_accumulators_mantra_id", "group_accumulators", ["mantra_id"], unique=False)

    # Create group_accumulator_history table
    op.create_table(
        "group_accumulator_history",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("group_accumulator_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["group_accumulator_id"], ["group_accumulators.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_group_accumulator_history_group_accumulator_id", "group_accumulator_history", ["group_accumulator_id"], unique=False)
    op.create_index("idx_group_accumulator_history_user_id", "group_accumulator_history", ["user_id"], unique=False)


def downgrade() -> None:
    # Drop group_accumulator_history table
    op.drop_index("idx_group_accumulator_history_user_id", table_name="group_accumulator_history")
    op.drop_index("idx_group_accumulator_history_group_accumulator_id", table_name="group_accumulator_history")
    op.drop_table("group_accumulator_history")

    # Drop group_accumulators table
    op.drop_index("idx_group_accumulators_mantra_id", table_name="group_accumulators")
    op.drop_index("idx_group_accumulators_group_id", table_name="group_accumulators")
    op.drop_table("group_accumulators")
