"""Integration tests for vote moderation functionality with real database."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from cardinal_vote.models import (
    Base,
    User,
    Vote,
    VoteOption,
)
from cardinal_vote.vote_moderation_manager import VoteModerationManager

# Test database setup - Use SQLite for CI compatibility
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_moderation.db"


@pytest.fixture
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def async_session_maker(async_engine):
    """Create async session maker for tests."""
    return async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def async_session(async_session_maker):
    """Create test database session."""
    async with async_session_maker() as session:
        yield session


@pytest.mark.asyncio
class TestVoteModerationIntegration:
    """Integration tests with real database operations."""

    async def test_full_moderation_workflow(self, async_session, test_user):
        """Test complete moderation workflow from flag creation to resolution."""
        # Create a vote
        vote = Vote(
            title="Test Vote for Moderation",
            slug="test-vote-moderation",
            description="Vote to be moderated",
            creator_id=test_user.id,
            status="active",
            created_at=datetime.now(UTC),
        )
        async_session.add(vote)

        # Add vote options
        option1 = VoteOption(
            vote_id=vote.id,
            name="Option 1",
            image_path="option1.jpg",
            created_at=datetime.now(UTC),
        )
        option2 = VoteOption(
            vote_id=vote.id,
            name="Option 2",
            image_path="option2.jpg",
            created_at=datetime.now(UTC),
        )
        async_session.add(option1)
        async_session.add(option2)
        await async_session.commit()

        # Initialize moderation manager
        manager = VoteModerationManager()

        # 1. Create a flag
        flag_result = await manager.create_vote_flag(
            session=async_session,
            vote_id=vote.id,
            flag_type="inappropriate_content",
            reason="Contains offensive content",
            flagger_id=test_user.id,
        )
        assert flag_result["success"] is True
        flag_id = flag_result["flag_id"]

        # Verify flag was created in database
        await async_session.refresh(vote)
        flags = await async_session.execute(
            text("SELECT * FROM vote_moderation_flags WHERE vote_id = :vote_id"),
            {"vote_id": str(vote.id)},
        )
        flag_rows = flags.fetchall()
        assert len(flag_rows) == 1
        assert flag_rows[0].flag_type == "inappropriate_content"
        assert flag_rows[0].status == "pending"

        # 2. Review the flag
        review_result = await manager.review_vote_flag(
            session=async_session,
            flag_id=flag_id,
            status="approved",
            reviewer_id=test_user.id,
            review_notes="Flag approved, content is inappropriate",
        )
        assert review_result["success"] is True

        # 3. Take moderation action
        action_result = await manager.take_moderation_action(
            session=async_session,
            vote_id=vote.id,
            action="hide",
            moderator_id=test_user.id,
            reason="Hidden due to inappropriate content",
        )
        assert action_result["success"] is True

        # Verify vote status was changed
        await async_session.refresh(vote)
        assert vote.status == "hidden"

        # Verify moderation action was logged
        actions = await async_session.execute(
            text("SELECT * FROM vote_moderation_actions WHERE vote_id = :vote_id"),
            {"vote_id": str(vote.id)},
        )
        action_rows = actions.fetchall()
        assert len(action_rows) == 1
        assert action_rows[0].action == "hide"
        assert action_rows[0].moderator_id == test_user.id

        # 4. Test dashboard stats include our data
        stats = await manager.get_moderation_dashboard_stats(async_session)
        assert "pending_flags" in stats
        assert "recent_flags" in stats
        assert stats["pending_flags"] == 0  # Flag was reviewed
        assert "total_moderated_votes" in stats

    async def test_batch_query_performance(self, async_session, test_user):
        """Test that batch queries work correctly with multiple votes."""
        # Create multiple votes with flags
        votes = []
        for i in range(5):
            vote = Vote(
                title=f"Test Vote {i}",
                slug=f"test-vote-{i}",
                description=f"Vote {i} description",
                creator_id=test_user.id,
                status="active",
                created_at=datetime.now(UTC),
            )
            async_session.add(vote)
            votes.append(vote)

        await async_session.flush()  # Get IDs

        # Create flags for each vote
        manager = VoteModerationManager()
        for vote in votes:
            await manager.create_vote_flag(
                session=async_session,
                vote_id=vote.id,
                flag_type="spam",
                reason=f"Spam vote {vote.title}",
                flagger_id=test_user.id,
            )

        await async_session.commit()

        # Test get_flagged_votes uses batch queries efficiently
        flagged_votes = await manager.get_flagged_votes(
            session=async_session, limit=10, offset=0
        )

        assert len(flagged_votes) == 5
        for vote_data in flagged_votes:
            assert "flag_counts" in vote_data
            assert "total_flags" in vote_data
            assert vote_data["total_flags"] == 1
            assert vote_data["flag_counts"]["pending"] == 1

    async def test_bulk_moderation_actions(self, async_session, test_user):
        """Test bulk moderation actions work with real database."""
        # Create multiple votes
        vote_ids = []
        for i in range(3):
            vote = Vote(
                title=f"Bulk Test Vote {i}",
                slug=f"bulk-test-vote-{i}",
                description=f"Vote {i} for bulk testing",
                creator_id=test_user.id,
                status="active",
                created_at=datetime.now(UTC),
            )
            async_session.add(vote)
            await async_session.flush()
            vote_ids.append(vote.id)

        await async_session.commit()

        # Execute bulk action
        manager = VoteModerationManager()
        result = await manager.bulk_moderation_action(
            session=async_session,
            vote_ids=vote_ids,
            action="disable",
            moderator_id=test_user.id,
            reason="Bulk disable for testing",
        )

        assert result["success"] is True
        assert result["processed_count"] == 3
        assert result["failed_count"] == 0

        # Verify all votes were disabled
        for vote_id in vote_ids:
            vote_result = await async_session.execute(
                text("SELECT status FROM votes WHERE id = :vote_id"),
                {"vote_id": str(vote_id)},
            )
            vote_row = vote_result.fetchone()
            assert vote_row.status == "disabled"

        # Verify moderation actions were logged
        actions = await async_session.execute(
            text(
                "SELECT COUNT(*) as count FROM vote_moderation_actions WHERE action = 'disable'"
            )
        )
        action_count = actions.fetchone()
        assert action_count.count == 3

    async def test_duplicate_flag_prevention(self, async_session, test_user):
        """Test that duplicate flags are prevented."""
        # Create a vote
        vote = Vote(
            title="Test Vote for Duplicate Flag",
            slug="test-vote-duplicate-flag",
            description="Vote to test duplicate flagging",
            creator_id=test_user.id,
            status="active",
            created_at=datetime.now(UTC),
        )
        async_session.add(vote)
        await async_session.commit()

        manager = VoteModerationManager()

        # Create first flag
        result1 = await manager.create_vote_flag(
            session=async_session,
            vote_id=vote.id,
            flag_type="inappropriate_content",
            reason="First flag",
            flagger_id=test_user.id,
        )
        assert result1["success"] is True

        # Try to create duplicate flag
        result2 = await manager.create_vote_flag(
            session=async_session,
            vote_id=vote.id,
            flag_type="inappropriate_content",
            reason="Duplicate flag attempt",
            flagger_id=test_user.id,
        )
        assert result2["success"] is False
        assert "already flagged" in result2["message"].lower()

        # Verify only one flag exists
        flags = await async_session.execute(
            text(
                "SELECT COUNT(*) as count FROM vote_moderation_flags WHERE vote_id = :vote_id"
            ),
            {"vote_id": str(vote.id)},
        )
        flag_count = flags.fetchone()
        assert flag_count.count == 1

    async def test_vote_restoration_workflow(self, async_session, test_user):
        """Test vote hide/restore workflow maintains proper state."""
        # Create and hide a vote
        vote = Vote(
            title="Test Vote for Restoration",
            slug="test-vote-restoration",
            description="Vote to test restoration",
            creator_id=test_user.id,
            status="active",
            created_at=datetime.now(UTC),
        )
        async_session.add(vote)
        await async_session.commit()

        manager = VoteModerationManager()

        # Hide the vote
        hide_result = await manager.take_moderation_action(
            session=async_session,
            vote_id=vote.id,
            action="hide",
            moderator_id=test_user.id,
            reason="Hiding for test",
        )
        assert hide_result["success"] is True

        await async_session.refresh(vote)
        assert vote.status == "hidden"

        # Restore the vote
        restore_result = await manager.take_moderation_action(
            session=async_session,
            vote_id=vote.id,
            action="restore",
            moderator_id=test_user.id,
            reason="Restoring after review",
        )
        assert restore_result["success"] is True

        await async_session.refresh(vote)
        # After restore, vote should be active again
        assert vote.status == "active"

        # Verify both actions were logged
        actions = await async_session.execute(
            text(
                "SELECT COUNT(*) as count FROM vote_moderation_actions WHERE vote_id = :vote_id"
            ),
            {"vote_id": str(vote.id)},
        )
        action_count = actions.fetchone()
        assert action_count.count == 2

    async def test_flag_pagination_and_filtering(self, async_session, test_user):
        """Test flag retrieval with pagination and status filtering."""
        # Create votes with different flag statuses
        votes = []
        for i in range(5):
            vote = Vote(
                title=f"Flag Filter Test Vote {i}",
                slug=f"flag-filter-test-vote-{i}",
                description=f"Vote {i} for flag filtering",
                creator_id=test_user.id,
                status="active",
                created_at=datetime.now(UTC),
            )
            async_session.add(vote)
            votes.append(vote)

        await async_session.flush()

        manager = VoteModerationManager()

        # Create flags with different statuses
        flag_ids = []
        for i, vote in enumerate(votes):
            result = await manager.create_vote_flag(
                session=async_session,
                vote_id=vote.id,
                flag_type="spam",
                reason=f"Flag for vote {i}",
                flagger_id=test_user.id,
            )
            flag_ids.append(result["flag_id"])

        # Review some flags as approved, others remain pending
        for i in range(2):
            await manager.review_vote_flag(
                session=async_session,
                flag_id=flag_ids[i],
                status="approved",
                reviewer_id=test_user.id,
                review_notes=f"Approved flag {i}",
            )

        await async_session.commit()

        # Test pending flags retrieval
        pending_flags = await manager.get_pending_flags(
            session=async_session, limit=10, offset=0
        )
        assert len(pending_flags) == 3  # 3 remain pending

        # Test flagged votes filtering by status
        flagged_votes_pending = await manager.get_flagged_votes(
            session=async_session, limit=10, offset=0, flag_status="pending"
        )
        assert len(flagged_votes_pending) == 3

        flagged_votes_approved = await manager.get_flagged_votes(
            session=async_session, limit=10, offset=0, flag_status="approved"
        )
        assert len(flagged_votes_approved) == 2


@pytest.fixture
async def test_user(async_session):
    """Create a test user for moderation tests."""
    user = User(
        email="moderator@test.com",
        username="moderator",
        first_name="Test",
        last_name="Moderator",
        role="super_admin",
        is_active=True,
        created_at=datetime.now(UTC),
    )
    async_session.add(user)
    await async_session.commit()
    return user
