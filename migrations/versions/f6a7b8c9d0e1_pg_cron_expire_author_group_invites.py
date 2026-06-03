"""expire pending author group invites via PostgreSQL (pg_cron when available)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-19 12:00:00.000000

Creates expire_pending_author_group_invites() and schedules it every 5 minutes with
pg_cron when the extension can be loaded (RDS, self-hosted with shared_preload_libraries).

Local postgres:16-alpine typically has no pg_cron; migration still applies the function
and runs it once. Enable pg_cron in production or run manually:
  SELECT expire_pending_author_group_invites();
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PG_CRON_JOB_NAME = "expire-author-group-invites"
_PG_CRON_SCHEDULE = "*/5 * * * *"


def _run_optional_pg_cron_steps(statements: list[str]) -> None:
    bind = op.get_bind()
    with bind.begin_nested():
        for statement in statements:
            bind.execute(sa.text(statement))


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION expire_pending_author_group_invites()
        RETURNS integer
        LANGUAGE plpgsql
        AS $$
        DECLARE
            updated_count integer;
        BEGIN
            UPDATE author_group_invites
            SET status = 'EXPIRED'
            WHERE status = 'PENDING'
              AND expires_at < NOW();
            GET DIAGNOSTICS updated_count = ROW_COUNT;
            RETURN updated_count;
        END;
        $$;
        """
    )
    op.execute("SELECT expire_pending_author_group_invites()")

    try:
        _run_optional_pg_cron_steps(
            [
                "CREATE EXTENSION IF NOT EXISTS pg_cron",
                f"SELECT cron.unschedule('{_PG_CRON_JOB_NAME}')",
                f"""
                SELECT cron.schedule(
                    '{_PG_CRON_JOB_NAME}',
                    '{_PG_CRON_SCHEDULE}',
                    $$SELECT expire_pending_author_group_invites()$$
                )
                """,
            ]
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        _run_optional_pg_cron_steps(
            [f"SELECT cron.unschedule('{_PG_CRON_JOB_NAME}')"]
        )
    except Exception:
        pass

    op.execute("DROP FUNCTION IF EXISTS expire_pending_author_group_invites()")
