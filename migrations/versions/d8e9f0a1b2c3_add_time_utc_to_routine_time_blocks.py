"""add time_utc to routine_time_blocks

Revision ID: d8e9f0a1b2c3
Revises: dfd2dcd179fd
Create Date: 2026-06-30 12:00:00.000000

Adds ``time_utc`` for UTC-based notification matching. Keeps the existing
``uq_routine_time`` index on ``(routine_id, time)`` and adds
``uq_routine_time_utc`` on ``(routine_id, time_utc)``.

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
down_revision: Union[str, None] = "dfd2dcd179fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _local_hhmm_to_utc_time(local_hhmm: str, timezone_name: str | None) -> time:
    """Self-contained backfill conversion (original migration implementation)."""
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


def _convert_local_hhmm_to_utc(local_hhmm: str, timezone_name: str | None) -> time:
    """Prefer shared app helper; fall back to inline conversion when unavailable."""
    try:
        from pecha_api.timezone_utils import local_hhmm_to_utc_time

        return local_hhmm_to_utc_time(local_hhmm, timezone_name or "UTC")
    except ImportError:
        return _local_hhmm_to_utc_time(local_hhmm, timezone_name)


def _column_is_nullable(table: str, column: str) -> bool:
    if not column_exists(table, column):
        return True
    return (
        op.get_bind()
        .execute(
            text(
                """
                SELECT is_nullable = 'YES'
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table
                  AND column_name = :column
                """
            ),
            {"table": table, "column": column},
        )
        .scalar()
        is True
    )


def _write_time_utc(connection, row_id, local_hhmm: str, timezone_name: str | None) -> None:
    time_utc = _convert_local_hhmm_to_utc(local_hhmm, timezone_name)
    connection.execute(
        text("UPDATE routine_time_blocks SET time_utc = :time_utc WHERE id = :id"),
        {"time_utc": time_utc, "id": row_id},
    )


def _backfill_time_utc(connection) -> None:
    rows = connection.execute(
        text(
            """
            SELECT rtb.id, rtb.time, r.timezone
            FROM routine_time_blocks rtb
            LEFT JOIN routines r ON r.id = rtb.routine_id
            WHERE rtb.time_utc IS NULL
            """
        )
    ).fetchall()

    for row in rows:
        _write_time_utc(connection, row.id, row.time, row.timezone)

    remaining = connection.execute(
        text("SELECT id, time FROM routine_time_blocks WHERE time_utc IS NULL")
    ).fetchall()
    for row in remaining:
        _write_time_utc(connection, row.id, row.time, "UTC")


def upgrade() -> None:
    if not column_exists("routine_time_blocks", "time_utc"):
        op.add_column(
            "routine_time_blocks",
            sa.Column("time_utc", sa.Time(timezone=True), nullable=True),
        )

    _backfill_time_utc(op.get_bind())

    if _column_is_nullable("routine_time_blocks", "time_utc"):
        op.alter_column("routine_time_blocks", "time_utc", nullable=False)

    if not index_exists("routine_time_blocks", "uq_routine_time_utc"):
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
