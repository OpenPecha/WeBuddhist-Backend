"""add_user_daily_logs_table

Revision ID: f2a3b4c5d6e7
Revises: 4c9060e232ad
Create Date: 2026-06-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "4c9060e232ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_daily_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_user_daily_logs_user_date"),
    )
    op.create_index("idx_user_daily_logs_user_id", "user_daily_logs", ["user_id"], unique=False)
    op.create_index("idx_user_daily_logs_user_date", "user_daily_logs", ["user_id", "log_date"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_user_daily_logs_user_date", table_name="user_daily_logs")
    op.drop_index("idx_user_daily_logs_user_id", table_name="user_daily_logs")
    op.drop_table("user_daily_logs")
