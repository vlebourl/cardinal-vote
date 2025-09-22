"""Add Dashboard configuration table for user dashboard settings

Revision ID: dashboard_config_005
Revises: dashboard_roles_004
Create Date: 2025-09-18 12:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dashboard_config_005'
down_revision = 'dashboard_roles_004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Dashboard configuration table."""

    # Create dashboards table
    op.create_table(
        'dashboards',
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
            nullable=False,
            unique=True  # One dashboard config per user
        ),
        sa.Column(
            'layout_config',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='JSON configuration for widget placement and layout'
        ),
        sa.Column(
            'theme_preference',
            sa.String(20),
            nullable=False,
            server_default='light'
        ),
        sa.Column(
            'notification_settings',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='JSON for notification preferences'
        ),
        sa.Column(
            'last_accessed',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp of last dashboard view'
        ),
        sa.Column(
            'widget_states',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment='JSON for expanded/collapsed widget states'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        )
    )

    # Add constraint for theme preference values
    op.create_check_constraint(
        'check_theme_preference',
        'dashboards',
        "theme_preference IN ('light', 'dark', 'auto')"
    )

    # Add indexes for performance
    op.create_index('idx_dashboards_user_id', 'dashboards', ['user_id'])
    op.create_index('idx_dashboards_last_accessed', 'dashboards', ['last_accessed'])
    op.create_index('idx_dashboards_theme', 'dashboards', ['theme_preference'])

    # Create default dashboard configurations for existing users
    op.execute("""
        INSERT INTO dashboards (user_id, layout_config, theme_preference, notification_settings, widget_states)
        SELECT
            id,
            '{
                "layout": "default",
                "widgets": [
                    {"type": "my_votes", "position": 1, "expanded": true},
                    {"type": "available_votes", "position": 2, "expanded": true},
                    {"type": "statistics", "position": 3, "expanded": false}
                ]
            }'::jsonb,
            'light',
            '{
                "email_notifications": true,
                "browser_notifications": true,
                "vote_updates": true,
                "new_votes": true,
                "vote_closed": true
            }'::jsonb,
            '{
                "my_votes": {"expanded": true},
                "available_votes": {"expanded": true},
                "statistics": {"expanded": false},
                "recent_activity": {"expanded": false}
            }'::jsonb
        FROM users
        WHERE NOT EXISTS (SELECT 1 FROM dashboards WHERE dashboards.user_id = users.id)
    """)


def downgrade() -> None:
    """Remove Dashboard configuration table."""

    # Remove indexes
    op.drop_index('idx_dashboards_theme', table_name='dashboards')
    op.drop_index('idx_dashboards_last_accessed', table_name='dashboards')
    op.drop_index('idx_dashboards_user_id', table_name='dashboards')

    # Remove constraint
    op.drop_constraint('check_theme_preference', 'dashboards', type_='check')

    # Drop the table
    op.drop_table('dashboards')
