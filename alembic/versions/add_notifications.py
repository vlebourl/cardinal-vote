"""Add Notifications system for dashboard messaging

Revision ID: dashboard_notifications_008
Revises: dashboard_stats_007
Create Date: 2025-09-18 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dashboard_notifications_008'
down_revision = 'dashboard_stats_007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Notifications system table."""

    # Create notification type enum
    notification_type_enum = postgresql.ENUM(
        'system_announcement', 'vote_created', 'vote_response', 'vote_closed',
        'vote_shared', 'account_update', 'security_alert', 'feature_update',
        'maintenance_notice', 'welcome_message',
        name='notification_type_enum'
    )
    notification_type_enum.create(op.get_bind())

    # Create priority enum
    priority_enum = postgresql.ENUM('low', 'medium', 'high', 'urgent', name='priority_enum')
    priority_enum.create(op.get_bind())

    # Create notifications table
    op.create_table(
        'notifications',
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
            nullable=True,
            comment='NULL for system-wide notifications'
        ),
        sa.Column(
            'notification_type',
            notification_type_enum,
            nullable=False
        ),
        sa.Column(
            'title',
            sa.String(100),
            nullable=False
        ),
        sa.Column(
            'message',
            sa.Text,
            nullable=False
        ),
        sa.Column(
            'priority',
            priority_enum,
            nullable=False,
            server_default='medium'
        ),
        sa.Column(
            'is_read',
            sa.Boolean,
            nullable=False,
            server_default='false'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            'read_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the notification was marked as read'
        ),
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When the notification should be automatically removed'
        ),
        sa.Column(
            'action_url',
            sa.String(500),
            nullable=True,
            comment='Optional URL for notification action'
        ),
        sa.Column(
            'notification_metadata',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='Additional notification data and context'
        )
    )

    # Add constraints
    op.create_check_constraint(
        'check_title_length',
        'notifications',
        'LENGTH(title) >= 1'
    )

    op.create_check_constraint(
        'check_message_length',
        'notifications',
        'LENGTH(message) >= 1'
    )

    op.create_check_constraint(
        'check_expires_future',
        'notifications',
        'expires_at IS NULL OR expires_at > created_at'
    )

    # Add indexes for performance (critical for dashboard notification queries)
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_priority', 'notifications', ['priority'])
    op.create_index('idx_notifications_type', 'notifications', ['notification_type'])
    op.create_index('idx_notifications_expires_at', 'notifications', ['expires_at'])

    # Composite indexes for dashboard queries
    op.create_index('idx_notifications_user_unread', 'notifications', ['user_id', 'is_read', 'created_at'])
    op.create_index('idx_notifications_user_priority', 'notifications', ['user_id', 'priority', 'created_at'])

    # System-wide notifications index (where user_id IS NULL)
    op.execute("CREATE INDEX idx_notifications_system_wide ON notifications (is_read, priority, created_at) WHERE user_id IS NULL")

    # Active notifications index (not expired)
    op.execute("CREATE INDEX idx_notifications_active ON notifications (user_id, is_read, created_at) WHERE expires_at IS NULL OR expires_at > NOW()")

    # Create a welcome notification for existing users
    op.execute("""
        INSERT INTO notifications (user_id, notification_type, title, message, priority, notification_metadata)
        SELECT
            u.id,
            'welcome_message',
            'Welcome to the New Dashboard!',
            'Your Cardinal Vote dashboard has been upgraded with new features including personalized statistics, real-time updates, and improved vote management. Explore the new interface to discover what''s changed.',
            'medium',
            '{"feature": "dashboard_upgrade", "version": "2.0"}'::jsonb
        FROM users u
        WHERE u.is_verified = true
    """)


def downgrade() -> None:
    """Remove Notifications system table."""

    # Remove indexes
    op.execute("DROP INDEX IF EXISTS idx_notifications_active")
    op.execute("DROP INDEX IF EXISTS idx_notifications_system_wide")
    op.drop_index('idx_notifications_user_priority', table_name='notifications')
    op.drop_index('idx_notifications_user_unread', table_name='notifications')
    op.drop_index('idx_notifications_expires_at', table_name='notifications')
    op.drop_index('idx_notifications_type', table_name='notifications')
    op.drop_index('idx_notifications_priority', table_name='notifications')
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')

    # Remove constraints
    op.drop_constraint('check_expires_future', 'notifications', type_='check')
    op.drop_constraint('check_message_length', 'notifications', type_='check')
    op.drop_constraint('check_title_length', 'notifications', type_='check')

    # Drop the table
    op.drop_table('notifications')

    # Drop the enum types
    priority_enum = postgresql.ENUM('low', 'medium', 'high', 'urgent', name='priority_enum')
    priority_enum.drop(op.get_bind())

    notification_type_enum = postgresql.ENUM(
        'system_announcement', 'vote_created', 'vote_response', 'vote_closed',
        'vote_shared', 'account_update', 'security_alert', 'feature_update',
        'maintenance_notice', 'welcome_message',
        name='notification_type_enum'
    )
    notification_type_enum.drop(op.get_bind())
