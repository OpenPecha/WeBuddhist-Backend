"""rename_mantra_id_to_accumulator_id_in_group_accumulators

Revision ID: 815f69f1fc54
Revises: 97c2dd42247b
Create Date: 2026-06-29 17:46:21.236785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '815f69f1fc54'
down_revision: Union[str, None] = '97c2dd42247b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old foreign key constraint
    op.drop_constraint(
        "group_accumulators_mantra_id_fkey",
        "group_accumulators",
        type_="foreignkey"
    )
    
    # Drop the old index
    op.drop_index("idx_group_accumulators_mantra_id", table_name="group_accumulators")
    
    # Rename the column
    op.alter_column(
        "group_accumulators",
        "mantra_id",
        new_column_name="accumulator_id"
    )
    
    # Create new foreign key constraint pointing to accumulators table
    op.create_foreign_key(
        "group_accumulators_accumulator_id_fkey",
        "group_accumulators",
        "accumulators",
        ["accumulator_id"],
        ["id"],
        ondelete="SET NULL"
    )
    
    # Create new index
    op.create_index(
        "idx_group_accumulators_accumulator_id",
        "group_accumulators",
        ["accumulator_id"],
        unique=False
    )


def downgrade() -> None:
    # Drop the new foreign key constraint
    op.drop_constraint(
        "group_accumulators_accumulator_id_fkey",
        "group_accumulators",
        type_="foreignkey"
    )
    
    # Drop the new index
    op.drop_index("idx_group_accumulators_accumulator_id", table_name="group_accumulators")
    
    # Rename the column back
    op.alter_column(
        "group_accumulators",
        "accumulator_id",
        new_column_name="mantra_id"
    )
    
    # Recreate old foreign key constraint pointing to mantra table
    op.create_foreign_key(
        "group_accumulators_mantra_id_fkey",
        "group_accumulators",
        "mantra",
        ["mantra_id"],
        ["id"],
        ondelete="SET NULL"
    )
    
    # Recreate old index
    op.create_index(
        "idx_group_accumulators_mantra_id",
        "group_accumulators",
        ["mantra_id"],
        unique=False
    )
