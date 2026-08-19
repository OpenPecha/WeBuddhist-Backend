"""add parent_id to accumulators

Links a user-created accumulator back to the preset it was created from. Presets
themselves have no parent (NULL). The app fetches a user's accumulator by
GET /accumulators/{parent_id} and creates one via POST when none exists.

Revision ID: 8515254497fe
Revises: 9436ccdf01b6
Create Date: 2026-06-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8515254497fe"
down_revision: Union[str, None] = "9436ccdf01b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PARENT_FK = "accumulators_parent_id_fkey"
PARENT_INDEX = "idx_accumulators_parent_id"


def upgrade() -> None:
    op.add_column(
        "accumulators",
        sa.Column("parent_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        PARENT_FK,
        "accumulators",
        "accumulators",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(PARENT_INDEX, "accumulators", ["parent_id"])


def downgrade() -> None:
    op.drop_index(PARENT_INDEX, table_name="accumulators")
    op.drop_constraint(PARENT_FK, "accumulators", type_="foreignkey")
    op.drop_column("accumulators", "parent_id")
