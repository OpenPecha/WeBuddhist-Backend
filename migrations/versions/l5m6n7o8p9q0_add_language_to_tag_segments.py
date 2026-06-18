"""add language to tag_segments

Revision ID: l5m6n7o8p9q0
Revises: 888b759bcd6a
Create Date: 2026-06-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "l5m6n7o8p9q0"
down_revision: Union[str, None] = "888b759bcd6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tag_segments",
        sa.Column(
            "language",
            postgresql.ENUM("EN", "BO", "ZH", "HI", "NE", "MN", name="languagecode", create_type=False),
            nullable=True,
        ),
    )
    op.execute("UPDATE tag_segments SET language = 'EN'")
    op.alter_column("tag_segments", "language", nullable=False)
    op.drop_constraint("tag_segments_pkey", "tag_segments", type_="primary")
    op.create_primary_key(
        "tag_segments_pkey",
        "tag_segments",
        ["tag_id", "segment_id", "language"],
    )


def downgrade() -> None:
    op.drop_constraint("tag_segments_pkey", "tag_segments", type_="primary")
    op.create_primary_key(
        "tag_segments_pkey",
        "tag_segments",
        ["tag_id", "segment_id"],
    )
    op.drop_column("tag_segments", "language")
