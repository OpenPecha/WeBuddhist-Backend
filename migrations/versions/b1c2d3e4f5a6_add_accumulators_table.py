"""add accumulators table

Revision ID: b1c2d3e4f5a6
Revises: 2e73e46c9349
Create Date: 2026-06-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "2e73e46c9349"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accumulators",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("preset", "user_created", name="accumulatortype"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_count", sa.Integer(), nullable=True),
        sa.Column("current_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("text_id", sa.UUID(), nullable=True),
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

    op.create_index("idx_accumulators_user_id", "accumulators", ["user_id"])
    op.create_index("idx_accumulators_type", "accumulators", ["type"])


def downgrade() -> None:
    op.drop_index("idx_accumulators_type", table_name="accumulators")
    op.drop_index("idx_accumulators_user_id", table_name="accumulators")
    op.drop_table("accumulators")
    op.execute("DROP TYPE accumulatortype")
