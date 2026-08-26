"""add timers table

Revision ID: ghxrmguaywg6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-11 12:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import enum_exists, index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = "ghxrmguaywg6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

timer_type_enum = postgresql.ENUM(
    "preset", "user_created", name="timertype", create_type=False
)


def upgrade() -> None:
    if not enum_exists("timertype"):
        op.execute("CREATE TYPE timertype AS ENUM ('preset', 'user_created')")

    if table_exists("timers"):
        return

    op.create_table(
        "timers",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("type", timer_type_enum, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("audio_url", sa.String(length=1000), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )

    if not index_exists("timers", "idx_timers_user_id"):
        op.create_index("idx_timers_user_id", "timers", ["user_id"])
    if not index_exists("timers", "idx_timers_type"):
        op.create_index("idx_timers_type", "timers", ["type"])


def downgrade() -> None:
    op.drop_index("idx_timers_type", table_name="timers")
    op.drop_index("idx_timers_user_id", table_name="timers")
    op.drop_table("timers")
    op.execute("DROP TYPE timertype")
