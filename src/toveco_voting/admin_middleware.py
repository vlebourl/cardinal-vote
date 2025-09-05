"""Admin middleware for authentication and security in the ToVéCo voting platform."""

import logging

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from .admin_auth import AdminAuthManager

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class AdminSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for admin security features like CSRF protection and session cleanup."""

    def __init__(self, app, auth_manager: AdminAuthManager):
        super().__init__(app)
        self.auth_manager = auth_manager
        self._cleanup_counter = 0

    async def dispatch(self, request: Request, call_next):
        """Process request with security checks."""
        # Periodic session cleanup (every 100 requests)
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            try:
                cleaned = self.auth_manager.cleanup_expired_sessions()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired sessions")
            except Exception as e:
                logger.error(f"Session cleanup failed: {e}")

        # Add security headers
        response = await call_next(request)

        # Security headers for admin pages
        if request.url.path.startswith("/admin"):
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, proxy-revalidate"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


def get_client_ip(request: Request) -> str:
    """Get client IP address, considering proxies."""
    # Check for forwarded headers (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection
    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def get_user_agent(request: Request) -> str:
    """Get user agent string."""
    return request.headers.get("User-Agent", "Unknown")


class AdminAuthDependency:
    """Dependency class for admin authentication."""

    def __init__(self, auth_manager: AdminAuthManager):
        self.auth_manager = auth_manager

    def __call__(
        self,
        request: Request,
        session_token: str | None = Cookie(None, alias="admin_session"),
    ) -> dict:
        """
        Dependency that validates admin session.
        Returns user info if authenticated, raises HTTPException otherwise.
        """
        if not session_token:
            logger.debug("No admin session token found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        ip_address = get_client_ip(request)
        user_info = self.auth_manager.validate_session(session_token, ip_address)

        if not user_info:
            logger.warning(f"Invalid session token from IP: {ip_address}")
            # Clear the invalid cookie by raising an exception that will be handled
            # by the admin routes to redirect to login
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        logger.debug(f"Authenticated admin user: {user_info['username']}")
        return user_info


class AdminAuthOptionalDependency:
    """Optional dependency class for admin authentication (for pages that can show different content)."""

    def __init__(self, auth_manager: AdminAuthManager):
        self.auth_manager = auth_manager

    def __call__(
        self,
        request: Request,
        session_token: str | None = Cookie(None, alias="admin_session"),
    ) -> dict | None:
        """
        Optional dependency that validates admin session.
        Returns user info if authenticated, None otherwise (no exception raised).
        """
        if not session_token:
            return None

        ip_address = get_client_ip(request)
        user_info = self.auth_manager.validate_session(session_token, ip_address)

        if user_info:
            logger.debug(
                f"Optionally authenticated admin user: {user_info['username']}"
            )

        return user_info


def create_admin_dependencies(
    auth_manager: AdminAuthManager,
) -> tuple[AdminAuthDependency, AdminAuthOptionalDependency]:
    """
    Factory function to create admin authentication dependencies.
    Returns tuple of (required_auth, optional_auth).
    """
    required_auth = AdminAuthDependency(auth_manager)
    optional_auth = AdminAuthOptionalDependency(auth_manager)
    return required_auth, optional_auth


# CSRF Protection utilities
def generate_csrf_token(session_data: dict) -> str:
    """Generate a CSRF token for the given session."""
    import hashlib
    import hmac
    import secrets

    # Create a token based on session ID and a random value
    random_part = secrets.token_urlsafe(16)
    session_id = session_data.get("session_id", "")

    # Create HMAC with session secret
    message = f"{session_id}:{random_part}".encode()
    csrf_token = hmac.new(
        key=session_id.encode(), msg=message, digestmod=hashlib.sha256
    ).hexdigest()

    return f"{random_part}:{csrf_token}"


def validate_csrf_token(token: str, session_data: dict) -> bool:
    """Validate a CSRF token against the session."""
    if not token or ":" not in token:
        return False

    try:
        random_part, csrf_token = token.rsplit(":", 1)
        session_id = session_data.get("session_id", "")

        # Recreate the expected token
        import hashlib
        import hmac

        message = f"{session_id}:{random_part}".encode()
        expected_token = hmac.new(
            key=session_id.encode(), msg=message, digestmod=hashlib.sha256
        ).hexdigest()

        # Compare tokens (constant time comparison)
        return hmac.compare_digest(csrf_token, expected_token)

    except Exception as e:
        logger.error(f"CSRF token validation error: {e}")
        return False


class CSRFProtectionDependency:
    """Dependency for CSRF protection on admin forms."""

    def __call__(
        self,
        request: Request,
        admin_user: dict = Depends(
            lambda: None
        ),  # Will be replaced with actual auth dependency
        csrf_token: str = None,
    ) -> bool:
        """
        Validate CSRF token for POST/PUT/DELETE requests.
        Returns True if valid, raises HTTPException otherwise.
        """
        # Skip CSRF for GET requests
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Skip if not an admin request
        if not admin_user:
            return True

        # Get CSRF token from form data or headers
        if not csrf_token:
            # Try to get from form data
            if request.headers.get("content-type", "").startswith(
                "application/x-www-form-urlencoded"
            ):
                # This would need to be handled in the route itself
                pass
            # Try to get from headers
            csrf_token = request.headers.get("X-CSRF-Token")

        if not csrf_token or not validate_csrf_token(csrf_token, admin_user):
            logger.warning(f"CSRF validation failed for {request.url}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed"
            )

        return True


# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self._attempts = {}

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if the request is within rate limits."""
        import time

        now = time.time()
        window_start = now - window_seconds

        if key not in self._attempts:
            self._attempts[key] = []

        # Remove old attempts
        self._attempts[key] = [
            attempt for attempt in self._attempts[key] if attempt > window_start
        ]

        # Check if within limit
        if len(self._attempts[key]) >= limit:
            return False

        # Record this attempt
        self._attempts[key].append(now)
        return True

    def clear_attempts(self, key: str) -> None:
        """Clear attempts for a key (e.g., after successful login)."""
        if key in self._attempts:
            del self._attempts[key]


# Global rate limiter instance
rate_limiter = RateLimiter()
