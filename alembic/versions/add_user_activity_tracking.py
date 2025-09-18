"""Add user activity tracking for dashboard features

Revision ID: dashboard_activity_003
Revises: dashboard_image_002
Create Date: 2025-09-18 08:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dashboard_activity_003'
down_revision = 'dashboard_image_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user activity tracking fields."""
    # The last_login field already exists in the User model, but let's ensure it's there
    # and add any additional activity tracking we might need

    # Add index for last_login queries (for dashboard statistics)
    op.create_index('idx_users_last_login', 'users', ['last_login'])

    # Add indexes for dashboard query performance
    op.create_index('idx_voter_responses_vote_submitted', 'voter_responses', ['vote_id', 'submitted_at'])
    op.create_index('idx_voter_responses_user_activity', 'voter_responses', ['user_id', 'submitted_at'])


def downgrade() -> None:
    """Remove user activity tracking enhancements."""
    # Remove indexes
    op.drop_index('idx_voter_responses_user_activity', table_name='voter_responses')
    op.drop_index('idx_voter_responses_vote_submitted', table_name='voter_responses')
    op.drop_index('idx_users_last_login', table_name='users')
