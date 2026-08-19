"""add_group_recitation_collection_id_to_events

Revision ID: f92e40f4092f
Revises: 6f9d6b6333d5
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f92e40f4092f"
down_revision: Union[str, None] = "6f9d6b6333d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("group_recitation_collection_id", sa.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_events_group_recitation_collection_id",
        "events",
        "group_recitation_collections",
        ["group_recitation_collection_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_events_group_recitation_collection_id",
        "events",
        ["group_recitation_collection_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_events_group_recitation_collection_id", table_name="events")
    op.drop_constraint(
        "fk_events_group_recitation_collection_id", "events", type_="foreignkey"
    )
    op.drop_column("events", "group_recitation_collection_id")
