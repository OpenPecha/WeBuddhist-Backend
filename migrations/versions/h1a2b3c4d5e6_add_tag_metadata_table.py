"""add tag_metadata table

Revision ID: h1a2b3c4d5e6
Revises: d7e8f9a0b1c2
Create Date: 2026-06-17 17:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h1a2b3c4d5e6'
down_revision: Union[str, None] = 'd7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tag_metadata table
    op.create_table('tag_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tag_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('language', postgresql.ENUM('EN', 'BO', 'ZH', 'HI', 'NE', 'MN', name='languagecode', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_id', 'language', name='uq_tag_metadata_tag_language')
    )
    op.create_index('idx_tag_metadata_tag_language', 'tag_metadata', ['tag_id', 'language'], unique=False)
    
    # Migrate existing data from tags to tag_metadata with language='EN'
    op.execute("""
        INSERT INTO tag_metadata (id, tag_id, name, description, language)
        SELECT 
            gen_random_uuid(),
            id,
            name,
            description,
            'EN'
        FROM tags
        WHERE deleted_at IS NULL
    """)
    
    # Drop the unique index on tags.name
    op.drop_index('idx_tags_name_unique', table_name='tags')
    
    # Drop name and description columns from tags table
    op.drop_column('tags', 'name')
    op.drop_column('tags', 'description')


def downgrade() -> None:
    # Add name and description columns back to tags table
    op.add_column('tags', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('tags', sa.Column('description', sa.Text(), nullable=True))
    
    # Migrate data back from tag_metadata to tags (using EN language)
    op.execute("""
        UPDATE tags
        SET name = tm.name,
            description = tm.description
        FROM tag_metadata tm
        WHERE tags.id = tm.tag_id
        AND tm.language = 'EN'
    """)
    
    # Make name column not nullable
    op.alter_column('tags', 'name', nullable=False)
    
    # Recreate the unique index on tags.name
    op.create_index('idx_tags_name_unique', 'tags', ['name'], unique=True, postgresql_where=sa.text("deleted_at IS NULL"))
    
    # Drop tag_metadata table
    op.drop_index('idx_tag_metadata_tag_language', table_name='tag_metadata')
    op.drop_table('tag_metadata')
