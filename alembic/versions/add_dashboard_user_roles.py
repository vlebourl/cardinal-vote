"""Add user roles and preferences for unified dashboard system

Revision ID: dashboard_roles_004
Revises: dashboard_activity_003
Create Date: 2025-09-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dashboard_roles_004'
down_revision = 'dashboard_activity_003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add role and preferences fields to users table for dashboard system."""

    # Add role enum field (with user/super_admin options)
    # First create the enum type
    role_enum = postgresql.ENUM('user', 'super_admin', name='user_role_enum')
    role_enum.create(op.get_bind())

    # Add role column with default 'user'
    op.add_column('users', sa.Column('role', role_enum, nullable=False, server_default='user'))

    # Add preferences JSON field for dashboard configuration
    op.add_column('users', sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Update existing super admins (those with is_super_admin = true) to have role = 'super_admin'
    op.execute("""
        UPDATE users
        SET role = 'super_admin'
        WHERE is_super_admin = true
    """)

    # Add index for role-based queries (critical for dashboard performance)
    op.create_index('idx_users_role', 'users', ['role'])

    # Add compound index for role and active status queries
    op.create_index('idx_users_role_active', 'users', ['role', 'is_verified'])

    # Set default preferences for existing users
    op.execute("""
        UPDATE users
        SET preferences = '{
            "theme": "light",
            "notifications_enabled": true,
            "dashboard_layout": "default",
            "items_per_page": 20
        }'::jsonb
        WHERE preferences IS NULL
    """)


def downgrade() -> None:
    """Remove role and preferences fields from users table."""

    # Remove indexes
    op.drop_index('idx_users_role_active', table_name='users')
    op.drop_index('idx_users_role', table_name='users')

    # Remove columns
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'role')

    # Drop the enum type
    role_enum = postgresql.ENUM('user', 'super_admin', name='user_role_enum')
    role_enum.drop(op.get_bind())
