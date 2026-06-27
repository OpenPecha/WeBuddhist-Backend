"""fix series_partner unique constraint to series_id + group_id

Revision ID: b1c2d3e4f5a7
Revises: z5a6b7c8d9e0
Create Date: 2026-06-27 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import table_exists

revision: str = "b1c2d3e4f5a7"
down_revision: Union[str, None] = "z5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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


def upgrade() -> None:
    if not table_exists("series_partner"):
        return

    if _constraint_exists("series_partner", "uq_series_partner_series"):
        op.drop_constraint("uq_series_partner_series", "series_partner", type_="unique")

    if not _constraint_exists("series_partner", "uq_series_partner_series_group"):
        op.create_unique_constraint(
            "uq_series_partner_series_group",
            "series_partner",
            ["series_id", "group_id"],
        )


def downgrade() -> None:
    if not table_exists("series_partner"):
        return

    if _constraint_exists("series_partner", "uq_series_partner_series_group"):
        op.drop_constraint("uq_series_partner_series_group", "series_partner", type_="unique")

    if not _constraint_exists("series_partner", "uq_series_partner_series"):
        op.create_unique_constraint(
            "uq_series_partner_series",
            "series_partner",
            ["series_id"],
        )
