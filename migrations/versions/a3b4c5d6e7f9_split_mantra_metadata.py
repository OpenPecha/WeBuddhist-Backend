"""split_mantra_metadata

Move text, meaning, language out of mantra into a new mantra_metadata table
(plus transliteration), so a mantra with shared audio_url can have metadata in
multiple languages. Mirrors the series / series_metadata pattern.

Revision ID: a3b4c5d6e7f9
Revises: b7c8d9e0f1a2
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a3b4c5d6e7f9'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mantra_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('mantra_id', sa.UUID(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('meaning', sa.Text(), nullable=True),
        sa.Column('transliteration', sa.Text(), nullable=True),
        sa.Column('language', postgresql.ENUM('EN', 'BO', 'ZH', name='languagecode', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['mantra_id'], ['mantra.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_mantra_metadata_mantra_id', 'mantra_metadata', ['mantra_id'])

    # Migrate existing per-mantra metadata into the new table.
    op.execute(
        """
        INSERT INTO mantra_metadata (id, mantra_id, text, meaning, transliteration, language)
        SELECT gen_random_uuid(), id, text, meaning, NULL, language
        FROM mantra
        """
    )

    op.drop_column('mantra', 'text')
    op.drop_column('mantra', 'meaning')
    op.drop_column('mantra', 'language')


def downgrade() -> None:
    op.add_column('mantra', sa.Column('text', sa.Text(), nullable=True))
    op.add_column('mantra', sa.Column('meaning', sa.Text(), nullable=True))
    op.add_column(
        'mantra',
        sa.Column('language', postgresql.ENUM('EN', 'BO', 'ZH', name='languagecode', create_type=False), nullable=True),
    )

    # Restore one metadata row per mantra (first by language) back onto mantra.
    op.execute(
        """
        UPDATE mantra m
        SET text = md.text,
            meaning = md.meaning,
            language = md.language
        FROM (
            SELECT DISTINCT ON (mantra_id) mantra_id, text, meaning, language
            FROM mantra_metadata
            ORDER BY mantra_id, language
        ) md
        WHERE md.mantra_id = m.id
        """
    )

    op.alter_column('mantra', 'text', nullable=False)
    op.alter_column('mantra', 'language', nullable=False)

    op.drop_index('idx_mantra_metadata_mantra_id', table_name='mantra_metadata')
    op.drop_table('mantra_metadata')
