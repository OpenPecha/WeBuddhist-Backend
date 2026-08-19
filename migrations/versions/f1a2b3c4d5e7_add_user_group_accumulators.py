"""add user_group_accumulators table for per-user session soft delete

Revision ID: f1a2b3c4d5e7
Revises: e9f0a1b2c3d4
Create Date: 2026-07-01 12:00:00.000000

Each user can have multiple participation sessions in a group accumulator.
Soft-deleting a session resets the user's active progress while preserving
history. The group accumulator itself is unchanged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists, fk_exists, index_exists, table_exists
from migrations.group_accumulator_schema import ensure_group_accumulator_tables

revision: str = "f1a2b3c4d5e7"
down_revision: Union[str, None] = "e9f0a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    ensure_group_accumulator_tables()

    if not table_exists("user_group_accumulators"):
        op.create_table(
            "user_group_accumulators",
            sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
            sa.Column("group_accumulator_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
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
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["group_accumulator_id"],
                ["group_accumulators.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not index_exists("user_group_accumulators", "idx_user_group_accumulators_group_user"):
        op.create_index(
            "idx_user_group_accumulators_group_user",
            "user_group_accumulators",
            ["group_accumulator_id", "user_id"],
            unique=False,
        )
    if not index_exists("user_group_accumulators", "idx_user_group_accumulators_user"):
        op.create_index(
            "idx_user_group_accumulators_user",
            "user_group_accumulators",
            ["user_id"],
            unique=False,
        )

    if not column_exists("group_accumulator_history", "user_group_accumulator_id"):
        op.add_column(
            "group_accumulator_history",
            sa.Column("user_group_accumulator_id", sa.UUID(), nullable=True),
        )

    if not fk_exists("group_accumulator_history", "group_accumulator_history_user_group_accumulator_id_fkey"):
        op.create_foreign_key(
            "group_accumulator_history_user_group_accumulator_id_fkey",
            "group_accumulator_history",
            "user_group_accumulators",
            ["user_group_accumulator_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not index_exists(
        "group_accumulator_history",
        "idx_group_accumulator_history_user_group_accumulator_id",
    ):
        op.create_index(
            "idx_group_accumulator_history_user_group_accumulator_id",
            "group_accumulator_history",
            ["user_group_accumulator_id"],
            unique=False,
        )

    _backfill_user_group_accumulators()


def _backfill_user_group_accumulators() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            INSERT INTO user_group_accumulators (id, group_accumulator_id, user_id, created_at, updated_at)
            SELECT gen_random_uuid(), j.group_accumulator_id, j.user_id, j.created_at, j.created_at
            FROM group_accumulator_joins j
            WHERE NOT EXISTS (
                SELECT 1 FROM user_group_accumulators uga
                WHERE uga.group_accumulator_id = j.group_accumulator_id
                  AND uga.user_id = j.user_id
                  AND uga.deleted_at IS NULL
            )
        """)
    )

    conn.execute(
        sa.text("""
            INSERT INTO user_group_accumulators (id, group_accumulator_id, user_id, created_at, updated_at)
            SELECT gen_random_uuid(), h.group_accumulator_id, h.user_id, MIN(h.created_at), MIN(h.created_at)
            FROM group_accumulator_history h
            WHERE NOT EXISTS (
                SELECT 1 FROM user_group_accumulators uga
                WHERE uga.group_accumulator_id = h.group_accumulator_id
                  AND uga.user_id = h.user_id
            )
            GROUP BY h.group_accumulator_id, h.user_id
        """)
    )

    conn.execute(
        sa.text("""
            UPDATE group_accumulator_history h
            SET user_group_accumulator_id = uga.id
            FROM user_group_accumulators uga
            WHERE h.group_accumulator_id = uga.group_accumulator_id
              AND h.user_id = uga.user_id
              AND h.user_group_accumulator_id IS NULL
              AND uga.deleted_at IS NULL
        """)
    )


def downgrade() -> None:
    if index_exists(
        "group_accumulator_history",
        "idx_group_accumulator_history_user_group_accumulator_id",
    ):
        op.drop_index(
            "idx_group_accumulator_history_user_group_accumulator_id",
            table_name="group_accumulator_history",
        )
    if fk_exists("group_accumulator_history", "group_accumulator_history_user_group_accumulator_id_fkey"):
        op.drop_constraint(
            "group_accumulator_history_user_group_accumulator_id_fkey",
            "group_accumulator_history",
            type_="foreignkey",
        )
    if column_exists("group_accumulator_history", "user_group_accumulator_id"):
        op.drop_column("group_accumulator_history", "user_group_accumulator_id")

    if index_exists("user_group_accumulators", "idx_user_group_accumulators_user"):
        op.drop_index("idx_user_group_accumulators_user", table_name="user_group_accumulators")
    if index_exists("user_group_accumulators", "idx_user_group_accumulators_group_user"):
        op.drop_index(
            "idx_user_group_accumulators_group_user",
            table_name="user_group_accumulators",
        )
    if table_exists("user_group_accumulators"):
        op.drop_table("user_group_accumulators")
