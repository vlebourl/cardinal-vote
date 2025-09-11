"""Tests for the CAPTCHA service functionality."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi import HTTPException

from cardinal_vote.captcha_service import (
    CaptchaServiceBase,
    HcaptchaService,
    MockCaptchaService,
    RecaptchaService,
    get_captcha_service,
    verify_captcha_response,
)


class TestCaptchaServiceBase:
    """Test cases for CaptchaServiceBase abstract class."""

    def test_captcha_service_base_is_abstract(self):
        """Test that CaptchaServiceBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CaptchaServiceBase()


class TestMockCaptchaService:
    """Test cases for MockCaptchaService."""

    def test_mock_captcha_service_init(self):
        """Test MockCaptchaService initialization."""
        service = MockCaptchaService()
        assert isinstance(service, CaptchaServiceBase)

    @pytest.mark.asyncio
    async def test_verify_captcha_success(self):
        """Test successful CAPTCHA verification."""
        service = MockCaptchaService()
        result = await service.verify_captcha("valid_token", "127.0.0.1")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_captcha_failure(self):
        """Test failed CAPTCHA verification with special token."""
        service = MockCaptchaService()
        result = await service.verify_captcha("FAIL_TEST", "127.0.0.1")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_without_ip(self):
        """Test CAPTCHA verification without IP address."""
        service = MockCaptchaService()
        result = await service.verify_captcha("valid_token")
        assert result is True


class TestRecaptchaService:
    """Test cases for RecaptchaService."""

    def test_recaptcha_service_init_with_secret(self):
        """Test RecaptchaService initialization with secret key."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = RecaptchaService()
            assert service.secret_key == "test_secret"
            assert service.site_key == "test_site_key"

    def test_recaptcha_service_init_without_secret(self):
        """Test RecaptchaService initialization without secret key raises error."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = ""

            with pytest.raises(ValueError) as exc_info:
                RecaptchaService()

            assert "RECAPTCHA_SECRET_KEY is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_captcha_success(self):
        """Test successful reCAPTCHA verification."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = RecaptchaService()

            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is True

    @pytest.mark.asyncio
    async def test_verify_captcha_empty_response(self):
        """Test CAPTCHA verification with empty response."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = RecaptchaService()
            result = await service.verify_captcha("", "127.0.0.1")
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_api_failure(self):
        """Test CAPTCHA verification with API failure."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = RecaptchaService()

            # Mock failed API response
            mock_response = Mock()
            mock_response.status_code = 500

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_verification_failure(self):
        """Test CAPTCHA verification with verification failure."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = RecaptchaService()

            # Mock verification failure response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error-codes": ["invalid-input-response"],
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await service.verify_captcha("invalid_token", "127.0.0.1")
                assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_timeout(self):
        """Test CAPTCHA verification with timeout."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = RecaptchaService()

            with patch("httpx.AsyncClient") as mock_client:
                from httpx import TimeoutException

                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=TimeoutException("Timeout")
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_request_error(self):
        """Test CAPTCHA verification with request error."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = RecaptchaService()

            with patch("httpx.AsyncClient") as mock_client:
                from httpx import RequestError

                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=RequestError("Connection failed")
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is False


class TestHcaptchaService:
    """Test cases for HcaptchaService."""

    def test_hcaptcha_service_init_with_secret(self):
        """Test HcaptchaService initialization with secret key."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()
            assert service.secret_key == "test_secret"
            assert service.site_key == "test_site_key"

    def test_hcaptcha_service_init_without_secret(self):
        """Test HcaptchaService initialization without secret key raises error."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = ""

            with pytest.raises(ValueError) as exc_info:
                HcaptchaService()

            assert "HCAPTCHA_SECRET_KEY is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_captcha_success(self):
        """Test successful hCaptcha verification."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()

            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is True

    @pytest.mark.asyncio
    async def test_verify_captcha_timeout(self):
        """Test hCaptcha verification timeout."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=httpx.TimeoutException("Timeout")
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_request_error(self):
        """Test hCaptcha verification request error."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    side_effect=httpx.RequestError("Network error")
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_http_error(self):
        """Test hCaptcha verification HTTP error response."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()

            mock_response = Mock()
            mock_response.status_code = 500

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_json_error(self):
        """Test hCaptcha verification with invalid JSON response."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await service.verify_captcha("valid_token", "127.0.0.1")
                assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_empty_response(self):
        """Test hCaptcha verification with empty response."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()

            result = await service.verify_captcha("", "127.0.0.1")
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_failure_with_error_codes(self):
        """Test hCaptcha verification failure with error codes."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = HcaptchaService()

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error-codes": ["invalid-input-response", "timeout-or-duplicate"],
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                    return_value=mock_response
                )

                result = await service.verify_captcha("invalid_token", "127.0.0.1")
                assert result is False


class TestGetCaptchaService:
    """Test cases for get_captcha_service function."""

    def test_get_captcha_service_mock(self):
        """Test get_captcha_service returns MockCaptchaService for 'mock' backend."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.CAPTCHA_BACKEND = "mock"

            service = get_captcha_service()
            assert isinstance(service, MockCaptchaService)

    def test_get_captcha_service_recaptcha(self):
        """Test get_captcha_service returns RecaptchaService for 'recaptcha' backend."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.CAPTCHA_BACKEND = "recaptcha"
            mock_settings.RECAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.RECAPTCHA_SITE_KEY = "test_site_key"

            service = get_captcha_service()
            assert isinstance(service, RecaptchaService)

    def test_get_captcha_service_hcaptcha(self):
        """Test get_captcha_service returns HcaptchaService for 'hcaptcha' backend."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.CAPTCHA_BACKEND = "hcaptcha"
            mock_settings.HCAPTCHA_SECRET_KEY = "test_secret"
            mock_settings.HCAPTCHA_SITE_KEY = "test_site_key"

            service = get_captcha_service()
            assert isinstance(service, HcaptchaService)

    def test_get_captcha_service_unknown_backend(self):
        """Test get_captcha_service returns MockCaptchaService for unknown backend."""
        with patch("cardinal_vote.captcha_service.settings") as mock_settings:
            mock_settings.CAPTCHA_BACKEND = "unknown"

            service = get_captcha_service()
            assert isinstance(service, MockCaptchaService)


class TestVerifyCaptchaResponse:
    """Test cases for verify_captcha_response function."""

    @pytest.mark.asyncio
    async def test_verify_captcha_response_success(self):
        """Test successful CAPTCHA response verification."""
        with patch(
            "cardinal_vote.captcha_service.get_captcha_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.verify_captcha = AsyncMock(return_value=True)
            mock_get_service.return_value = mock_service

            result = await verify_captcha_response(
                "valid_token", "127.0.0.1", raise_on_failure=False
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_captcha_response_failure_no_raise(self):
        """Test failed CAPTCHA response verification without raising exception."""
        with patch(
            "cardinal_vote.captcha_service.get_captcha_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.verify_captcha = AsyncMock(return_value=False)
            mock_get_service.return_value = mock_service

            result = await verify_captcha_response(
                "invalid_token", "127.0.0.1", raise_on_failure=False
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_response_failure_with_raise(self):
        """Test failed CAPTCHA response verification with raising exception."""
        with patch(
            "cardinal_vote.captcha_service.get_captcha_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.verify_captcha = AsyncMock(return_value=False)
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await verify_captcha_response(
                    "invalid_token", "127.0.0.1", raise_on_failure=True
                )

            assert exc_info.value.status_code == 400
            assert "CAPTCHA verification failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_captcha_response_service_error_no_raise(self):
        """Test CAPTCHA service error without raising exception."""
        with patch(
            "cardinal_vote.captcha_service.get_captcha_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.verify_captcha = AsyncMock(
                side_effect=Exception("Service error")
            )
            mock_get_service.return_value = mock_service

            result = await verify_captcha_response(
                "token", "127.0.0.1", raise_on_failure=False
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_captcha_response_service_error_with_raise(self):
        """Test CAPTCHA service error with raising exception."""
        with patch(
            "cardinal_vote.captcha_service.get_captcha_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.verify_captcha = AsyncMock(
                side_effect=Exception("Service error")
            )
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await verify_captcha_response(
                    "token", "127.0.0.1", raise_on_failure=True
                )

            assert exc_info.value.status_code == 500
            assert "CAPTCHA verification service unavailable" in str(
                exc_info.value.detail
            )

    @pytest.mark.asyncio
    async def test_verify_captcha_response_default_raise_on_failure(self):
        """Test that raise_on_failure defaults to True."""
        with patch(
            "cardinal_vote.captcha_service.get_captcha_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.verify_captcha = AsyncMock(return_value=False)
            mock_get_service.return_value = mock_service

            with pytest.raises(HTTPException) as exc_info:
                await verify_captcha_response("invalid_token", "127.0.0.1")

            assert exc_info.value.status_code == 400
            assert "CAPTCHA verification failed" in str(exc_info.value.detail)
