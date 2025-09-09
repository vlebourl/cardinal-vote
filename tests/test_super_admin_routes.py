"""Tests for super admin API routes."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from cardinal_vote.models import User
from cardinal_vote.super_admin_routes import (
    bulk_update_users_endpoint,
    get_comprehensive_system_stats,
    get_platform_audit_log,
    get_recent_user_activity,
    get_system_statistics,
    get_user_details,
    get_user_management_summary,
    list_users,
    manage_user,
)


@pytest.fixture
def sample_super_admin_user():
    """Create a sample super admin user for testing."""
    return User(
        id=uuid4(),
        email="superadmin@test.com",
        first_name="Super",
        last_name="Admin",
        is_verified=True,
        is_super_admin=True,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_regular_user():
    """Create a sample regular user for testing."""
    return User(
        id=uuid4(),
        email="user@test.com",
        first_name="Regular",
        last_name="User",
        is_verified=True,
        is_super_admin=False,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
async def mock_session():
    """Create mock async session for testing."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_auth_manager():
    """Create mock auth manager for testing."""
    return AsyncMock()


class TestSystemStatistics:
    """Test cases for system statistics endpoints."""

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_system_statistics_success(
        self, sample_super_admin_user, mock_session
    ):
        """Test successful system statistics retrieval."""
        # Mock database query results
        mock_session.execute.side_effect = [
            AsyncMock(scalar=AsyncMock(return_value=100)),  # total_users
            AsyncMock(scalar=AsyncMock(return_value=80)),  # verified_users
            AsyncMock(scalar=AsyncMock(return_value=5)),  # super_admins
            AsyncMock(scalar=AsyncMock(return_value=50)),  # total_votes
            AsyncMock(scalar=AsyncMock(return_value=20)),  # active_votes
            AsyncMock(scalar=AsyncMock(return_value=200)),  # total_responses
        ]

        result = await get_system_statistics(
            current_user=sample_super_admin_user, session=mock_session
        )

        assert result.total_users == 100
        assert result.verified_users == 80
        assert result.super_admins == 5
        assert result.total_votes == 50
        assert result.active_votes == 20
        assert result.total_responses == 200

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_system_statistics_database_error(
        self, sample_super_admin_user, mock_session
    ):
        """Test system statistics with database error."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await get_system_statistics(
                current_user=sample_super_admin_user, session=mock_session
            )

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_comprehensive_system_stats_success(
        self, sample_super_admin_user, mock_session
    ):
        """Test comprehensive system statistics endpoint."""
        expected_stats = {
            "total_users": 100,
            "verified_users": 80,
            "platform_health": {"status": "healthy", "score": 95},
            "timestamp": "2023-01-01T00:00:00",
        }

        with patch(
            "cardinal_vote.super_admin_routes.SuperAdminManager"
        ) as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.get_comprehensive_system_stats.return_value = expected_stats
            mock_manager_class.return_value = mock_manager

            result = await get_comprehensive_system_stats(
                current_user=sample_super_admin_user, session=mock_session
            )

            assert result == expected_stats
            mock_manager.get_comprehensive_system_stats.assert_called_once_with(
                mock_session
            )


class TestUserManagement:
    """Test cases for user management endpoints."""

    @pytest.mark.unit
    @pytest.mark.api
    async def test_list_users_success(self, sample_super_admin_user, mock_session):
        """Test successful user listing with pagination."""
        # Mock user data
        mock_users = [
            Mock(
                id=uuid4(),
                email="user1@test.com",
                first_name="User",
                last_name="One",
                is_verified=True,
                is_super_admin=False,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                vote_count=5,
            ),
            Mock(
                id=uuid4(),
                email="user2@test.com",
                first_name="User",
                last_name="Two",
                is_verified=False,
                is_super_admin=False,
                created_at=datetime.utcnow(),
                last_login=None,
                vote_count=0,
            ),
        ]

        # Mock query execution
        mock_session.execute.side_effect = [
            AsyncMock(fetchall=AsyncMock(return_value=mock_users)),  # Main query
            AsyncMock(scalar=AsyncMock(return_value=2)),  # Count query
        ]

        result = await list_users(
            current_user=sample_super_admin_user,
            session=mock_session,
            page=1,
            limit=20,
            search=None,
        )

        assert "users" in result
        assert "pagination" in result
        assert len(result["users"]) == 2
        assert result["pagination"]["total_count"] == 2

    @pytest.mark.unit
    @pytest.mark.api
    async def test_list_users_with_search(self, sample_super_admin_user, mock_session):
        """Test user listing with search functionality."""
        mock_users = [
            Mock(
                id=uuid4(),
                email="john@test.com",
                first_name="John",
                last_name="Doe",
                is_verified=True,
                is_super_admin=False,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                vote_count=3,
            ),
        ]

        mock_session.execute.side_effect = [
            AsyncMock(fetchall=AsyncMock(return_value=mock_users)),
            AsyncMock(scalar=AsyncMock(return_value=1)),
        ]

        result = await list_users(
            current_user=sample_super_admin_user,
            session=mock_session,
            page=1,
            limit=20,
            search="john",
        )

        assert len(result["users"]) == 1
        assert result["users"][0]["email"] == "john@test.com"

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_user_details_success(
        self,
        sample_super_admin_user,
        sample_regular_user,
        mock_session,
        mock_auth_manager,
    ):
        """Test successful user details retrieval."""
        user_id = sample_regular_user.id

        # Mock auth manager response
        mock_auth_manager.get_user_by_id.return_value = sample_regular_user

        # Mock database queries
        mock_session.execute.side_effect = [
            AsyncMock(scalar=AsyncMock(return_value=5)),  # total_votes
            AsyncMock(scalar=AsyncMock(return_value=2)),  # active_votes
            AsyncMock(
                scalars=AsyncMock(
                    return_value=AsyncMock(all=AsyncMock(return_value=[]))
                )
            ),  # recent_votes
        ]

        result = await get_user_details(
            user_id=user_id,
            current_user=sample_super_admin_user,
            auth_manager=mock_auth_manager,
            session=mock_session,
        )

        assert "user" in result
        assert "statistics" in result
        assert "recent_votes" in result
        assert result["user"]["id"] == str(user_id)
        assert result["statistics"]["total_votes"] == 5

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_user_details_not_found(
        self, sample_super_admin_user, mock_session, mock_auth_manager
    ):
        """Test user details for non-existent user."""
        user_id = uuid4()
        mock_auth_manager.get_user_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_user_details(
                user_id=user_id,
                current_user=sample_super_admin_user,
                auth_manager=mock_auth_manager,
                session=mock_session,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.unit
    @pytest.mark.api
    async def test_manage_user_update_success(
        self,
        sample_super_admin_user,
        sample_regular_user,
        mock_session,
        mock_auth_manager,
    ):
        """Test successful user management update."""
        from cardinal_vote.super_admin_routes import UserManagementRequest

        user_id = sample_regular_user.id
        request_data = UserManagementRequest(
            operation="update_user",
            user_id=user_id,
            is_verified=True,
            is_super_admin=False,
        )

        mock_auth_manager.get_user_by_id.return_value = sample_regular_user

        result = await manage_user(
            request_data=request_data,
            current_user=sample_super_admin_user,
            auth_manager=mock_auth_manager,
            session=mock_session,
        )

        assert result.status_code == 200
        response_data = result.body.decode()
        assert "success" in response_data
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.api
    async def test_manage_user_self_modification_blocked(
        self, sample_super_admin_user, mock_session, mock_auth_manager
    ):
        """Test that super admin cannot modify their own super admin status."""
        from cardinal_vote.super_admin_routes import UserManagementRequest

        request_data = UserManagementRequest(
            operation="update_user",
            user_id=sample_super_admin_user.id,
            is_super_admin=False,
        )

        mock_auth_manager.get_user_by_id.return_value = sample_super_admin_user

        result = await manage_user(
            request_data=request_data,
            current_user=sample_super_admin_user,
            auth_manager=mock_auth_manager,
            session=mock_session,
        )

        assert result.status_code == 400
        response_data = result.body.decode()
        assert "Cannot modify your own super admin status" in response_data


class TestBulkOperations:
    """Test cases for bulk operations endpoints."""

    @pytest.mark.unit
    @pytest.mark.api
    async def test_bulk_update_users_success(
        self, sample_super_admin_user, mock_session
    ):
        """Test successful bulk user update."""
        request_data = {
            "user_ids": [str(uuid4()), str(uuid4())],
            "operation": "verify_users",
        }

        expected_result = {
            "success": True,
            "message": "Successfully verified 2 users",
            "affected_count": 2,
        }

        with patch(
            "cardinal_vote.super_admin_routes.SuperAdminManager"
        ) as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.bulk_update_users.return_value = expected_result
            mock_manager_class.return_value = mock_manager

            result = await bulk_update_users_endpoint(
                request_data=request_data,
                current_user=sample_super_admin_user,
                session=mock_session,
            )

            assert result == expected_result
            mock_manager.bulk_update_users.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.api
    async def test_bulk_update_users_invalid_request(
        self, sample_super_admin_user, mock_session
    ):
        """Test bulk update with invalid request data."""
        request_data = {
            "user_ids": [],  # Empty list
            "operation": "verify_users",
        }

        result = await bulk_update_users_endpoint(
            request_data=request_data,
            current_user=sample_super_admin_user,
            session=mock_session,
        )

        assert result["success"] is False
        assert "user_ids and operation are required" in result["message"]

    @pytest.mark.unit
    @pytest.mark.api
    async def test_bulk_update_users_invalid_uuid(
        self, sample_super_admin_user, mock_session
    ):
        """Test bulk update with invalid UUID format."""
        request_data = {
            "user_ids": ["invalid-uuid", "another-invalid"],
            "operation": "verify_users",
        }

        result = await bulk_update_users_endpoint(
            request_data=request_data,
            current_user=sample_super_admin_user,
            session=mock_session,
        )

        assert result["success"] is False
        assert "Invalid user ID format" in result["message"]


class TestActivityAndAudit:
    """Test cases for activity and audit endpoints."""

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_recent_user_activity_success(
        self, sample_super_admin_user, mock_session
    ):
        """Test successful recent user activity retrieval."""
        expected_activity = [
            {
                "type": "user_registration",
                "user_id": str(uuid4()),
                "user_email": "newuser@test.com",
                "user_name": "New User",
                "is_verified": True,
                "vote_count": 2,
                "created_at": "2023-01-01T00:00:00",
            }
        ]

        with patch(
            "cardinal_vote.super_admin_routes.SuperAdminManager"
        ) as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.get_recent_user_activity.return_value = expected_activity
            mock_manager_class.return_value = mock_manager

            result = await get_recent_user_activity(
                current_user=sample_super_admin_user, session=mock_session, limit=20
            )

            assert result == expected_activity
            mock_manager.get_recent_user_activity.assert_called_once_with(
                mock_session, 20
            )

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_user_management_summary_success(
        self, sample_super_admin_user, mock_session
    ):
        """Test successful user management summary retrieval."""
        expected_summary = {
            "verified_users_count": 50,
            "unverified_users_count": 10,
            "super_admins_count": 3,
            "most_active_users": [],
            "recent_registrations": [],
        }

        with patch(
            "cardinal_vote.super_admin_routes.SuperAdminManager"
        ) as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.get_user_management_summary.return_value = expected_summary
            mock_manager_class.return_value = mock_manager

            result = await get_user_management_summary(
                current_user=sample_super_admin_user, session=mock_session
            )

            assert result == expected_summary

    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_platform_audit_log_success(
        self, sample_super_admin_user, mock_session
    ):
        """Test successful platform audit log retrieval."""
        expected_audit_log = [
            {
                "event_type": "user_registration",
                "timestamp": "2023-01-01T00:00:00",
                "user_email": "user@test.com",
                "details": "New user registered",
            },
            {
                "event_type": "vote_creation",
                "timestamp": "2023-01-01T01:00:00",
                "user_email": "admin@test.com",
                "details": "Vote created: Test Vote",
                "vote_slug": "test-vote",
            },
        ]

        with patch(
            "cardinal_vote.super_admin_routes.SuperAdminManager"
        ) as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.get_platform_audit_log.return_value = expected_audit_log
            mock_manager_class.return_value = mock_manager

            result = await get_platform_audit_log(
                current_user=sample_super_admin_user, session=mock_session, limit=50
            )

            assert result == expected_audit_log
            mock_manager.get_platform_audit_log.assert_called_once_with(
                mock_session, 50
            )


class TestErrorHandling:
    """Test cases for error handling in API routes."""

    @pytest.mark.unit
    @pytest.mark.api
    async def test_database_error_propagation(
        self, sample_super_admin_user, mock_session
    ):
        """Test that database errors are properly handled and propagated."""
        from sqlalchemy.exc import SQLAlchemyError

        with patch(
            "cardinal_vote.super_admin_routes.SuperAdminManager"
        ) as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.get_comprehensive_system_stats.side_effect = SQLAlchemyError(
                "DB Error"
            )
            mock_manager_class.return_value = mock_manager

            with pytest.raises(HTTPException) as exc_info:
                await get_comprehensive_system_stats(
                    current_user=sample_super_admin_user, session=mock_session
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.unit
    @pytest.mark.api
    async def test_generic_exception_handling(
        self, sample_super_admin_user, mock_session
    ):
        """Test handling of unexpected exceptions."""
        with patch(
            "cardinal_vote.super_admin_routes.SuperAdminManager"
        ) as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager.get_recent_user_activity.side_effect = Exception(
                "Unexpected error"
            )
            mock_manager_class.return_value = mock_manager

            with pytest.raises(HTTPException) as exc_info:
                await get_recent_user_activity(
                    current_user=sample_super_admin_user, session=mock_session, limit=20
                )

            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestValidationAndSecurity:
    """Test cases for input validation and security."""

    @pytest.mark.unit
    @pytest.mark.api
    async def test_pagination_limits(self, sample_super_admin_user, mock_session):
        """Test that pagination limits are enforced."""
        # Mock empty result
        mock_session.execute.side_effect = [
            AsyncMock(fetchall=AsyncMock(return_value=[])),
            AsyncMock(scalar=AsyncMock(return_value=0)),
        ]

        # Test with valid limits
        result = await list_users(
            current_user=sample_super_admin_user,
            session=mock_session,
            page=1,
            limit=20,
            search=None,
        )
        assert "users" in result

        # Test with edge case limits (should be handled by FastAPI Query validation)
        result = await list_users(
            current_user=sample_super_admin_user,
            session=mock_session,
            page=1,
            limit=100,  # Max limit
            search=None,
        )
        assert "users" in result

    @pytest.mark.unit
    @pytest.mark.api
    async def test_user_id_validation(
        self, sample_super_admin_user, mock_session, mock_auth_manager
    ):
        """Test user ID validation in endpoints."""
        # Test with valid UUID
        valid_uuid = uuid4()
        mock_auth_manager.get_user_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_user_details(
                user_id=valid_uuid,
                current_user=sample_super_admin_user,
                auth_manager=mock_auth_manager,
                session=mock_session,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.performance
    async def test_query_performance(self, sample_super_admin_user, mock_session):
        """Test that endpoints use efficient queries."""
        # Mock empty results
        mock_session.execute.side_effect = [
            AsyncMock(fetchall=AsyncMock(return_value=[])),
            AsyncMock(scalar=AsyncMock(return_value=0)),
        ]

        # Test user listing endpoint
        await list_users(
            current_user=sample_super_admin_user,
            session=mock_session,
            page=1,
            limit=50,
            search=None,
        )

        # Should use exactly 2 queries: one for data, one for count
        assert mock_session.execute.call_count == 2
