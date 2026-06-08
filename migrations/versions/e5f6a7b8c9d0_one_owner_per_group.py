"""one owner per group — demote extras and partial unique index

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE author_group_members AS m
        SET role = 'ADMIN'
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY group_id
                       ORDER BY created_at ASC, id ASC
                   ) AS rn
            FROM author_group_members
            WHERE role = 'OWNER'
        ) ranked
        WHERE m.id = ranked.id AND ranked.rn > 1
        """
    )
    op.create_index(
        "uq_author_group_members_one_owner_per_group",
        "author_group_members",
        ["group_id"],
        unique=True,
        postgresql_where=sa.text("role = 'OWNER'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_author_group_members_one_owner_per_group",
        table_name="author_group_members",
    )
