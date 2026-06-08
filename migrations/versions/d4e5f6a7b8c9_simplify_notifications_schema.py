"""simplify notifications schema — drop reference_type and action columns

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("idx_notifications_reference", table_name="notifications")
    op.drop_column("notifications", "action_2_path")
    op.drop_column("notifications", "action_2_method")
    op.drop_column("notifications", "action_2_label")
    op.drop_column("notifications", "action_1_path")
    op.drop_column("notifications", "action_1_method")
    op.drop_column("notifications", "action_1_label")
    op.drop_column("notifications", "reference_type")
    op.create_index(
        "idx_notifications_category_reference",
        "notifications",
        ["category", "reference_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_notifications_category_reference", table_name="notifications")
    op.add_column(
        "notifications",
        sa.Column("reference_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("action_1_label", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("action_1_method", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("action_1_path", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("action_2_label", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("action_2_method", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("action_2_path", sa.String(length=500), nullable=True),
    )
    op.create_index(
        "idx_notifications_reference",
        "notifications",
        ["reference_type", "reference_id"],
        unique=False,
    )
