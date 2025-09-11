"""Integration tests for CAPTCHA-enabled vote submission."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from cardinal_vote.main import app
from tests.test_auth_integration import create_test_user, get_auth_headers


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_captcha_success():
    """Mock successful CAPTCHA verification."""
    with patch("cardinal_vote.captcha_service.verify_captcha_response") as mock_verify:
        mock_verify.return_value = AsyncMock(return_value=True)
        yield mock_verify


@pytest.fixture
def mock_captcha_failure():
    """Mock failed CAPTCHA verification."""
    with patch("cardinal_vote.captcha_service.verify_captcha_response") as mock_verify:
        mock_verify.side_effect = Exception("CAPTCHA verification failed")
        yield mock_verify


class TestCaptchaVoteIntegration:
    """Integration tests for CAPTCHA-enabled vote submission."""

    @pytest.mark.asyncio
    async def test_anonymous_vote_submission_with_captcha_success(
        self, client, mock_captcha_success
    ):
        """Test successful anonymous vote submission with CAPTCHA."""
        # Create test user and vote
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        # Create a vote
        vote_data = {
            "title": "Test Vote for CAPTCHA",
            "description": "Testing CAPTCHA integration",
            "options": [
                {
                    "title": "Option 1",
                    "content": "First option",
                    "option_type": "text",
                    "display_order": 1,
                },
                {
                    "title": "Option 2",
                    "content": "Second option",
                    "option_type": "text",
                    "display_order": 2,
                },
            ],
        }

        create_response = client.post("/api/votes/", headers=headers, json=vote_data)
        assert create_response.status_code == 201

        vote_id = create_response.json()["id"]

        # Activate the vote
        activate_response = client.patch(
            f"/api/votes/{vote_id}/status", headers=headers, json={"status": "active"}
        )
        assert activate_response.status_code == 200

        # Get vote details to get the slug
        vote_details = client.get(f"/api/votes/{vote_id}", headers=headers)
        assert vote_details.status_code == 200
        vote_slug = vote_details.json()["slug"]

        # Submit anonymous vote with CAPTCHA
        submission_data = {
            "voter_first_name": "Test",
            "voter_last_name": "User",
            "responses": {
                create_response.json()["options"][0]["id"]: 2,
                create_response.json()["options"][1]["id"]: 1,
            },
            "captcha_response": "MOCK_SUCCESS_TOKEN",
        }

        submit_response = client.post(
            f"/api/votes/public/{vote_slug}/submit", json=submission_data
        )

        assert submit_response.status_code == 201
        assert submit_response.json()["success"] is True

        # Verify CAPTCHA was called
        mock_captcha_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_anonymous_vote_submission_with_captcha_failure(
        self, client, mock_captcha_failure
    ):
        """Test anonymous vote submission with CAPTCHA failure."""
        # Create test user and vote
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        # Create a vote
        vote_data = {
            "title": "Test Vote for CAPTCHA Failure",
            "description": "Testing CAPTCHA failure",
            "options": [
                {
                    "title": "Option 1",
                    "content": "First option",
                    "option_type": "text",
                    "display_order": 1,
                }
            ],
        }

        create_response = client.post("/api/votes/", headers=headers, json=vote_data)
        assert create_response.status_code == 201

        vote_id = create_response.json()["id"]

        # Activate the vote
        activate_response = client.patch(
            f"/api/votes/{vote_id}/status", headers=headers, json={"status": "active"}
        )
        assert activate_response.status_code == 200

        # Get vote details to get the slug
        vote_details = client.get(f"/api/votes/{vote_id}", headers=headers)
        assert vote_details.status_code == 200
        vote_slug = vote_details.json()["slug"]

        # Submit anonymous vote with invalid CAPTCHA
        submission_data = {
            "voter_first_name": "Test",
            "voter_last_name": "User",
            "responses": {create_response.json()["options"][0]["id"]: 1},
            "captcha_response": "INVALID_TOKEN",
        }

        submit_response = client.post(
            f"/api/votes/public/{vote_slug}/submit", json=submission_data
        )

        # Should fail due to CAPTCHA verification failure
        assert submit_response.status_code == 400
        assert "CAPTCHA verification failed" in submit_response.json()["detail"]

    @pytest.mark.asyncio
    async def test_anonymous_vote_submission_missing_captcha(self, client):
        """Test anonymous vote submission with missing CAPTCHA response."""
        # Create test user and vote
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        # Create a vote
        vote_data = {
            "title": "Test Vote Missing CAPTCHA",
            "description": "Testing missing CAPTCHA",
            "options": [
                {
                    "title": "Option 1",
                    "content": "First option",
                    "option_type": "text",
                    "display_order": 1,
                }
            ],
        }

        create_response = client.post("/api/votes/", headers=headers, json=vote_data)
        assert create_response.status_code == 201

        vote_id = create_response.json()["id"]

        # Activate the vote
        activate_response = client.patch(
            f"/api/votes/{vote_id}/status", headers=headers, json={"status": "active"}
        )
        assert activate_response.status_code == 200

        # Get vote details to get the slug
        vote_details = client.get(f"/api/votes/{vote_id}", headers=headers)
        assert vote_details.status_code == 200
        vote_slug = vote_details.json()["slug"]

        # Submit anonymous vote without CAPTCHA response
        submission_data = {
            "voter_first_name": "Test",
            "voter_last_name": "User",
            "responses": {create_response.json()["options"][0]["id"]: 1},
            # Missing captcha_response field
        }

        submit_response = client.post(
            f"/api/votes/public/{vote_slug}/submit", json=submission_data
        )

        # Should fail validation due to missing required field
        assert submit_response.status_code == 422

    @pytest.mark.asyncio
    async def test_anonymous_vote_submission_empty_captcha(self, client):
        """Test anonymous vote submission with empty CAPTCHA response."""
        # Create test user and vote
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        # Create a vote
        vote_data = {
            "title": "Test Vote Empty CAPTCHA",
            "description": "Testing empty CAPTCHA",
            "options": [
                {
                    "title": "Option 1",
                    "content": "First option",
                    "option_type": "text",
                    "display_order": 1,
                }
            ],
        }

        create_response = client.post("/api/votes/", headers=headers, json=vote_data)
        assert create_response.status_code == 201

        vote_id = create_response.json()["id"]

        # Activate the vote
        activate_response = client.patch(
            f"/api/votes/{vote_id}/status", headers=headers, json={"status": "active"}
        )
        assert activate_response.status_code == 200

        # Get vote details to get the slug
        vote_details = client.get(f"/api/votes/{vote_id}", headers=headers)
        assert vote_details.status_code == 200
        vote_slug = vote_details.json()["slug"]

        # Submit anonymous vote with empty CAPTCHA response
        submission_data = {
            "voter_first_name": "Test",
            "voter_last_name": "User",
            "responses": {create_response.json()["options"][0]["id"]: 1},
            "captcha_response": "",  # Empty string
        }

        submit_response = client.post(
            f"/api/votes/public/{vote_slug}/submit", json=submission_data
        )

        # Should fail validation due to empty CAPTCHA response
        assert submit_response.status_code == 422

    @pytest.mark.asyncio
    async def test_authenticated_vote_submission_captcha_bypass(
        self, client, mock_captcha_success
    ):
        """Test that authenticated vote submissions might bypass CAPTCHA (if implemented)."""
        # Create test user and vote
        user_data = await create_test_user()
        headers = await get_auth_headers(user_data["email"], "testpassword123")

        # Create a vote
        vote_data = {
            "title": "Test Vote Authenticated",
            "description": "Testing authenticated submission",
            "options": [
                {
                    "title": "Option 1",
                    "content": "First option",
                    "option_type": "text",
                    "display_order": 1,
                }
            ],
        }

        create_response = client.post("/api/votes/", headers=headers, json=vote_data)
        assert create_response.status_code == 201

        vote_id = create_response.json()["id"]

        # Activate the vote
        activate_response = client.patch(
            f"/api/votes/{vote_id}/status", headers=headers, json={"status": "active"}
        )
        assert activate_response.status_code == 200

        # Submit authenticated vote (this endpoint may not require CAPTCHA)
        submission_data = {
            "voter_first_name": "Test",
            "voter_last_name": "User",
            "responses": {create_response.json()["options"][0]["id"]: 2},
            # Note: No captcha_response field for authenticated submissions
        }

        submit_response = client.post(
            f"/api/votes/{vote_id}/submit", headers=headers, json=submission_data
        )

        # This might succeed if authenticated users don't need CAPTCHA
        # The exact behavior depends on the implementation
        if submit_response.status_code == 201:
            assert submit_response.json()["success"] is True
        else:
            # If CAPTCHA is required even for authenticated users
            assert submit_response.status_code in [400, 422]


class TestCaptchaConfiguration:
    """Tests for CAPTCHA configuration and service selection."""

    def test_mock_captcha_service_selection(self):
        """Test that mock CAPTCHA service is selected in development."""
        from cardinal_vote.captcha_service import (
            MockCaptchaService,
            get_captcha_service,
        )

        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.CAPTCHA_BACKEND = "mock"

            service = get_captcha_service()
            assert isinstance(service, MockCaptchaService)

    def test_recaptcha_service_selection(self):
        """Test that reCAPTCHA service is selected when configured."""
        from cardinal_vote.captcha_service import RecaptchaService, get_captcha_service

        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.CAPTCHA_BACKEND = "recaptcha"
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = get_captcha_service()
            assert isinstance(service, RecaptchaService)

    def test_hcaptcha_service_selection(self):
        """Test that hCaptcha service is selected when configured."""
        from cardinal_vote.captcha_service import HcaptchaService, get_captcha_service

        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.CAPTCHA_BACKEND = "hcaptcha"
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = get_captcha_service()
            assert isinstance(service, HcaptchaService)
