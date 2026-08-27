"""add author group status column

Adds DRAFT/PUBLISHED/UNPUBLISHED to author groups, independent of is_public.
Existing rows are backfilled from is_public: public -> PUBLISHED,
private -> DRAFT.

Revision ID: ag1b2c3d4e5f
Revises: pm2b3c4d5e6f
Create Date: 2026-08-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ag1b2c3d4e5f"
down_revision: Union[str, None] = "pm2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

author_group_status_enum = sa.Enum(
    "DRAFT",
    "PUBLISHED",
    "UNPUBLISHED",
    name="author_group_status",
)


def upgrade() -> None:
    author_group_status_enum.create(op.get_bind(), checkfirst=True)
    # server_default keeps in-flight inserts valid during deploy.
    op.add_column(
        "author_groups",
        sa.Column(
            "status",
            author_group_status_enum,
            nullable=False,
            server_default="DRAFT",
        ),
    )
    # Backfill so existing public groups stay reachable by the app.
    op.execute(
        "UPDATE author_groups SET status = 'PUBLISHED' WHERE is_public = true"
    )
    op.execute(
        "UPDATE author_groups SET status = 'DRAFT' WHERE is_public = false"
    )
    op.create_index(
        "idx_author_groups_status_type",
        "author_groups",
        ["status", "group_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_author_groups_status_type", table_name="author_groups")
    op.drop_column("author_groups", "status")
    author_group_status_enum.drop(op.get_bind(), checkfirst=True)
