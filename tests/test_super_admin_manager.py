"""Tests for SuperAdminManager business logic."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from cardinal_vote.models import User
from cardinal_vote.super_admin_manager import SuperAdminManager


@pytest.fixture
async def super_admin_manager():
    """Create SuperAdminManager instance for testing."""
    return SuperAdminManager()


@pytest.fixture
async def mock_session():
    """Create mock async session for testing."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_users():
    """Create sample users for testing."""
    now = datetime.utcnow()
    return [
        User(
            id=uuid4(),
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            is_verified=True,
            is_super_admin=True,
            created_at=now - timedelta(days=10),
        ),
        User(
            id=uuid4(),
            email="user1@test.com",
            first_name="User",
            last_name="One",
            is_verified=True,
            is_super_admin=False,
            created_at=now - timedelta(days=5),
        ),
        User(
            id=uuid4(),
            email="user2@test.com",
            first_name="User",
            last_name="Two",
            is_verified=False,
            is_super_admin=False,
            created_at=now - timedelta(days=1),
        ),
    ]


class TestSuperAdminManager:
    """Test cases for SuperAdminManager class."""

    @pytest.mark.unit
    async def test_init(self):
        """Test SuperAdminManager initialization."""
        manager = SuperAdminManager()
        assert manager is not None

    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_comprehensive_system_stats_success(
        self, super_admin_manager, mock_session
    ):
        """Test successful retrieval of comprehensive system statistics."""
        # Mock user statistics
        user_stats_mock = Mock()
        user_stats_mock.total_users = 100
        user_stats_mock.verified_users = 80
        user_stats_mock.unverified_users = 20
        user_stats_mock.super_admins = 5
        user_stats_mock.recent_users = 10
        user_stats_mock.users_created_today = 2

        # Mock vote statistics
        vote_stats_mock = Mock()
        vote_stats_mock.total_votes = 50
        vote_stats_mock.draft_votes = 10
        vote_stats_mock.active_votes = 20
        vote_stats_mock.closed_votes = 20
        vote_stats_mock.recent_votes = 5
        vote_stats_mock.votes_created_today = 1

        # Mock response statistics
        response_stats_mock = Mock()
        response_stats_mock.total_responses = 200
        response_stats_mock.recent_responses = 30
        response_stats_mock.responses_today = 5

        # Setup mock session responses
        async def mock_execute(*args, **kwargs):
            # Return different results based on call order
            if not hasattr(mock_execute, "call_count"):
                mock_execute.call_count = 0

            mock_execute.call_count += 1

            if mock_execute.call_count == 1:
                # User stats query
                result = AsyncMock()
                result.fetchone = AsyncMock(return_value=user_stats_mock)
                return result
            elif mock_execute.call_count == 2:
                # Vote stats query
                result = AsyncMock()
                result.fetchone = AsyncMock(return_value=vote_stats_mock)
                return result
            else:
                # Response stats query
                result = AsyncMock()
                result.fetchone = AsyncMock(return_value=response_stats_mock)
                return result

        mock_session.execute = mock_execute

        # Execute test
        result = await super_admin_manager.get_comprehensive_system_stats(mock_session)

        # Verify results
        assert isinstance(result, dict)
        assert result["total_users"] == 100
        assert result["verified_users"] == 80
        assert result["unverified_users"] == 20
        assert result["super_admins"] == 5
        assert result["total_votes"] == 50
        assert result["total_responses"] == 200
        assert "platform_health" in result
        assert "timestamp" in result

        # Verify session calls
        assert mock_session.execute.call_count == 3

    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_comprehensive_system_stats_empty_database(
        self, super_admin_manager, mock_session
    ):
        """Test system statistics with empty database."""
        # Mock empty results
        mock_session.execute.side_effect = [
            AsyncMock(fetchone=AsyncMock(return_value=None)),
            AsyncMock(fetchone=AsyncMock(return_value=None)),
            AsyncMock(fetchone=AsyncMock(return_value=None)),
        ]

        result = await super_admin_manager.get_comprehensive_system_stats(mock_session)

        # Verify all counts are zero
        assert result["total_users"] == 0
        assert result["verified_users"] == 0
        assert result["total_votes"] == 0
        assert result["total_responses"] == 0

    @pytest.mark.unit
    async def test_calculate_platform_health_healthy(
        self, super_admin_manager, mock_session
    ):
        """Test platform health calculation for healthy system."""
        stats = {
            "total_users": 100,
            "verified_users": 90,  # 90% verification rate
            "total_votes": 50,
            "active_votes": 20,  # 40% active rate
            "recent_users": 10,
            "recent_responses": 30,
        }

        health = await super_admin_manager._calculate_platform_health(
            mock_session, stats
        )

        assert health["status"] == "healthy"
        assert health["score"] >= 80
        assert len(health["warnings"]) == 0

    @pytest.mark.unit
    async def test_calculate_platform_health_warning(
        self, super_admin_manager, mock_session
    ):
        """Test platform health calculation for warning status."""
        stats = {
            "total_users": 100,
            "verified_users": 30,  # 30% verification rate (low)
            "total_votes": 50,
            "active_votes": 10,  # 20% active rate (low)
            "recent_users": 0,  # No recent users
            "recent_responses": 0,  # No recent responses
        }

        health = await super_admin_manager._calculate_platform_health(
            mock_session, stats
        )

        assert health["status"] in ["warning", "critical"]
        assert health["score"] < 80
        assert len(health["warnings"]) > 0

    @pytest.mark.unit
    async def test_calculate_platform_health_zero_division_protection(
        self, super_admin_manager, mock_session
    ):
        """Test platform health calculation with zero values (zero-division protection)."""
        stats = {
            "total_users": 0,
            "verified_users": 0,
            "total_votes": 0,
            "active_votes": 0,
            "recent_users": 0,
            "recent_responses": 0,
        }

        health = await super_admin_manager._calculate_platform_health(
            mock_session, stats
        )

        # Should handle zero division gracefully and return healthy status
        # (no penalties applied due to zero-division protection)
        assert health["status"] == "healthy"
        assert health["score"] == 100
        assert len(health["warnings"]) == 0

    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_recent_user_activity_success(
        self, super_admin_manager, mock_session
    ):
        """Test successful retrieval of recent user activity."""
        # Mock user data with vote counts
        mock_users = [
            Mock(
                id=uuid4(),
                email="user1@test.com",
                first_name="User",
                last_name="One",
                is_verified=True,
                is_super_admin=False,
                created_at=datetime.utcnow() - timedelta(days=1),
                last_login=datetime.utcnow() - timedelta(hours=2),
                vote_count=5,
            ),
            Mock(
                id=uuid4(),
                email="user2@test.com",
                first_name="User",
                last_name="Two",
                is_verified=False,
                is_super_admin=False,
                created_at=datetime.utcnow() - timedelta(days=2),
                last_login=None,
                vote_count=0,
            ),
        ]

        mock_session.execute.return_value = AsyncMock(
            fetchall=AsyncMock(return_value=mock_users)
        )

        result = await super_admin_manager.get_recent_user_activity(
            mock_session, limit=10
        )

        assert isinstance(result, list)
        assert len(result) == 2

        # Check first user
        user_activity = result[0]
        assert user_activity["type"] == "user_registration"
        assert user_activity["user_email"] == "user1@test.com"
        assert user_activity["user_name"] == "User One"
        assert user_activity["is_verified"] is True
        assert user_activity["vote_count"] == 5
        assert user_activity["last_login"] is not None

        # Check second user
        user_activity = result[1]
        assert user_activity["user_email"] == "user2@test.com"
        assert user_activity["is_verified"] is False
        assert user_activity["vote_count"] == 0
        assert user_activity["last_login"] is None

    @pytest.mark.unit
    @pytest.mark.database
    async def test_bulk_update_users_verify_success(
        self, super_admin_manager, mock_session
    ):
        """Test successful bulk user verification."""
        user_ids = [uuid4(), uuid4(), uuid4()]

        # Mock successful update result
        mock_result = Mock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result

        result = await super_admin_manager.bulk_update_users(
            mock_session, user_ids, "verify_users"
        )

        assert result["success"] is True
        assert result["affected_count"] == 3
        assert "Successfully verified 3 users" in result["message"]
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.database
    async def test_bulk_update_users_unverify_success(
        self, super_admin_manager, mock_session
    ):
        """Test successful bulk user unverification."""
        user_ids = [uuid4(), uuid4()]

        # Mock successful update result
        mock_result = Mock()
        mock_result.rowcount = 2
        mock_session.execute.return_value = mock_result

        result = await super_admin_manager.bulk_update_users(
            mock_session, user_ids, "unverify_users"
        )

        assert result["success"] is True
        assert result["affected_count"] == 2
        assert "Successfully unverified 2 users" in result["message"]

    @pytest.mark.unit
    async def test_bulk_update_users_no_users(self, super_admin_manager, mock_session):
        """Test bulk update with empty user list."""
        result = await super_admin_manager.bulk_update_users(
            mock_session, [], "verify_users"
        )

        assert result["success"] is False
        assert result["message"] == "No users specified"

    @pytest.mark.unit
    async def test_bulk_update_users_size_limit(
        self, super_admin_manager, mock_session
    ):
        """Test bulk update with too many users."""
        from cardinal_vote.super_admin_manager import BULK_OPERATION_LIMITS

        # Create more user IDs than the limit allows
        user_ids = [
            uuid4() for _ in range(BULK_OPERATION_LIMITS["max_users_per_operation"] + 1)
        ]

        result = await super_admin_manager.bulk_update_users(
            mock_session, user_ids, "verify_users"
        )

        assert result["success"] is False
        assert "Too many users specified" in result["message"]
        assert (
            str(BULK_OPERATION_LIMITS["max_users_per_operation"]) in result["message"]
        )

    @pytest.mark.unit
    async def test_bulk_update_users_invalid_operation(
        self, super_admin_manager, mock_session
    ):
        """Test bulk update with invalid operation."""
        user_ids = [uuid4()]

        result = await super_admin_manager.bulk_update_users(
            mock_session, user_ids, "invalid_operation"
        )

        assert result["success"] is False
        assert "Unknown bulk operation" in result["message"]

    @pytest.mark.unit
    @pytest.mark.database
    async def test_bulk_update_users_database_error(
        self, super_admin_manager, mock_session
    ):
        """Test bulk update with database error."""
        from sqlalchemy.exc import SQLAlchemyError

        user_ids = [uuid4()]
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        result = await super_admin_manager.bulk_update_users(
            mock_session, user_ids, "verify_users"
        )

        assert result["success"] is False
        assert "Database error during bulk operation" in result["message"]
        mock_session.rollback.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_user_management_summary_success(
        self, super_admin_manager, mock_session
    ):
        """Test successful retrieval of user management summary."""
        # Mock verified users
        verified_users = [Mock(id=uuid4(), email="verified@test.com")]
        # Mock unverified users
        unverified_users = [Mock(id=uuid4(), email="unverified@test.com")]
        # Mock super admins
        super_admins = [Mock(id=uuid4(), email="admin@test.com")]

        # Mock most active users query result
        most_active_users = [
            Mock(
                id=uuid4(),
                email="active@test.com",
                first_name="Active",
                last_name="User",
                vote_count=10,
            )
        ]

        mock_session.execute.side_effect = [
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=verified_users))
                )
            ),
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=unverified_users))
                )
            ),
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=super_admins))
                )
            ),
            AsyncMock(fetchall=AsyncMock(return_value=most_active_users)),
        ]

        result = await super_admin_manager.get_user_management_summary(mock_session)

        assert isinstance(result, dict)
        assert result["verified_users_count"] == 1
        assert result["unverified_users_count"] == 1
        assert result["super_admins_count"] == 1
        assert len(result["most_active_users"]) == 1
        assert result["most_active_users"][0]["email"] == "active@test.com"
        assert result["most_active_users"][0]["vote_count"] == 10

    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_platform_audit_log_success(
        self, super_admin_manager, mock_session
    ):
        """Test successful retrieval of platform audit log."""
        # Mock recent users
        recent_users = [
            Mock(
                id=uuid4(),
                email="newuser@test.com",
                first_name="New",
                last_name="User",
                created_at=datetime.utcnow() - timedelta(days=1),
                is_verified=True,
            )
        ]

        # Mock recent votes with user data
        recent_votes = [
            (
                Mock(
                    id=uuid4(),
                    title="Test Vote",
                    slug="test-vote",
                    status="active",
                    created_at=datetime.utcnow() - timedelta(hours=6),
                ),
                Mock(email="creator@test.com"),
            )
        ]

        mock_session.execute.side_effect = [
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=recent_users))
                )
            ),
            AsyncMock(all=AsyncMock(return_value=recent_votes)),
        ]

        result = await super_admin_manager.get_platform_audit_log(
            mock_session, limit=20
        )

        assert isinstance(result, list)
        assert len(result) <= 20

        # Check for user registration event
        user_events = [e for e in result if e["event_type"] == "user_registration"]
        assert len(user_events) == 1
        assert user_events[0]["user_email"] == "newuser@test.com"

        # Check for vote creation event
        vote_events = [e for e in result if e["event_type"] == "vote_creation"]
        assert len(vote_events) == 1
        assert vote_events[0]["details"] == "Vote created: Test Vote"

    @pytest.mark.unit
    @pytest.mark.database
    async def test_database_error_handling(self, super_admin_manager, mock_session):
        """Test database error handling in various methods."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_session.execute.side_effect = SQLAlchemyError("Database connection error")

        # Test error handling in get_comprehensive_system_stats
        with pytest.raises(SQLAlchemyError):
            await super_admin_manager.get_comprehensive_system_stats(mock_session)

        # Test error handling in get_recent_user_activity
        with pytest.raises(SQLAlchemyError):
            await super_admin_manager.get_recent_user_activity(mock_session)

        # Test error handling in get_user_management_summary
        with pytest.raises(SQLAlchemyError):
            await super_admin_manager.get_user_management_summary(mock_session)

    @pytest.mark.performance
    async def test_query_efficiency(self, super_admin_manager, mock_session):
        """Test that queries are efficient and avoid N+1 problems."""
        # Mock data for performance test
        mock_session.execute.return_value = AsyncMock(
            fetchall=AsyncMock(return_value=[])
        )

        # Test recent user activity - should use single query with JOIN
        await super_admin_manager.get_recent_user_activity(mock_session, limit=100)

        # Should only execute one query (with JOIN) instead of N+1 queries
        assert mock_session.execute.call_count == 1

        # Reset mock
        mock_session.reset_mock()

        # Test user management summary - should use efficient queries
        mock_session.execute.side_effect = [
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=[]))
                )
            ),
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=[]))
                )
            ),
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=[]))
                )
            ),
            AsyncMock(fetchall=AsyncMock(return_value=[])),
        ]

        await super_admin_manager.get_user_management_summary(mock_session)

        # Should use 4 optimized queries instead of many individual queries
        assert mock_session.execute.call_count == 4
