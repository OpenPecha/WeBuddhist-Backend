"""add series_enrollment

Revision ID: 15513c3dbecf
Revises: e26ae474faf3
Create Date: 2026-05-26 21:18:21.086782

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '15513c3dbecf'
down_revision: Union[str, None] = 'e26ae474faf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SERIES_ENROLLMENT_FK = 'fk_user_plan_progress_series_enrollment_id'


def upgrade() -> None:
    from sqlalchemy.exc import ProgrammingError

    connection = op.get_bind()

    try:
        connection.execute(sa.text(
            "CREATE TYPE seriesstatus AS ENUM ('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED')"
        ))
    except ProgrammingError:
        pass

    try:
        connection.execute(sa.text(
            "CREATE TYPE enrollmentsource AS ENUM ('DIRECT', 'SERIES')"
        ))
    except ProgrammingError:
        pass

    seriesstatus_enum = postgresql.ENUM(
        'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED',
        name='seriesstatus',
        create_type=False,
    )
    enrollmentsource_enum = postgresql.ENUM(
        'DIRECT', 'SERIES',
        name='enrollmentsource',
        create_type=False,
    )

    op.create_table(
        'user_series_enrollment',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('series_id', sa.UUID(), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', seriesstatus_enum, nullable=False),
        sa.Column('auto_enroll_next', sa.Boolean(), nullable=False),
        sa.Column('current_plan_id', sa.UUID(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['current_plan_id'], ['plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['series_id'], ['series.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'series_id', name='uq_user_series_enrollment'),
    )
    op.create_index(
        'idx_user_series_enrollment_current_plan',
        'user_series_enrollment',
        ['current_plan_id'],
        unique=False,
    )
    op.create_index(
        'idx_user_series_enrollment_series',
        'user_series_enrollment',
        ['series_id'],
        unique=False,
    )
    op.create_index(
        'idx_user_series_enrollment_user_status',
        'user_series_enrollment',
        ['user_id', 'status'],
        unique=False,
    )

    op.add_column(
        'user_plan_progress',
        sa.Column(
            'enrollment_source',
            enrollmentsource_enum,
            nullable=False,
            server_default='DIRECT',
        ),
    )
    op.add_column(
        'user_plan_progress',
        sa.Column('series_enrollment_id', sa.UUID(), nullable=True),
    )
    op.add_column(
        'user_plan_progress',
        sa.Column('auto_enrolled', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'user_plan_progress',
        sa.Column('auto_enrolled_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column('user_plan_progress', 'enrollment_source', server_default=None)
    op.alter_column('user_plan_progress', 'auto_enrolled', server_default=None)

    op.create_index(
        'idx_user_progress_enrollment_source',
        'user_plan_progress',
        ['enrollment_source'],
        unique=False,
    )
    op.create_index(
        'idx_user_progress_series_enrollment',
        'user_plan_progress',
        ['series_enrollment_id'],
        unique=False,
    )
    op.create_foreign_key(
        SERIES_ENROLLMENT_FK,
        'user_plan_progress',
        'user_series_enrollment',
        ['series_enrollment_id'],
        ['id'],
        ondelete='CASCADE',
    )

    _drop_legacy_series_plan_order()


def _drop_legacy_series_plan_order() -> None:
    """Remove series_plan_order if a previous revision of this migration created it."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'series_plan_order' not in inspector.get_table_names():
        return
    op.drop_index('idx_series_plan_order_series', table_name='series_plan_order')
    op.drop_index('idx_series_plan_order_display', table_name='series_plan_order')
    op.drop_table('series_plan_order')


def downgrade() -> None:
    for fk_name in (
        SERIES_ENROLLMENT_FK,
        'user_plan_progress_series_enrollment_id_fkey',
    ):
        op.execute(
            sa.text(
                f'ALTER TABLE user_plan_progress DROP CONSTRAINT IF EXISTS "{fk_name}"'
            )
        )
    op.drop_index('idx_user_progress_series_enrollment', table_name='user_plan_progress')
    op.drop_index('idx_user_progress_enrollment_source', table_name='user_plan_progress')
    op.drop_column('user_plan_progress', 'auto_enrolled_at')
    op.drop_column('user_plan_progress', 'auto_enrolled')
    op.drop_column('user_plan_progress', 'series_enrollment_id')
    op.drop_column('user_plan_progress', 'enrollment_source')
    op.drop_index('idx_user_series_enrollment_user_status', table_name='user_series_enrollment')
    op.drop_index('idx_user_series_enrollment_series', table_name='user_series_enrollment')
    op.drop_index('idx_user_series_enrollment_current_plan', table_name='user_series_enrollment')
    op.drop_table('user_series_enrollment')

    _drop_legacy_series_plan_order()

    enrollmentsource_enum = sa.Enum(name='enrollmentsource')
    enrollmentsource_enum.drop(op.get_bind(), checkfirst=True)

    seriesstatus_enum = sa.Enum(name='seriesstatus')
    seriesstatus_enum.drop(op.get_bind(), checkfirst=True)
