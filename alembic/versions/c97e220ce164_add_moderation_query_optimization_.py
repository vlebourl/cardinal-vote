"""add_moderation_query_optimization_indexes

Revision ID: c97e220ce164
Revises: bff158c3e8a6
Create Date: 2025-09-09 19:22:41.392822

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c97e220ce164"
down_revision: str | Sequence[str] | None = "bff158c3e8a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add composite indexes for common query patterns as suggested in code review

    # Composite index for flag queries by vote_id and status
    op.create_index(
        "idx_flags_vote_status", "vote_moderation_flags", ["vote_id", "status"]
    )

    # Composite index for moderation actions by moderator and date
    op.create_index(
        "idx_actions_moderator_date",
        "vote_moderation_actions",
        ["moderator_id", "created_at"],
    )

    # Index for flag queries by flagger and creation date
    op.create_index(
        "idx_flags_flagger_date", "vote_moderation_flags", ["flagger_id", "created_at"]
    )

    # Index for actions by vote and date (for vote history)
    op.create_index(
        "idx_actions_vote_date", "vote_moderation_actions", ["vote_id", "created_at"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the optimization indexes
    op.drop_index("idx_actions_vote_date", table_name="vote_moderation_actions")
    op.drop_index("idx_flags_flagger_date", table_name="vote_moderation_flags")
    op.drop_index("idx_actions_moderator_date", table_name="vote_moderation_actions")
    op.drop_index("idx_flags_vote_status", table_name="vote_moderation_flags")
