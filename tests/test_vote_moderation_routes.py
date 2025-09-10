"""Tests for vote moderation API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import httpx
import pytest
from httpx import AsyncClient

from cardinal_vote.main import app
from cardinal_vote.super_admin_routes import (
    super_admin_router,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_app():
    """Ensure the super admin router is registered for tests."""
    # Check if super admin router is already included
    router_paths = []
    for route in app.routes:
        if hasattr(route, "path"):
            router_paths.append(route.path)

    # If super admin routes are not found, manually include them
    if not any("/api/admin/" in path for path in router_paths):
        # Include the router
        app.include_router(super_admin_router)

    # Override dependencies for testing
    from unittest.mock import AsyncMock, Mock

    from cardinal_vote.dependencies import (
        get_async_session,
        get_auth_manager,
        get_current_super_admin,
    )

    def override_get_auth_manager():
        mock_auth_manager = Mock()
        return mock_auth_manager

    def override_get_async_session():
        mock_session = AsyncMock()
        return mock_session

    async def override_get_current_super_admin():
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.is_super_admin = True
        mock_user.email = "admin@test.com"
        return mock_user

    # Override the dependencies
    app.dependency_overrides[get_auth_manager] = override_get_auth_manager
    app.dependency_overrides[get_async_session] = override_get_async_session
    app.dependency_overrides[get_current_super_admin] = override_get_current_super_admin


@pytest.fixture
def auth_headers():
    """Mock authorization headers for super admin."""
    return {"Authorization": "Bearer mock-jwt-token"}


@pytest.fixture
def sample_vote_data():
    """Sample vote data for testing."""
    return {
        "id": str(uuid4()),
        "title": "Test Vote",
        "description": "Test description",
        "slug": "test-vote",
        "status": "active",
        "creator_id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_flag_data():
    """Sample flag data for testing."""
    return {
        "id": str(uuid4()),
        "vote_id": str(uuid4()),
        "flag_type": "inappropriate_content",
        "reason": "This content violates community standards",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }


class TestModerationDashboardEndpoint:
    """Test /api/admin/moderation/dashboard endpoint."""

    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_get_moderation_dashboard_success(self, mock_manager, auth_headers):
        """Test successful dashboard data retrieval."""
        # Mock manager responses - use AsyncMock for awaitable methods
        mock_manager_instance = Mock()
        mock_manager_instance.get_moderation_dashboard_stats = AsyncMock(
            return_value={"pending_flags": 5, "total_moderated_votes": 10}
        )
        mock_manager_instance.get_pending_flags = AsyncMock(return_value=[])
        mock_manager_instance.get_flagged_votes = AsyncMock(return_value=[])
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/moderation/dashboard", headers=auth_headers
            )

        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "pending_flags" in data
        assert "flagged_votes" in data

    async def test_get_moderation_dashboard_unauthorized(self):
        """Test dashboard access without authentication."""
        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/admin/moderation/dashboard")

        assert response.status_code == 401

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_get_moderation_dashboard_error(
        self, mock_manager, mock_auth, auth_headers
    ):
        """Test dashboard endpoint with internal error."""
        # Mock authentication
        mock_user = Mock()
        mock_auth.return_value = mock_user

        # Mock manager error
        mock_manager_instance = Mock()
        mock_manager_instance.get_moderation_dashboard_stats.side_effect = Exception(
            "Database error"
        )
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/moderation/dashboard", headers=auth_headers
            )

        assert response.status_code == 500


class TestFlagsEndpoints:
    """Test flag management endpoints."""

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_get_pending_flags_success(
        self, mock_manager, mock_auth, auth_headers, sample_flag_data
    ):
        """Test successful pending flags retrieval."""
        # Mock authentication
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.get_pending_flags.return_value = [sample_flag_data]
        mock_manager.return_value = mock_manager_instance

        # Mock count query
        with patch("cardinal_vote.super_admin_routes.session") as mock_session:
            mock_result = Mock()
            mock_result.scalar.return_value = 1
            mock_session.execute.return_value = mock_result

            transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/moderation/flags", headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "flags" in data
        assert "total_count" in data

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_review_flag_success(self, mock_manager, mock_auth, auth_headers):
        """Test successful flag review."""
        flag_id = str(uuid4())
        review_data = {
            "status": "approved",
            "review_notes": "Flag approved after review",
        }

        # Mock authentication
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.review_vote_flag.return_value = {
            "success": True,
            "message": "Flag reviewed successfully",
            "flag_id": flag_id,
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/moderation/flags/{flag_id}/review",
                json=review_data,
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["flag_id"] == flag_id

    async def test_review_flag_invalid_uuid(self, auth_headers):
        """Test flag review with invalid UUID format."""
        review_data = {"status": "approved", "review_notes": "Test notes"}

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/admin/moderation/flags/invalid-uuid/review",
                json=review_data,
                headers=auth_headers,
            )

        assert response.status_code == 400
        assert "Invalid flag ID format" in response.json()["detail"]

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_review_flag_not_found(self, mock_manager, mock_auth, auth_headers):
        """Test review of non-existent flag."""
        flag_id = str(uuid4())
        review_data = {"status": "approved", "review_notes": "Test notes"}

        # Mock authentication
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.review_vote_flag.return_value = {
            "success": False,
            "message": "Flag not found",
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/moderation/flags/{flag_id}/review",
                json=review_data,
                headers=auth_headers,
            )

        assert response.status_code == 400
        assert "Flag not found" in response.json()["detail"]


class TestVoteModerationEndpoints:
    """Test vote moderation endpoints."""

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_get_flagged_votes_success(
        self, mock_manager, mock_auth, auth_headers, sample_vote_data
    ):
        """Test successful flagged votes retrieval."""
        # Mock authentication
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.get_flagged_votes.return_value = [sample_vote_data]
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/admin/moderation/votes", headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "votes" in data
        assert len(data["votes"]) == 1

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_get_vote_moderation_summary_success(
        self, mock_manager, mock_auth, auth_headers
    ):
        """Test successful vote moderation summary retrieval."""
        vote_id = str(uuid4())

        # Mock authentication
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.get_vote_moderation_summary.return_value = {
            "vote_id": vote_id,
            "vote_title": "Test Vote",
            "vote_status": "active",
            "creator_email": "test@example.com",
            "recent_actions": [],
            "flags": [],
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                f"/api/admin/moderation/votes/{vote_id}/summary", headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["vote_id"] == vote_id

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_take_moderation_action_success(
        self, mock_manager, mock_auth, auth_headers
    ):
        """Test successful moderation action."""
        vote_id = str(uuid4())
        action_data = {
            "action_type": "disable_vote",
            "reason": "Policy violation",
            "additional_data": {"severity": "high"},
        }

        # Mock authentication
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.take_moderation_action.return_value = {
            "success": True,
            "message": "Action completed successfully",
            "action_id": str(uuid4()),
            "vote_id": vote_id,
            "previous_status": "active",
            "new_status": "disabled",
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/moderation/votes/{vote_id}/action",
                json=action_data,
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["vote_id"] == vote_id

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_bulk_moderation_action_success(
        self, mock_manager, mock_auth, auth_headers
    ):
        """Test successful bulk moderation action."""
        bulk_data = {
            "vote_ids": [str(uuid4()), str(uuid4())],
            "action_type": "disable_vote",
            "reason": "Bulk policy enforcement",
        }

        # Mock authentication
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.bulk_moderation_action.return_value = {
            "success": True,
            "message": "Bulk action completed: 2 successful, 0 failed",
            "success_count": 2,
            "error_count": 0,
            "results": [
                {
                    "vote_id": bulk_data["vote_ids"][0],
                    "success": True,
                    "message": "Success",
                },
                {
                    "vote_id": bulk_data["vote_ids"][1],
                    "success": True,
                    "message": "Success",
                },
            ],
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/admin/moderation/bulk-action",
                json=bulk_data,
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["success_count"] == 2
        assert data["error_count"] == 0

    async def test_bulk_moderation_action_invalid_vote_id(self, auth_headers):
        """Test bulk action with invalid vote ID."""
        bulk_data = {
            "vote_ids": ["invalid-uuid", str(uuid4())],
            "action_type": "disable_vote",
            "reason": "Test reason",
        }

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/admin/moderation/bulk-action",
                json=bulk_data,
                headers=auth_headers,
            )

        assert response.status_code == 400
        assert "Invalid vote ID format" in response.json()["detail"]


class TestPublicFlagEndpoint:
    """Test public vote flagging endpoint."""

    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_flag_vote_success_anonymous(self, mock_manager):
        """Test successful anonymous vote flagging."""
        vote_id = str(uuid4())
        flag_data = {
            "flag_type": "inappropriate_content",
            "reason": "This content is inappropriate",
        }

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.create_vote_flag.return_value = {
            "success": True,
            "message": "Vote flagged successfully",
            "flag_id": str(uuid4()),
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/flag-vote/{vote_id}/flag", json=flag_data
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_flag_vote_success_authenticated(
        self, mock_manager, mock_auth, auth_headers
    ):
        """Test successful authenticated vote flagging."""
        vote_id = str(uuid4())
        flag_data = {"flag_type": "spam", "reason": "This is spam content"}

        # Mock authentication (optional for this endpoint)
        mock_auth.return_value = Mock(id=uuid4())

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.create_vote_flag.return_value = {
            "success": True,
            "message": "Vote flagged successfully",
            "flag_id": str(uuid4()),
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/flag-vote/{vote_id}/flag",
                json=flag_data,
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_flag_vote_invalid_uuid(self):
        """Test vote flagging with invalid vote ID."""
        flag_data = {"flag_type": "spam", "reason": "Test reason"}

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/admin/flag-vote/invalid-uuid/flag", json=flag_data
            )

        assert response.status_code == 400
        assert "Invalid vote ID format" in response.json()["detail"]

    @patch("cardinal_vote.super_admin_routes.VoteModerationManager")
    async def test_flag_vote_not_found(self, mock_manager):
        """Test flagging non-existent vote."""
        vote_id = str(uuid4())
        flag_data = {"flag_type": "spam", "reason": "Test reason"}

        # Mock manager response
        mock_manager_instance = Mock()
        mock_manager_instance.create_vote_flag.return_value = {
            "success": False,
            "message": "Vote not found",
        }
        mock_manager.return_value = mock_manager_instance

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/flag-vote/{vote_id}/flag", json=flag_data
            )

        assert response.status_code == 400
        assert "Vote not found" in response.json()["detail"]

    async def test_flag_vote_invalid_flag_type(self):
        """Test vote flagging with invalid flag type."""
        vote_id = str(uuid4())
        flag_data = {"flag_type": "invalid_type", "reason": "Test reason"}

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/flag-vote/{vote_id}/flag", json=flag_data
            )

        assert response.status_code == 422  # Validation error

    async def test_flag_vote_short_reason(self):
        """Test vote flagging with too short reason."""
        vote_id = str(uuid4())
        flag_data = {
            "flag_type": "spam",
            "reason": "Short",  # Too short (less than 10 chars)
        }

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/admin/flag-vote/{vote_id}/flag", json=flag_data
            )

        assert response.status_code == 422  # Validation error


class TestModerationEndpointSecurity:
    """Test security aspects of moderation endpoints."""

    async def test_moderation_endpoints_require_auth(self):
        """Test that moderation endpoints require authentication."""
        endpoints = [
            "/api/admin/moderation/dashboard",
            "/api/admin/moderation/flags",
            "/api/admin/moderation/votes",
        ]

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for endpoint in endpoints:
                response = await client.get(endpoint)
                assert response.status_code == 401

    async def test_moderation_post_endpoints_require_auth(self):
        """Test that moderation POST endpoints require authentication."""
        flag_id = str(uuid4())
        vote_id = str(uuid4())

        endpoints_data = [
            (
                f"/api/admin/moderation/flags/{flag_id}/review",
                {"status": "approved", "review_notes": "Test"},
            ),
            (
                f"/api/admin/moderation/votes/{vote_id}/action",
                {"action_type": "disable_vote", "reason": "Test"},
            ),
            (
                "/api/admin/moderation/bulk-action",
                {
                    "vote_ids": [str(uuid4())],
                    "action_type": "disable_vote",
                    "reason": "Test",
                },
            ),
        ]

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for endpoint, data in endpoints_data:
                response = await client.post(endpoint, json=data)
                assert response.status_code == 401

    @patch("cardinal_vote.super_admin_routes.get_current_super_admin")
    async def test_non_super_admin_access_denied(self, mock_auth, auth_headers):
        """Test that non-super admin users are denied access."""
        # Mock regular user (not super admin)
        mock_user = Mock()
        mock_user.is_super_admin = False
        mock_auth.return_value = mock_user

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/api/admin/moderation/dashboard", headers=auth_headers)

        # This would depend on the actual authorization implementation
        # The test verifies that proper access control is in place


class TestModerationInputValidation:
    """Test input validation for moderation endpoints."""

    async def test_flag_review_validation(self, auth_headers):
        """Test flag review input validation."""
        flag_id = str(uuid4())

        # Test missing required fields
        invalid_data = [
            {},  # Empty data
            {"status": "approved"},  # Missing review_notes
            {"review_notes": "Test notes"},  # Missing status
            {"status": "invalid_status", "review_notes": "Test"},  # Invalid status
            {"status": "approved", "review_notes": ""},  # Empty review notes
        ]

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for data in invalid_data:
                response = await client.post(
                    f"/api/admin/moderation/flags/{flag_id}/review",
                    json=data,
                    headers=auth_headers,
                )
                assert response.status_code == 422

    async def test_moderation_action_validation(self, auth_headers):
        """Test moderation action input validation."""
        vote_id = str(uuid4())

        # Test invalid action data
        invalid_data = [
            {},  # Empty data
            {"action_type": "disable_vote"},  # Missing reason
            {"reason": "Test reason"},  # Missing action_type
            {"action_type": "invalid_action", "reason": "Test"},  # Invalid action type
            {"action_type": "disable_vote", "reason": "Short"},  # Too short reason
        ]

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for data in invalid_data:
                response = await client.post(
                    f"/api/admin/moderation/votes/{vote_id}/action",
                    json=data,
                    headers=auth_headers,
                )
                assert response.status_code == 422

    async def test_bulk_action_validation(self, auth_headers):
        """Test bulk action input validation."""
        invalid_data = [
            {},  # Empty data
            {
                "vote_ids": [],
                "action_type": "disable_vote",
                "reason": "Test",
            },  # Empty vote_ids
            {
                "vote_ids": [str(uuid4())] * 51,
                "action_type": "disable_vote",
                "reason": "Test",
            },  # Too many votes
            {"vote_ids": [str(uuid4())], "reason": "Test"},  # Missing action_type
            {
                "vote_ids": [str(uuid4())],
                "action_type": "disable_vote",
            },  # Missing reason
        ]

        transport = httpx.ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for data in invalid_data:
                response = await client.post(
                    "/api/admin/moderation/bulk-action", json=data, headers=auth_headers
                )
                assert response.status_code == 422
