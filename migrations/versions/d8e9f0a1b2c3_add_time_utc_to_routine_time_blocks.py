"""add time_utc to routine_time_blocks

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-06-30 12:00:00.000000

"""
from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Sequence, Union
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

from migrations.idempotency import column_exists, index_exists

# revision identifiers, used by Alembic.
revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _local_hhmm_to_utc_time(local_hhmm: str, timezone_name: str | None) -> time:
    hour_str, minute_str = local_hhmm.split(":")
    hour, minute = int(hour_str), int(minute_str)
    reference_date = datetime.now(timezone.utc).date()

    if timezone_name and timezone_name.strip():
        try:
            tz = ZoneInfo(timezone_name.strip())
            local_dt = datetime.combine(reference_date, time(hour, minute), tzinfo=tz)
            return local_dt.astimezone(timezone.utc).timetz()
        except Exception:
            pass

    return time(hour, minute, tzinfo=timezone.utc)


def _backfill_time_utc(connection) -> None:
    rows = connection.execute(
        text(
            """
            SELECT rtb.id, rtb.time, r.timezone
            FROM routine_time_blocks rtb
            JOIN routines r ON r.id = rtb.routine_id
            WHERE rtb.deleted_at IS NULL
            """
        )
    ).fetchall()

    for row in rows:
        time_utc = _local_hhmm_to_utc_time(row.time, row.timezone)
        connection.execute(
            text("UPDATE routine_time_blocks SET time_utc = :time_utc WHERE id = :id"),
            {"time_utc": time_utc, "id": row.id},
        )


def upgrade() -> None:
    if not column_exists("routine_time_blocks", "time_utc"):
        op.add_column(
            "routine_time_blocks",
            sa.Column("time_utc", sa.Time(timezone=True), nullable=True),
        )

    connection = op.get_bind()
    _backfill_time_utc(connection)

    op.alter_column("routine_time_blocks", "time_utc", nullable=False)

    if index_exists("routine_time_blocks", "uq_routine_time_utc"):
        return

    op.create_index(
        "uq_routine_time_utc",
        "routine_time_blocks",
        ["routine_id", "time_utc"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    if index_exists("routine_time_blocks", "uq_routine_time_utc"):
        op.drop_index(
            "uq_routine_time_utc",
            table_name="routine_time_blocks",
            postgresql_where=sa.text("deleted_at IS NULL"),
        )

    if column_exists("routine_time_blocks", "time_utc"):
        op.drop_column("routine_time_blocks", "time_utc")
