"""add_content_type_to_accumulators

Add a content_type column (mantra|chant) to accumulators so an accumulator
row can represent either a mantra or a chant (text-based recitation).
Backfills existing rows based on whether mantra_id or text_id is set.

Revision ID: ct1a2b3c4d5e
Revises: p3q4r5s6t7u8
Create Date: 2026-07-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'ct1a2b3c4d5e'
down_revision: Union[str, None] = 'p3q4r5s6t7u8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

content_type_enum = postgresql.ENUM(
    'mantra', 'chant', name='contenttype', create_type=False
)


def upgrade() -> None:
    content_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'accumulators',
        sa.Column(
            'content_type',
            content_type_enum,
            nullable=False,
            server_default='mantra',
        ),
    )

    # Backfill: rows with a mantra_id stay 'mantra' (default already applied).
    # Rows with no mantra_id but a text_id are chants.
    op.execute(
        """
        UPDATE accumulators
        SET content_type = 'chant'
        WHERE mantra_id IS NULL AND text_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column('accumulators', 'content_type')
    content_type_enum.drop(op.get_bind(), checkfirst=True)
