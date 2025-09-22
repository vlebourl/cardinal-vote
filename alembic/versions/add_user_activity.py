"""Add UserActivity tracking table for dashboard analytics

Revision ID: dashboard_activity_006
Revises: dashboard_config_005
Create Date: 2025-09-18 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dashboard_activity_006'
down_revision = 'dashboard_config_005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create UserActivity tracking table."""

    # First create the activity type enum
    activity_type_enum = postgresql.ENUM(
        'login', 'logout', 'vote_created', 'vote_participated', 'vote_modified',
        'vote_closed', 'vote_shared', 'dashboard_viewed', 'profile_updated',
        'preferences_updated',
        name='activity_type_enum'
    )
    activity_type_enum.create(op.get_bind())

    # Create user_activities table
    op.create_table(
        'user_activities',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            nullable=False
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'activity_type',
            activity_type_enum,
            nullable=False
        ),
        sa.Column(
            'entity_type',
            sa.String(50),
            nullable=True,
            comment='Type of related entity (vote, user, etc.)'
        ),
        sa.Column(
            'entity_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='ID of related entity'
        ),
        sa.Column(
            'activity_data',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Additional activity details in JSON format'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            'ip_address',
            postgresql.INET,
            nullable=True,
            comment='Client IP address'
        ),
        sa.Column(
            'user_agent',
            sa.Text,
            nullable=True,
            comment='Browser user agent string'
        )
    )

    # Add constraints
    op.create_check_constraint(
        'check_entity_consistency',
        'user_activities',
        '(entity_type IS NULL AND entity_id IS NULL) OR (entity_type IS NOT NULL AND entity_id IS NOT NULL)'
    )

    # Add indexes for performance (critical for dashboard analytics)
    op.create_index('idx_user_activities_user_id', 'user_activities', ['user_id'])
    op.create_index('idx_user_activities_created_at', 'user_activities', ['created_at'])
    op.create_index('idx_user_activities_user_time', 'user_activities', ['user_id', 'created_at'])
    op.create_index('idx_user_activities_activity_type', 'user_activities', ['activity_type'])
    op.create_index('idx_user_activities_entity', 'user_activities', ['entity_type', 'entity_id'])

    # Index for dashboard analytics queries (recent activity, user engagement)
    op.create_index('idx_user_activities_dashboard', 'user_activities', ['user_id', 'activity_type', 'created_at'])

    # Partial index for login activities (commonly queried)
    op.execute("CREATE INDEX idx_user_activities_logins ON user_activities (user_id, created_at) WHERE activity_type = 'login'")


def downgrade() -> None:
    """Remove UserActivity tracking table."""

    # Remove indexes
    op.execute("DROP INDEX IF EXISTS idx_user_activities_logins")
    op.drop_index('idx_user_activities_dashboard', table_name='user_activities')
    op.drop_index('idx_user_activities_entity', table_name='user_activities')
    op.drop_index('idx_user_activities_activity_type', table_name='user_activities')
    op.drop_index('idx_user_activities_user_time', table_name='user_activities')
    op.drop_index('idx_user_activities_created_at', table_name='user_activities')
    op.drop_index('idx_user_activities_user_id', table_name='user_activities')

    # Remove constraint
    op.drop_constraint('check_entity_consistency', 'user_activities', type_='check')

    # Drop the table
    op.drop_table('user_activities')

    # Drop the enum type
    activity_type_enum = postgresql.ENUM(
        'login', 'logout', 'vote_created', 'vote_participated', 'vote_modified',
        'vote_closed', 'vote_shared', 'dashboard_viewed', 'profile_updated',
        'preferences_updated',
        name='activity_type_enum'
    )
    activity_type_enum.drop(op.get_bind())
