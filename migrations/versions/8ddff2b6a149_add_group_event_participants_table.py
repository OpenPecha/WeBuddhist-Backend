"""add group_event_participants table

Revision ID: 8ddff2b6a149
Revises: b0c1d2e3f4a5
Create Date: 2026-07-22 16:07:14.802784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ddff2b6a149'
down_revision: Union[str, None] = 'b0c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group_event_participants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id", "user_id", name="uq_group_event_participants_event_user"
        ),
    )
    op.create_index(
        "idx_group_event_participants_event_id",
        "group_event_participants",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        "idx_group_event_participants_user_id",
        "group_event_participants",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_group_event_participants_user_id", table_name="group_event_participants"
    )
    op.drop_index(
        "idx_group_event_participants_event_id", table_name="group_event_participants"
    )
    op.drop_table("group_event_participants")
