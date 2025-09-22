"""Add Statistics aggregation table for dashboard metrics

Revision ID: dashboard_stats_007
Revises: dashboard_activity_006
Create Date: 2025-09-18 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dashboard_stats_007'
down_revision = 'dashboard_activity_006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Statistics aggregation table."""

    # Create the metric type enum
    metric_type_enum = postgresql.ENUM(
        'votes_created', 'votes_participated', 'votes_closed', 'responses_received',
        'user_logins', 'dashboard_views', 'vote_shares', 'avg_response_time',
        'system_total_users', 'system_total_votes', 'system_total_responses',
        'system_active_votes', 'user_engagement_score',
        name='metric_type_enum'
    )
    metric_type_enum.create(op.get_bind())

    # Create the time period enum
    time_period_enum = postgresql.ENUM(
        'daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'all_time',
        name='time_period_enum'
    )
    time_period_enum.create(op.get_bind())

    # Create statistics table
    op.create_table(
        'statistics',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column(
            'metric_type',
            metric_type_enum,
            nullable=False
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=True,
            comment='NULL for system-wide statistics'
        ),
        sa.Column(
            'time_period',
            time_period_enum,
            nullable=False
        ),
        sa.Column(
            'period_start',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='Start of the measurement period'
        ),
        sa.Column(
            'period_end',
            sa.DateTime(timezone=True),
            nullable=False,
            comment='End of the measurement period'
        ),
        sa.Column(
            'metric_value',
            sa.Numeric(precision=15, scale=4),
            nullable=False,
            comment='The calculated metric value'
        ),
        sa.Column(
            'additional_data',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Additional breakdown and metadata'
        ),
        sa.Column(
            'calculated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            'is_current',
            sa.Boolean,
            nullable=False,
            server_default='true',
            comment='Whether this is the latest calculation for this metric/period'
        )
    )

    # Add constraints
    op.create_check_constraint(
        'check_period_order',
        'statistics',
        'period_start <= period_end'
    )

    # Unique constraint: only one current statistic per combination
    op.create_unique_constraint(
        'unique_current_statistic',
        'statistics',
        ['metric_type', 'user_id', 'time_period', 'period_start', 'is_current'],
        postgresql_where=sa.text('is_current = true')
    )

    # Add indexes for performance
    op.create_index('idx_statistics_metric_type', 'statistics', ['metric_type'])
    op.create_index('idx_statistics_user_id', 'statistics', ['user_id'])
    op.create_index('idx_statistics_time_period', 'statistics', ['time_period'])
    op.create_index('idx_statistics_calculated_at', 'statistics', ['calculated_at'])
    op.create_index('idx_statistics_is_current', 'statistics', ['is_current'])

    # Composite indexes for dashboard queries
    op.create_index('idx_statistics_user_current', 'statistics', ['user_id', 'is_current'])
    op.create_index('idx_statistics_metric_user_current', 'statistics', ['metric_type', 'user_id', 'is_current'])
    op.create_index('idx_statistics_period_range', 'statistics', ['time_period', 'period_start', 'period_end'])

    # System-wide statistics index (where user_id IS NULL)
    op.execute("CREATE INDEX idx_statistics_system_wide ON statistics (metric_type, time_period, is_current) WHERE user_id IS NULL")


def downgrade() -> None:
    """Remove Statistics aggregation table."""

    # Remove indexes
    op.execute("DROP INDEX IF EXISTS idx_statistics_system_wide")
    op.drop_index('idx_statistics_period_range', table_name='statistics')
    op.drop_index('idx_statistics_metric_user_current', table_name='statistics')
    op.drop_index('idx_statistics_user_current', table_name='statistics')
    op.drop_index('idx_statistics_is_current', table_name='statistics')
    op.drop_index('idx_statistics_calculated_at', table_name='statistics')
    op.drop_index('idx_statistics_time_period', table_name='statistics')
    op.drop_index('idx_statistics_user_id', table_name='statistics')
    op.drop_index('idx_statistics_metric_type', table_name='statistics')

    # Remove constraints
    op.drop_constraint('unique_current_statistic', 'statistics', type_='unique')
    op.drop_constraint('check_period_order', 'statistics', type_='check')

    # Drop the table
    op.drop_table('statistics')

    # Drop the enum types
    time_period_enum = postgresql.ENUM(
        'daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'all_time',
        name='time_period_enum'
    )
    time_period_enum.drop(op.get_bind())

    metric_type_enum = postgresql.ENUM(
        'votes_created', 'votes_participated', 'votes_closed', 'responses_received',
        'user_logins', 'dashboard_views', 'vote_shares', 'avg_response_time',
        'system_total_users', 'system_total_votes', 'system_total_responses',
        'system_active_votes', 'user_engagement_score',
        name='metric_type_enum'
    )
    metric_type_enum.drop(op.get_bind())
