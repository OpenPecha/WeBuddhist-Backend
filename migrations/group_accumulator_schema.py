"""Idempotent helpers to ensure group accumulator tables exist.

Production databases may have alembic_version past the branch that originally
created these tables (merge/stamp drift). Migrations that alter group
accumulators call ensure_group_accumulator_tables() first.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists, fk_exists, index_exists, table_exists


def ensure_group_accumulator_tables() -> None:
    """Create group accumulator tables at their current schema if missing."""
    if not table_exists("group_accumulators"):
        _create_group_accumulators()
    else:
        _upgrade_group_accumulators_columns()

    if not table_exists("group_accumulator_history"):
        _create_group_accumulator_history()


def _create_group_accumulators() -> None:
    op.create_table(
        "group_accumulators",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("accumulator_id", sa.UUID(), nullable=True),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("image_key", sa.String(length=1000), nullable=True),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["accumulator_id"], ["accumulators.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_id"], ["author_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_group_accumulators_group_id",
        "group_accumulators",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "idx_group_accumulators_accumulator_id",
        "group_accumulators",
        ["accumulator_id"],
        unique=False,
    )


def _upgrade_group_accumulators_columns() -> None:
    """Add columns that may be missing when the table exists from a partial branch."""
    if column_exists("group_accumulators", "mantra_id") and not column_exists(
        "group_accumulators", "accumulator_id"
    ):
        if index_exists("group_accumulators", "idx_group_accumulators_mantra_id"):
            op.drop_index("idx_group_accumulators_mantra_id", table_name="group_accumulators")
        if fk_exists("group_accumulators", "group_accumulators_mantra_id_fkey"):
            op.drop_constraint(
                "group_accumulators_mantra_id_fkey",
                "group_accumulators",
                type_="foreignkey",
            )
        op.alter_column(
            "group_accumulators",
            "mantra_id",
            new_column_name="accumulator_id",
        )
        op.create_foreign_key(
            "group_accumulators_accumulator_id_fkey",
            "group_accumulators",
            "accumulators",
            ["accumulator_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            "idx_group_accumulators_accumulator_id",
            "group_accumulators",
            ["accumulator_id"],
            unique=False,
        )

    if not column_exists("group_accumulators", "deleted_at"):
        op.add_column(
            "group_accumulators",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not column_exists("group_accumulators", "title"):
        op.add_column(
            "group_accumulators",
            sa.Column("title", sa.String(), nullable=True),
        )

    if not column_exists("group_accumulators", "image_key"):
        op.add_column(
            "group_accumulators",
            sa.Column("image_key", sa.String(length=1000), nullable=True),
        )


def _create_group_accumulator_history() -> None:
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
        sa.ForeignKeyConstraint(
            ["group_accumulator_id"],
            ["group_accumulators.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_group_accumulator_history_group_accumulator_id",
        "group_accumulator_history",
        ["group_accumulator_id"],
        unique=False,
    )
    op.create_index(
        "idx_group_accumulator_history_user_id",
        "group_accumulator_history",
        ["user_id"],
        unique=False,
    )
