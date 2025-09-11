"""Rate limiting middleware and utilities for the generalized voting platform."""

import logging
import time
from collections import defaultdict
from typing import Any, cast

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development and small-scale deployments."""

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        # Store: {ip_address: [(timestamp, endpoint), ...]}
        self._requests: dict[str, list[tuple[float, str]]] = defaultdict(list)
        self._cleanup_interval = 60  # seconds
        self._last_cleanup = time.time()

    def _cleanup_old_requests(self) -> None:
        """Clean up old request records to prevent memory buildup."""
        current_time = time.time()

        # Only cleanup every minute to avoid performance impact
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        cutoff_time = current_time - 3600  # Keep records for 1 hour max

        for ip in list(self._requests.keys()):
            # Filter out requests older than 1 hour
            self._requests[ip] = [
                (timestamp, endpoint)
                for timestamp, endpoint in self._requests[ip]
                if timestamp > cutoff_time
            ]

            # Remove empty IP entries
            if not self._requests[ip]:
                del self._requests[ip]

        self._last_cleanup = current_time

    def is_rate_limited(
        self,
        ip_address: str,
        endpoint: str,
        max_requests: int = 60,
        window_seconds: int = 300,  # 5 minutes
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if an IP address is rate limited for a specific endpoint.

        Args:
            ip_address: Client IP address
            endpoint: API endpoint path
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited, rate_limit_info)
        """
        self._cleanup_old_requests()

        current_time = time.time()
        window_start = current_time - window_seconds

        # Get requests for this IP and endpoint within the window
        requests_in_window = [
            timestamp
            for timestamp, ep in self._requests[ip_address]
            if ep == endpoint and timestamp > window_start
        ]

        request_count = len(requests_in_window)
        is_limited = request_count >= max_requests

        # Calculate reset time (when oldest request in window expires)
        reset_time = int(current_time + window_seconds)
        if requests_in_window:
            oldest_request = min(requests_in_window)
            reset_time = int(oldest_request + window_seconds)

        rate_limit_info = {
            "limit": max_requests,
            "remaining": max(
                0, max_requests - request_count - 1
            ),  # -1 for current request
            "reset": reset_time,
            "window": window_seconds,
        }

        return is_limited, rate_limit_info

    def record_request(self, ip_address: str, endpoint: str) -> None:
        """Record a request for rate limiting tracking."""
        current_time = time.time()
        self._requests[ip_address].append((current_time, endpoint))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(self, app: Any, rate_limiter: InMemoryRateLimiter) -> None:
        """Initialize rate limiting middleware."""
        super().__init__(app)
        self.rate_limiter = rate_limiter

        # Define rate limits for different endpoint patterns
        self.rate_limits = {
            # Voting endpoints - stricter limits
            "/api/votes/*/submit": {
                "max_requests": 5,
                "window_seconds": 300,
            },  # 5 votes per 5 min
            "/api/votes/*/anonymous/submit": {
                "max_requests": 3,
                "window_seconds": 300,
            },  # 3 anonymous votes per 5 min
            # Image upload endpoints - moderate limits
            "/api/votes/images/upload": {
                "max_requests": 20,
                "window_seconds": 300,
            },  # 20 uploads per 5 min
            # Authentication endpoints - moderate limits
            "/api/auth/register": {
                "max_requests": 5,
                "window_seconds": 300,
            },  # 5 registrations per 5 min
            "/api/auth/login": {
                "max_requests": 10,
                "window_seconds": 300,
            },  # 10 login attempts per 5 min
            "/api/auth/token": {
                "max_requests": 10,
                "window_seconds": 300,
            },  # 10 token requests per 5 min
            # Password reset - stricter limits
            "/api/auth/request-password-reset": {
                "max_requests": 3,
                "window_seconds": 600,
            },  # 3 per 10 min
            "/api/auth/reset-password": {
                "max_requests": 3,
                "window_seconds": 600,
            },  # 3 per 10 min
            # General API endpoints - more lenient
            "default": {
                "max_requests": 100,
                "window_seconds": 300,
            },  # 100 requests per 5 min
        }

    def _get_endpoint_pattern(self, path: str) -> str:
        """Get the rate limit pattern for a given path."""
        # Check for exact matches first
        for pattern in self.rate_limits:
            if pattern == "default":
                continue

            # Simple wildcard matching for vote IDs and slugs
            if "*" in pattern:
                pattern_parts = pattern.split("*")
                if len(pattern_parts) == 2:
                    prefix, suffix = pattern_parts
                    if path.startswith(prefix) and path.endswith(suffix):
                        return pattern
            elif path == pattern:
                return pattern

        # Return default if no specific pattern matches
        return "default"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request through rate limiting."""
        # Skip rate limiting for health checks and static files
        if request.url.path.startswith(("/api/health", "/static", "/uploads")):
            return cast(Response, await call_next(request))

        client_ip = self._get_client_ip(request)
        endpoint_pattern = self._get_endpoint_pattern(request.url.path)

        # Get rate limit configuration for this endpoint
        rate_config = self.rate_limits.get(
            endpoint_pattern, self.rate_limits["default"]
        )
        max_requests = rate_config["max_requests"]
        window_seconds = rate_config["window_seconds"]

        # Check if request should be rate limited
        is_limited, rate_info = self.rate_limiter.is_rate_limited(
            client_ip, endpoint_pattern, max_requests, window_seconds
        )

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on endpoint {endpoint_pattern}. "
                f"Limit: {max_requests} per {window_seconds}s"
            )

            # Return 429 Too Many Requests with rate limit headers
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(window_seconds),
                },
            )

        # Record the request for rate limiting
        self.rate_limiter.record_request(client_ip, endpoint_pattern)

        # Process the request
        response = cast(Response, await call_next(request))

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

        return response


# Global rate limiter instance
_rate_limiter: InMemoryRateLimiter | None = None


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


def create_rate_limit_middleware(app: Any) -> RateLimitMiddleware:
    """Create rate limiting middleware for the application."""
    rate_limiter = get_rate_limiter()
    return RateLimitMiddleware(app, rate_limiter)
