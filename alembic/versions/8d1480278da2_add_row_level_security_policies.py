"""Add Row-Level Security policies

Revision ID: 8d1480278da2
Revises: b9061c1f6adb
Create Date: 2025-09-07 12:27:09.928481

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d1480278da2"
down_revision: str | Sequence[str] | None = "b9061c1f6adb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable Row-Level Security on generalized platform tables
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE generalized_votes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE vote_options ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE voter_responses ENABLE ROW LEVEL SECURITY;")

    # Users table RLS policies
    # Users can view and update their own profile
    op.execute("""
        CREATE POLICY user_own_profile ON users
        FOR ALL
        USING (id = current_user_id() OR is_super_admin());
    """)

    # Super admins can view all users
    op.execute("""
        CREATE POLICY admin_view_all_users ON users
        FOR SELECT
        USING (is_super_admin());
    """)

    # Generalized votes table RLS policies
    # Users can view and manage their own votes
    op.execute("""
        CREATE POLICY user_own_votes ON generalized_votes
        FOR ALL
        USING (creator_id = current_user_id() OR is_super_admin());
    """)

    # Public can view active votes (for voting)
    op.execute("""
        CREATE POLICY public_view_active_votes ON generalized_votes
        FOR SELECT
        USING (status = 'active');
    """)

    # Vote options table RLS policies
    # Users can manage options for their own votes
    op.execute("""
        CREATE POLICY user_own_vote_options ON vote_options
        FOR ALL
        USING (
            vote_id IN (
                SELECT id FROM generalized_votes
                WHERE creator_id = current_user_id()
            ) OR is_super_admin()
        );
    """)

    # Public can view options for active votes
    op.execute("""
        CREATE POLICY public_view_active_vote_options ON vote_options
        FOR SELECT
        USING (
            vote_id IN (
                SELECT id FROM generalized_votes
                WHERE status = 'active'
            )
        );
    """)

    # Voter responses table RLS policies
    # Vote creators can view all responses to their votes
    op.execute("""
        CREATE POLICY creator_view_vote_responses ON voter_responses
        FOR SELECT
        USING (
            vote_id IN (
                SELECT id FROM generalized_votes
                WHERE creator_id = current_user_id()
            ) OR is_super_admin()
        );
    """)

    # Voters can insert responses to active votes
    op.execute("""
        CREATE POLICY public_insert_vote_responses ON voter_responses
        FOR INSERT
        WITH CHECK (
            vote_id IN (
                SELECT id FROM generalized_votes
                WHERE status = 'active'
            )
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS user_own_profile ON users;")
    op.execute("DROP POLICY IF EXISTS admin_view_all_users ON users;")
    op.execute("DROP POLICY IF EXISTS user_own_votes ON generalized_votes;")
    op.execute("DROP POLICY IF EXISTS public_view_active_votes ON generalized_votes;")
    op.execute("DROP POLICY IF EXISTS user_own_vote_options ON vote_options;")
    op.execute("DROP POLICY IF EXISTS public_view_active_vote_options ON vote_options;")
    op.execute("DROP POLICY IF EXISTS creator_view_vote_responses ON voter_responses;")
    op.execute("DROP POLICY IF EXISTS public_insert_vote_responses ON voter_responses;")

    # Disable Row-Level Security on generalized platform tables
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE generalized_votes DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE vote_options DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE voter_responses DISABLE ROW LEVEL SECURITY;")
