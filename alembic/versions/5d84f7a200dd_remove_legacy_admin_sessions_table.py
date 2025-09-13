"""remove_legacy_admin_sessions_table

Revision ID: 5d84f7a200dd
Revises: c97e220ce164
Create Date: 2025-09-13 10:06:01.345591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d84f7a200dd'
down_revision: Union[str, Sequence[str], None] = 'c97e220ce164'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove legacy admin_sessions table.

    This table was used for session-based authentication which has been
    replaced by JWT-based authentication in the generalized platform.
    """
    # Drop admin_sessions table if it exists
    op.execute("DROP TABLE IF EXISTS admin_sessions")


def downgrade() -> None:
    """Recreate admin_sessions table.

    Note: This recreates the table structure only. Any data that existed
    before the upgrade will not be restored.
    """
    # Recreate admin_sessions table structure
    op.create_table(
        'admin_sessions',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
    )
