"""CAPTCHA service for the generalized voting platform."""

import logging
from abc import ABC, abstractmethod

import httpx
from fastapi import HTTPException, status

from .config import settings

logger = logging.getLogger(__name__)


class CaptchaServiceBase(ABC):
    """Abstract base class for CAPTCHA services."""

    @abstractmethod
    async def verify_captcha(
        self, captcha_response: str, user_ip: str | None = None
    ) -> bool:
        """Verify a CAPTCHA response."""
        pass


class MockCaptchaService(CaptchaServiceBase):
    """Mock CAPTCHA service for development - always returns True."""

    def __init__(self) -> None:
        """Initialize mock CAPTCHA service."""
        logger.info("Initialized Mock CAPTCHA Service (Development Mode)")

    async def verify_captcha(
        self, captcha_response: str, user_ip: str | None = None
    ) -> bool:
        """Verify CAPTCHA response (mock - always returns True in development)."""
        logger.info(f"Mock CAPTCHA verification - Response: {captcha_response[:20]}...")

        # In development, we can simulate different scenarios
        if captcha_response == "FAIL_TEST":
            return False

        return True


class RecaptchaService(CaptchaServiceBase):
    """Google reCAPTCHA v2 service implementation."""

    def __init__(self) -> None:
        """Initialize reCAPTCHA service."""
        self.secret_key = getattr(settings, "RECAPTCHA_SECRET_KEY", "")
        self.site_key = getattr(settings, "RECAPTCHA_SITE_KEY", "")
        self.verify_url = "https://www.google.com/recaptcha/api/siteverify"

        if not self.secret_key:
            raise ValueError("RECAPTCHA_SECRET_KEY is required for reCAPTCHA service")

        logger.info("Initialized Google reCAPTCHA Service")

    async def verify_captcha(
        self, captcha_response: str, user_ip: str | None = None
    ) -> bool:
        """Verify reCAPTCHA response with Google's API."""
        if not captcha_response:
            logger.warning("Empty CAPTCHA response received")
            return False

        try:
            # Prepare verification data
            verify_data = {
                "secret": self.secret_key,
                "response": captcha_response,
            }

            if user_ip:
                verify_data["remoteip"] = user_ip

            # Make request to reCAPTCHA API
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.verify_url, data=verify_data)

                if response.status_code != 200:
                    logger.error(
                        f"reCAPTCHA API returned status {response.status_code}"
                    )
                    return False

                result = response.json()

                # Check verification result
                success: bool = bool(result.get("success", False))

                if not success:
                    error_codes = result.get("error-codes", [])
                    logger.warning(f"reCAPTCHA verification failed: {error_codes}")

                return success

        except httpx.TimeoutException:
            logger.error("reCAPTCHA verification timed out")
            return False
        except httpx.RequestError as e:
            logger.error(f"reCAPTCHA verification request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during reCAPTCHA verification: {e}")
            return False


class HcaptchaService(CaptchaServiceBase):
    """hCaptcha service implementation."""

    def __init__(self) -> None:
        """Initialize hCaptcha service."""
        self.secret_key = getattr(settings, "HCAPTCHA_SECRET_KEY", "")
        self.site_key = getattr(settings, "HCAPTCHA_SITE_KEY", "")
        self.verify_url = "https://hcaptcha.com/siteverify"

        if not self.secret_key:
            raise ValueError("HCAPTCHA_SECRET_KEY is required for hCaptcha service")

        logger.info("Initialized hCaptcha Service")

    async def verify_captcha(
        self, captcha_response: str, user_ip: str | None = None
    ) -> bool:
        """Verify hCaptcha response with hCaptcha's API."""
        if not captcha_response:
            logger.warning("Empty CAPTCHA response received")
            return False

        try:
            # Prepare verification data
            verify_data = {
                "secret": self.secret_key,
                "response": captcha_response,
            }

            if user_ip:
                verify_data["remoteip"] = user_ip

            # Make request to hCaptcha API
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.verify_url, data=verify_data)

                if response.status_code != 200:
                    logger.error(f"hCaptcha API returned status {response.status_code}")
                    return False

                result = response.json()

                # Check verification result
                success: bool = bool(result.get("success", False))

                if not success:
                    error_codes = result.get("error-codes", [])
                    logger.warning(f"hCaptcha verification failed: {error_codes}")

                return success

        except httpx.TimeoutException:
            logger.error("hCaptcha verification timed out")
            return False
        except httpx.RequestError as e:
            logger.error(f"hCaptcha verification request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during hCaptcha verification: {e}")
            return False


def get_captcha_service() -> CaptchaServiceBase:
    """Get the appropriate CAPTCHA service based on configuration."""
    captcha_backend = getattr(settings, "CAPTCHA_BACKEND", "mock")

    if captcha_backend == "recaptcha":
        return RecaptchaService()
    elif captcha_backend == "hcaptcha":
        return HcaptchaService()
    else:
        return MockCaptchaService()


async def verify_captcha_response(
    captcha_response: str, user_ip: str | None = None, raise_on_failure: bool = True
) -> bool:
    """
    Convenience function to verify CAPTCHA response.

    Args:
        captcha_response: The CAPTCHA response token from the frontend
        user_ip: Optional user IP address for additional verification
        raise_on_failure: Whether to raise HTTPException on failure

    Returns:
        bool: True if CAPTCHA is valid, False otherwise

    Raises:
        HTTPException: If raise_on_failure is True and CAPTCHA verification fails
    """
    captcha_service = get_captcha_service()

    try:
        is_valid = await captcha_service.verify_captcha(captcha_response, user_ip)

        if not is_valid and raise_on_failure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CAPTCHA verification failed. Please try again.",
            )

        return is_valid

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CAPTCHA verification error: {e}")

        if raise_on_failure:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CAPTCHA verification service unavailable",
            ) from e

        return False
