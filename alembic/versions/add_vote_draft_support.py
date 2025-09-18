"""Add vote draft support for dashboard functionality

Revision ID: dashboard_draft_001
Revises: base
Create Date: 2025-09-18 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dashboard_draft_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add draft support fields to votes table."""
    # Add draft-specific fields to generalized_votes table
    op.add_column('generalized_votes', sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('generalized_votes', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('generalized_votes', sa.Column('published_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('generalized_votes', sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('generalized_votes', sa.Column('draft_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('generalized_votes', sa.Column('choice_count', sa.Integer(), nullable=False, server_default='0'))

    # Add indexes for performance
    op.create_index('idx_votes_draft_status', 'generalized_votes', ['is_draft', 'is_active'])
    op.create_index('idx_votes_creator_status', 'generalized_votes', ['creator_id', 'is_draft', 'is_active'])
    op.create_index('idx_votes_draft_expires', 'generalized_votes', ['draft_expires_at'])

    # Update existing votes to have proper draft status
    # Set existing votes as published (is_draft=false, is_active based on status)
    op.execute("""
        UPDATE generalized_votes
        SET is_draft = false,
            is_active = CASE WHEN status = 'active' THEN true ELSE false END,
            published_at = created_at,
            closed_at = CASE WHEN status = 'closed' THEN updated_at ELSE NULL END
        WHERE status != 'draft'
    """)


def downgrade() -> None:
    """Remove draft support fields from votes table."""
    # Remove indexes
    op.drop_index('idx_votes_draft_expires', table_name='generalized_votes')
    op.drop_index('idx_votes_creator_status', table_name='generalized_votes')
    op.drop_index('idx_votes_draft_status', table_name='generalized_votes')

    # Remove columns
    op.drop_column('generalized_votes', 'choice_count')
    op.drop_column('generalized_votes', 'draft_expires_at')
    op.drop_column('generalized_votes', 'closed_at')
    op.drop_column('generalized_votes', 'published_at')
    op.drop_column('generalized_votes', 'is_active')
    op.drop_column('generalized_votes', 'is_draft')
