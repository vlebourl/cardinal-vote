"""Tests for VoteModerationManager business logic."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from cardinal_vote.models import User, Vote, VoteModerationFlag
from cardinal_vote.vote_moderation_manager import VoteModerationManager


@pytest.fixture
async def moderation_manager():
    """Create VoteModerationManager instance for testing."""
    return VoteModerationManager()


@pytest.fixture
async def mock_session():
    """Create mock async session for testing."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.add = AsyncMock()
    return session


@pytest.fixture
def sample_vote():
    """Create sample vote for testing."""
    return Vote(
        id=uuid4(),
        title="Test Vote",
        description="Test vote description",
        slug="test-vote",
        status="active",
        creator_id=uuid4(),
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_verified=True,
        is_super_admin=False,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_super_admin():
    """Create sample super admin for testing."""
    return User(
        id=uuid4(),
        email="admin@example.com",
        first_name="Super",
        last_name="Admin",
        is_verified=True,
        is_super_admin=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_flag(sample_vote, sample_user):
    """Create sample moderation flag for testing."""
    return VoteModerationFlag(
        id=uuid4(),
        vote_id=sample_vote.id,
        flagger_id=sample_user.id,
        flag_type="inappropriate_content",
        reason="This content violates community standards",
        status="pending",
        created_at=datetime.utcnow(),
    )


class TestCreateVoteFlag:
    """Test create_vote_flag functionality."""

    async def test_create_vote_flag_success(
        self, moderation_manager, mock_session, sample_vote, sample_user
    ):
        """Test successful flag creation."""
        # Mock vote exists
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote
        mock_session.execute.side_effect = [vote_result, Mock()]

        # Mock no existing flag
        existing_flag_result = Mock()
        existing_flag_result.scalar_one_or_none.return_value = None
        mock_session.execute.side_effect = [vote_result, existing_flag_result]

        result = await moderation_manager.create_vote_flag(
            mock_session,
            sample_vote.id,
            "inappropriate_content",
            "Test reason",
            sample_user.id,
        )

        assert result["success"] is True
        assert "flag_id" in result
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_create_vote_flag_nonexistent_vote(
        self, moderation_manager, mock_session, sample_user
    ):
        """Test flag creation for non-existent vote."""
        # Mock vote doesn't exist
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.create_vote_flag(
            mock_session,
            uuid4(),
            "inappropriate_content",
            "Test reason",
            sample_user.id,
        )

        assert result["success"] is False
        assert result["message"] == "Vote not found"
        mock_session.add.assert_not_called()

    async def test_create_vote_flag_duplicate(
        self, moderation_manager, mock_session, sample_vote, sample_user, sample_flag
    ):
        """Test duplicate flag prevention."""
        # Mock vote exists
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote

        # Mock existing flag
        existing_flag_result = Mock()
        existing_flag_result.scalar_one_or_none.return_value = sample_flag
        mock_session.execute.side_effect = [vote_result, existing_flag_result]

        result = await moderation_manager.create_vote_flag(
            mock_session,
            sample_vote.id,
            "inappropriate_content",
            "Test reason",
            sample_user.id,
        )

        assert result["success"] is False
        assert "already flagged" in result["message"]
        mock_session.add.assert_not_called()

    async def test_create_vote_flag_anonymous(
        self, moderation_manager, mock_session, sample_vote
    ):
        """Test anonymous flag creation."""
        # Mock vote exists
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.create_vote_flag(
            mock_session,
            sample_vote.id,
            "spam",
            "This is spam content",
            None,  # Anonymous flag
        )

        assert result["success"] is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()


class TestReviewVoteFlag:
    """Test review_vote_flag functionality."""

    async def test_review_flag_success(
        self, moderation_manager, mock_session, sample_flag, sample_super_admin
    ):
        """Test successful flag review."""
        # Mock flag exists
        flag_result = Mock()
        flag_result.scalar_one_or_none.return_value = sample_flag
        mock_session.execute.return_value = flag_result

        result = await moderation_manager.review_vote_flag(
            mock_session,
            sample_flag.id,
            sample_super_admin.id,
            "approved",
            "Flag reviewed and approved",
        )

        assert result["success"] is True
        assert result["flag_id"] == str(sample_flag.id)
        mock_session.commit.assert_called_once()

    async def test_review_flag_not_found(
        self, moderation_manager, mock_session, sample_super_admin
    ):
        """Test review of non-existent flag."""
        # Mock flag doesn't exist
        flag_result = Mock()
        flag_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = flag_result

        result = await moderation_manager.review_vote_flag(
            mock_session, uuid4(), sample_super_admin.id, "approved", "Review notes"
        )

        assert result["success"] is False
        assert result["message"] == "Flag not found"

    async def test_review_flag_already_reviewed(
        self, moderation_manager, mock_session, sample_flag, sample_super_admin
    ):
        """Test review of already reviewed flag."""
        # Set flag as already reviewed
        sample_flag.status = "approved"

        # Mock flag exists but already reviewed
        flag_result = Mock()
        flag_result.scalar_one_or_none.return_value = sample_flag
        mock_session.execute.return_value = flag_result

        result = await moderation_manager.review_vote_flag(
            mock_session,
            sample_flag.id,
            sample_super_admin.id,
            "rejected",
            "Review notes",
        )

        assert result["success"] is False
        assert "already been reviewed" in result["message"]


class TestTakeModerationAction:
    """Test take_moderation_action functionality."""

    async def test_close_vote_success(
        self, moderation_manager, mock_session, sample_vote, sample_super_admin
    ):
        """Test successful vote closing."""
        # Mock vote exists and is active
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.take_moderation_action(
            mock_session,
            sample_vote.id,
            sample_super_admin.id,
            "close_vote",
            "Vote closing due to completion",
        )

        assert result["success"] is True
        assert result["new_status"] == "closed"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_disable_vote_success(
        self, moderation_manager, mock_session, sample_vote, sample_super_admin
    ):
        """Test successful vote disabling."""
        # Mock vote exists
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.take_moderation_action(
            mock_session,
            sample_vote.id,
            sample_super_admin.id,
            "disable_vote",
            "Vote disabled due to policy violation",
        )

        assert result["success"] is True
        assert result["new_status"] == "disabled"

    async def test_hide_vote_success(
        self, moderation_manager, mock_session, sample_vote, sample_super_admin
    ):
        """Test successful vote hiding."""
        # Mock vote exists
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.take_moderation_action(
            mock_session,
            sample_vote.id,
            sample_super_admin.id,
            "hide_vote",
            "Vote hidden due to inappropriate content",
        )

        assert result["success"] is True
        assert result["new_status"] == "hidden"

    async def test_restore_vote_success(
        self, moderation_manager, mock_session, sample_vote, sample_super_admin
    ):
        """Test successful vote restoration."""
        # Set vote as disabled
        sample_vote.status = "disabled"

        # Mock vote exists
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.take_moderation_action(
            mock_session,
            sample_vote.id,
            sample_super_admin.id,
            "restore_vote",
            "Vote restored after review",
        )

        assert result["success"] is True
        assert result["new_status"] in ["draft", "active"]

    async def test_moderation_action_vote_not_found(
        self, moderation_manager, mock_session, sample_super_admin
    ):
        """Test moderation action on non-existent vote."""
        # Mock vote doesn't exist
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.take_moderation_action(
            mock_session, uuid4(), sample_super_admin.id, "close_vote", "Test reason"
        )

        assert result["success"] is False
        assert result["message"] == "Vote not found"

    async def test_close_non_active_vote(
        self, moderation_manager, mock_session, sample_vote, sample_super_admin
    ):
        """Test closing non-active vote."""
        # Set vote as already closed
        sample_vote.status = "closed"

        # Mock vote exists
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = sample_vote
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.take_moderation_action(
            mock_session,
            sample_vote.id,
            sample_super_admin.id,
            "close_vote",
            "Test reason",
        )

        assert result["success"] is False
        assert "Can only close active votes" in result["message"]


class TestBulkModerationAction:
    """Test bulk_moderation_action functionality."""

    async def test_bulk_action_success(
        self, moderation_manager, mock_session, sample_super_admin
    ):
        """Test successful bulk moderation action."""
        vote_ids = [uuid4(), uuid4(), uuid4()]

        # Mock successful individual actions
        async def mock_take_action(session, vote_id, moderator_id, action_type, reason):
            return {
                "success": True,
                "message": "Action completed",
                "vote_id": str(vote_id),
            }

        moderation_manager.take_moderation_action = mock_take_action

        result = await moderation_manager.bulk_moderation_action(
            mock_session,
            vote_ids,
            sample_super_admin.id,
            "disable_vote",
            "Bulk disable for policy violation",
        )

        assert result["success"] is True
        assert result["success_count"] == 3
        assert result["error_count"] == 0
        assert len(result["results"]) == 3

    async def test_bulk_action_too_many_votes(
        self, moderation_manager, mock_session, sample_super_admin
    ):
        """Test bulk action with too many votes."""
        vote_ids = [uuid4() for _ in range(51)]  # Exceeds limit of 50

        result = await moderation_manager.bulk_moderation_action(
            mock_session, vote_ids, sample_super_admin.id, "disable_vote", "Test reason"
        )

        assert result["success"] is False
        assert "Cannot process more than 50 votes" in result["message"]

    async def test_bulk_action_partial_success(
        self, moderation_manager, mock_session, sample_super_admin
    ):
        """Test bulk action with partial success."""
        vote_ids = [uuid4(), uuid4(), uuid4()]

        # Mock mixed results
        call_count = 0

        async def mock_take_action(session, vote_id, moderator_id, action_type, reason):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return {"success": True, "message": "Success"}
            else:
                return {"success": False, "message": "Failed"}

        moderation_manager.take_moderation_action = mock_take_action

        result = await moderation_manager.bulk_moderation_action(
            mock_session, vote_ids, sample_super_admin.id, "disable_vote", "Test reason"
        )

        assert result["success"] is True
        assert result["success_count"] == 2
        assert result["error_count"] == 1


class TestGetPendingFlags:
    """Test get_pending_flags functionality."""

    async def test_get_pending_flags_success(self, moderation_manager, mock_session):
        """Test successful retrieval of pending flags."""
        # Mock database result
        mock_flag = Mock()
        mock_flag.id = uuid4()
        mock_flag.vote_id = uuid4()
        mock_flag.flag_type = "inappropriate_content"
        mock_flag.reason = "Test reason"
        mock_flag.created_at = datetime.utcnow()
        mock_flag.vote = Mock()
        mock_flag.vote.title = "Test Vote"
        mock_flag.vote.slug = "test-vote"
        mock_flag.vote.status = "active"
        mock_flag.vote.creator = Mock()
        mock_flag.vote.creator.email = "creator@test.com"
        mock_flag.flagger = Mock()
        mock_flag.flagger.email = "flagger@test.com"

        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = [mock_flag]
        mock_session.execute.return_value = result_mock

        result = await moderation_manager.get_pending_flags(
            mock_session, limit=10, offset=0
        )

        assert len(result) == 1
        assert result[0]["flag_type"] == "inappropriate_content"
        assert result[0]["vote_title"] == "Test Vote"

    async def test_get_pending_flags_empty(self, moderation_manager, mock_session):
        """Test retrieval of pending flags when none exist."""
        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = result_mock

        result = await moderation_manager.get_pending_flags(mock_session)

        assert len(result) == 0


class TestGetModerationDashboardStats:
    """Test get_moderation_dashboard_stats functionality."""

    async def test_get_dashboard_stats_success(self, moderation_manager, mock_session):
        """Test successful dashboard statistics retrieval."""
        # Mock database results
        pending_result = Mock()
        pending_result.scalar.return_value = 5

        flags_result = [
            Mock(flag_type="spam", count=3),
            Mock(flag_type="inappropriate_content", count=2),
        ]

        actions_result = [
            Mock(action_type="disable_vote", count=4),
            Mock(action_type="hide_vote", count=1),
        ]

        votes_result = [
            Mock(status="disabled", count=2),
            Mock(status="hidden", count=1),
        ]

        mock_session.execute.side_effect = [
            pending_result,
            flags_result,
            actions_result,
            votes_result,
        ]

        result = await moderation_manager.get_moderation_dashboard_stats(mock_session)

        assert result["pending_flags"] == 5
        assert result["recent_flags_by_type"]["spam"] == 3
        assert result["recent_actions_by_type"]["disable_vote"] == 4
        assert result["moderated_votes_by_status"]["disabled"] == 2
        assert result["total_moderated_votes"] == 3

    async def test_get_dashboard_stats_error(self, moderation_manager, mock_session):
        """Test dashboard statistics retrieval with error."""
        # Mock database error
        mock_session.execute.side_effect = Exception("Database error")

        result = await moderation_manager.get_moderation_dashboard_stats(mock_session)

        # Should return default values on error
        assert result["pending_flags"] == 0
        assert result["total_moderated_votes"] == 0


class TestGetVoteModerationSummary:
    """Test get_vote_moderation_summary functionality."""

    async def test_get_vote_summary_success(self, moderation_manager, mock_session):
        """Test successful vote moderation summary retrieval."""
        vote_id = uuid4()

        # Mock vote with creator
        mock_vote = Mock()
        mock_vote.id = vote_id
        mock_vote.title = "Test Vote"
        mock_vote.slug = "test-vote"
        mock_vote.status = "active"
        mock_vote.creator.email = "creator@test.com"

        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = mock_vote

        # Mock empty flags and actions
        empty_result = Mock()
        empty_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [vote_result, empty_result, empty_result]

        result = await moderation_manager.get_vote_moderation_summary(
            mock_session, vote_id
        )

        assert result is not None
        assert result["vote_id"] == str(vote_id)
        assert result["vote_title"] == "Test Vote"
        assert result["creator_email"] == "creator@test.com"
        assert len(result["recent_actions"]) == 0
        assert len(result["flags"]) == 0

    async def test_get_vote_summary_not_found(self, moderation_manager, mock_session):
        """Test vote summary for non-existent vote."""
        vote_result = Mock()
        vote_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = vote_result

        result = await moderation_manager.get_vote_moderation_summary(
            mock_session, uuid4()
        )

        assert result is None


class TestGetFlaggedVotes:
    """Test get_flagged_votes functionality."""

    async def test_get_flagged_votes_success(self, moderation_manager, mock_session):
        """Test successful retrieval of flagged votes."""
        # Mock vote with flags
        mock_vote = Mock()
        mock_vote.id = uuid4()
        mock_vote.title = "Flagged Vote"
        mock_vote.slug = "flagged-vote"
        mock_vote.status = "active"
        mock_vote.created_at = datetime.utcnow()
        mock_vote.creator = Mock()
        mock_vote.creator.email = "creator@test.com"
        mock_vote.options = [Mock(), Mock()]  # 2 options

        votes_result = Mock()
        votes_result.scalars.return_value.all.return_value = [mock_vote]

        # Mock flag counts batch query - create proper row objects
        flags_result = Mock()
        flag_row = Mock()
        flag_row.__getitem__ = Mock(
            side_effect=lambda x: {0: mock_vote.id, 1: "pending", 2: 2}[x]
        )
        flags_result.__iter__ = Mock(return_value=iter([flag_row]))

        # Mock response counts batch query
        responses_result = Mock()
        response_row = Mock()
        response_row.__getitem__ = Mock(
            side_effect=lambda x: {0: mock_vote.id, 1: 10}[x]
        )
        responses_result.__iter__ = Mock(return_value=iter([response_row]))

        # Mock the three calls to execute: votes, flag counts, response counts
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return votes_result
            elif call_count == 2:
                return flags_result
            else:
                return responses_result

        mock_session.execute.side_effect = mock_execute

        result = await moderation_manager.get_flagged_votes(
            mock_session, limit=20, offset=0
        )

        assert len(result) == 1
        assert result[0]["title"] == "Flagged Vote"
        assert result[0]["total_options"] == 2
        assert result[0]["total_responses"] == 10
        assert result[0]["flag_counts"]["pending"] == 2

    async def test_get_flagged_votes_empty(self, moderation_manager, mock_session):
        """Test retrieval of flagged votes when none exist."""
        votes_result = Mock()
        votes_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = votes_result

        result = await moderation_manager.get_flagged_votes(mock_session)

        assert len(result) == 0

    async def test_get_flagged_votes_with_filter(
        self, moderation_manager, mock_session
    ):
        """Test retrieval of flagged votes with status filter."""
        votes_result = Mock()
        votes_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = votes_result

        result = await moderation_manager.get_flagged_votes(
            mock_session, limit=20, offset=0, flag_status="approved"
        )

        assert len(result) == 0
