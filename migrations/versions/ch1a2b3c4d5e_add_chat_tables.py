"""add_chat_tables

Revision ID: ch1a2b3c4d5e
Revises: gp4d5e6f7g8h
Create Date: 2026-07-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'ch1a2b3c4d5e'
down_revision: Union[str, None] = 'gp4d5e6f7g8h'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_enum_type(name: str, values: str) -> None:
    op.execute(
        f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )


def upgrade() -> None:
    _ensure_enum_type('chat_room_member_role', "'CREATOR', 'MEMBER'")

    chat_room_member_role_enum = postgresql.ENUM(
        'CREATOR', 'MEMBER',
        name='chat_room_member_role',
        create_type=False,
    )

    op.create_table(
        'chat_rooms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('sender_id', sa.UUID(), nullable=True),
        sa.Column('receiver_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('img_url', sa.String(length=1000), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['author_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "(group_id IS NOT NULL AND sender_id IS NULL AND receiver_id IS NULL) OR "
            "(group_id IS NULL AND sender_id IS NOT NULL AND receiver_id IS NOT NULL AND sender_id <> receiver_id)",
            name='ck_chat_rooms_kind_shape',
        ),
    )
    op.create_index(
        'uq_chat_rooms_group_id',
        'chat_rooms',
        ['group_id'],
        unique=True,
        postgresql_where=sa.text("group_id IS NOT NULL AND deleted_at IS NULL"),
    )
    op.create_index(
        'uq_chat_rooms_sender_receiver',
        'chat_rooms',
        ['sender_id', 'receiver_id'],
        unique=True,
        postgresql_where=sa.text("group_id IS NULL AND deleted_at IS NULL"),
    )
    op.create_index(
        'idx_chat_rooms_updated_at',
        'chat_rooms',
        [sa.text('updated_at DESC')],
        unique=False,
    )
    op.create_index('idx_chat_rooms_created_by', 'chat_rooms', ['created_by'], unique=False)

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('sender_id', sa.UUID(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'idx_chat_messages_room_created',
        'chat_messages',
        ['room_id', sa.text('created_at DESC')],
        unique=False,
    )
    op.create_index(
        'idx_chat_messages_room_active',
        'chat_messages',
        ['room_id', 'created_at'],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        'chat_room_members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', chat_room_member_role_enum, nullable=False, server_default='MEMBER'),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id', 'user_id', name='uq_chat_room_members_room_user'),
    )
    op.create_index('idx_chat_room_members_room_id', 'chat_room_members', ['room_id'], unique=False)
    op.create_index('idx_chat_room_members_user_id', 'chat_room_members', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_chat_room_members_user_id', table_name='chat_room_members')
    op.drop_index('idx_chat_room_members_room_id', table_name='chat_room_members')
    op.drop_table('chat_room_members')

    op.drop_index('idx_chat_messages_room_active', table_name='chat_messages')
    op.drop_index('idx_chat_messages_room_created', table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_index('idx_chat_rooms_created_by', table_name='chat_rooms')
    op.drop_index('idx_chat_rooms_updated_at', table_name='chat_rooms')
    op.drop_index('uq_chat_rooms_sender_receiver', table_name='chat_rooms')
    op.drop_index('uq_chat_rooms_group_id', table_name='chat_rooms')
    op.drop_table('chat_rooms')

    op.execute('DROP TYPE IF EXISTS chat_room_member_role')
