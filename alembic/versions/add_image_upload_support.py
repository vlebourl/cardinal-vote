"""Add image upload support for vote choices

Revision ID: dashboard_image_002
Revises: dashboard_draft_001
Create Date: 2025-09-18 08:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dashboard_image_002'
down_revision = 'dashboard_draft_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add image upload support to vote_options table."""
    # Add image path field to vote_options table
    op.add_column('vote_options', sa.Column('image_path', sa.String(500), nullable=True))

    # Add constraint to ensure either title/content OR image_path is provided
    op.create_check_constraint(
        'check_choice_content',
        'vote_options',
        '(title IS NOT NULL AND title != \'\') OR (image_path IS NOT NULL AND image_path != \'\')'
    )

    # Add text_content as alias for content field (for clarity)
    op.add_column('vote_options', sa.Column('text_content', sa.Text(), nullable=True))

    # Copy existing content to text_content field
    op.execute("UPDATE vote_options SET text_content = content WHERE content IS NOT NULL")

    # Add index for image path queries
    op.create_index('idx_vote_options_image_path', 'vote_options', ['image_path'])


def downgrade() -> None:
    """Remove image upload support from vote_options table."""
    # Remove index
    op.drop_index('idx_vote_options_image_path', table_name='vote_options')

    # Remove constraint
    op.drop_constraint('check_choice_content', 'vote_options', type_='check')

    # Remove columns
    op.drop_column('vote_options', 'text_content')
    op.drop_column('vote_options', 'image_path')
