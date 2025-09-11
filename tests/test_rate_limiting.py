"""Tests for the rate limiting functionality."""

import time
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Response

from cardinal_vote.rate_limiting import (
    InMemoryRateLimiter,
    RateLimitMiddleware,
    create_rate_limit_middleware,
    get_rate_limiter,
)


class TestInMemoryRateLimiter:
    """Test cases for InMemoryRateLimiter class."""

    def test_init(self):
        """Test InMemoryRateLimiter initialization."""
        limiter = InMemoryRateLimiter()
        assert limiter._requests == {}
        assert limiter._cleanup_interval == 60
        assert limiter._last_cleanup <= time.time()

    def test_is_rate_limited_first_request(self):
        """Test rate limiting for first request."""
        limiter = InMemoryRateLimiter()

        is_limited, info = limiter.is_rate_limited(
            "127.0.0.1", "/api/test", max_requests=10, window_seconds=300
        )

        assert is_limited is False
        assert info["limit"] == 10
        assert info["remaining"] == 9  # -1 for current request
        assert info["window"] == 300

    def test_is_rate_limited_within_limit(self):
        """Test rate limiting when within limits."""
        limiter = InMemoryRateLimiter()

        # Record a few requests
        for _ in range(5):
            limiter.record_request("127.0.0.1", "/api/test")

        is_limited, info = limiter.is_rate_limited(
            "127.0.0.1", "/api/test", max_requests=10, window_seconds=300
        )

        assert is_limited is False
        assert info["remaining"] == 4  # 10 - 5 - 1 for current

    def test_is_rate_limited_exceeded(self):
        """Test rate limiting when limit exceeded."""
        limiter = InMemoryRateLimiter()

        # Record requests up to limit
        for _ in range(10):
            limiter.record_request("127.0.0.1", "/api/test")

        is_limited, info = limiter.is_rate_limited(
            "127.0.0.1", "/api/test", max_requests=10, window_seconds=300
        )

        assert is_limited is True
        assert info["remaining"] == 0

    def test_is_rate_limited_different_endpoints(self):
        """Test rate limiting for different endpoints."""
        limiter = InMemoryRateLimiter()

        # Record requests for one endpoint
        for _ in range(10):
            limiter.record_request("127.0.0.1", "/api/test1")

        # Check limit for different endpoint
        is_limited, info = limiter.is_rate_limited(
            "127.0.0.1", "/api/test2", max_requests=10, window_seconds=300
        )

        assert is_limited is False
        assert info["remaining"] == 9

    def test_is_rate_limited_different_ips(self):
        """Test rate limiting for different IP addresses."""
        limiter = InMemoryRateLimiter()

        # Record requests for one IP
        for _ in range(10):
            limiter.record_request("127.0.0.1", "/api/test")

        # Check limit for different IP
        is_limited, info = limiter.is_rate_limited(
            "192.168.1.1", "/api/test", max_requests=10, window_seconds=300
        )

        assert is_limited is False
        assert info["remaining"] == 9

    def test_is_rate_limited_window_expiry(self):
        """Test that old requests outside window don't count."""
        limiter = InMemoryRateLimiter()

        # Mock time to simulate old requests
        old_time = time.time() - 400  # 400 seconds ago

        # Add old requests manually
        limiter._requests["127.0.0.1"] = [(old_time, "/api/test")] * 10

        is_limited, info = limiter.is_rate_limited(
            "127.0.0.1", "/api/test", max_requests=5, window_seconds=300
        )

        # Old requests should not count (they're outside 300s window)
        assert is_limited is False

    def test_record_request(self):
        """Test request recording."""
        limiter = InMemoryRateLimiter()

        limiter.record_request("127.0.0.1", "/api/test")

        assert "127.0.0.1" in limiter._requests
        assert len(limiter._requests["127.0.0.1"]) == 1

        timestamp, endpoint = limiter._requests["127.0.0.1"][0]
        assert endpoint == "/api/test"
        assert timestamp <= time.time()

    def test_cleanup_old_requests(self):
        """Test cleanup of old requests."""
        limiter = InMemoryRateLimiter()

        # Add old requests
        old_time = time.time() - 3700  # Older than 1 hour
        limiter._requests["127.0.0.1"] = [(old_time, "/api/test")]
        limiter._requests["192.168.1.1"] = [(time.time(), "/api/test")]

        # Force cleanup
        limiter._last_cleanup = time.time() - 70  # Force cleanup
        limiter._cleanup_old_requests()

        # Old IP should be removed, new IP should remain
        assert "127.0.0.1" not in limiter._requests
        assert "192.168.1.1" in limiter._requests


class TestRateLimitMiddleware:
    """Test cases for RateLimitMiddleware class."""

    def test_init(self):
        """Test RateLimitMiddleware initialization."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()

        middleware = RateLimitMiddleware(app, rate_limiter)

        assert middleware.rate_limiter is rate_limiter
        assert middleware.rate_limits is not None
        assert "default" in middleware.rate_limits

    def test_get_endpoint_pattern_exact_match(self):
        """Test endpoint pattern matching for exact paths."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        pattern = middleware._get_endpoint_pattern("/api/auth/login")
        assert pattern == "/api/auth/login"

    def test_get_endpoint_pattern_wildcard_match(self):
        """Test endpoint pattern matching for wildcard paths."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        pattern = middleware._get_endpoint_pattern(
            "/api/votes/123e4567-e89b-12d3-a456-426614174000/submit"
        )
        assert pattern == "/api/votes/*/submit"

    def test_get_endpoint_pattern_default(self):
        """Test endpoint pattern matching for default case."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        pattern = middleware._get_endpoint_pattern("/some/unknown/path")
        assert pattern == "default"

    def test_get_client_ip_direct(self):
        """Test client IP extraction from direct connection."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        mock_client = Mock()
        mock_client.host = "127.0.0.1"

        request = Mock()
        request.headers = {}
        request.client = mock_client

        ip = middleware._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_get_client_ip_forwarded_for(self):
        """Test client IP extraction from X-Forwarded-For header."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        request = Mock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = None

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"  # Should take first IP

    def test_get_client_ip_real_ip(self):
        """Test client IP extraction from X-Real-IP header."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        request = Mock()
        request.headers = {"X-Real-IP": "192.168.1.2"}
        request.client = None

        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.2"

    def test_get_client_ip_fallback(self):
        """Test client IP extraction fallback."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        request = Mock()
        request.headers = {}
        request.client = None

        ip = middleware._get_client_ip(request)
        assert ip == "unknown"

    @pytest.mark.asyncio
    async def test_dispatch_health_check_skip(self):
        """Test that health checks skip rate limiting."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        request = Mock()
        request.url.path = "/api/health"

        call_next = AsyncMock(return_value=Response())

        await middleware.dispatch(request, call_next)

        assert call_next.called
        # Should not record any requests for health checks
        assert rate_limiter._requests == {}

    @pytest.mark.asyncio
    async def test_dispatch_static_files_skip(self):
        """Test that static files skip rate limiting."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        request = Mock()
        request.url.path = "/static/style.css"

        call_next = AsyncMock(return_value=Response())

        await middleware.dispatch(request, call_next)

        assert call_next.called
        # Should not record any requests for static files
        assert rate_limiter._requests == {}

    @pytest.mark.asyncio
    async def test_dispatch_within_limit(self):
        """Test dispatch when request is within rate limit."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        request = Mock()
        request.url.path = "/api/test"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        assert call_next.called
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_rate_limited(self):
        """Test dispatch when request is rate limited."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        request = Mock()
        request.url.path = "/api/test"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"

        # Pre-fill rate limiter to exceed limit
        for _ in range(100):
            rate_limiter.record_request("127.0.0.1", "default")

        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        # Should not call next middleware
        assert not call_next.called
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.body.decode()
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"


class TestGlobalFunctions:
    """Test cases for global functions."""

    def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns same instance."""
        # Clear any existing instance
        import cardinal_vote.rate_limiting

        cardinal_vote.rate_limiting._rate_limiter = None

        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2
        assert isinstance(limiter1, InMemoryRateLimiter)

    def test_create_rate_limit_middleware(self):
        """Test create_rate_limit_middleware function."""
        app = Mock()

        middleware = create_rate_limit_middleware(app)

        assert isinstance(middleware, RateLimitMiddleware)
        assert isinstance(middleware.rate_limiter, InMemoryRateLimiter)


class TestRateLimitConfiguration:
    """Test cases for rate limit configuration."""

    def test_rate_limits_voting_endpoints(self):
        """Test that voting endpoints have stricter limits."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        vote_config = middleware.rate_limits["/api/votes/*/submit"]
        anonymous_config = middleware.rate_limits["/api/votes/*/anonymous/submit"]

        assert vote_config["max_requests"] == 5
        assert vote_config["window_seconds"] == 300
        assert anonymous_config["max_requests"] == 3
        assert anonymous_config["window_seconds"] == 300

    def test_rate_limits_auth_endpoints(self):
        """Test that auth endpoints have moderate limits."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        login_config = middleware.rate_limits["/api/auth/login"]
        register_config = middleware.rate_limits["/api/auth/register"]

        assert login_config["max_requests"] == 10
        assert login_config["window_seconds"] == 300
        assert register_config["max_requests"] == 5
        assert register_config["window_seconds"] == 300

    def test_rate_limits_password_reset_endpoints(self):
        """Test that password reset endpoints have strict limits."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        reset_request_config = middleware.rate_limits[
            "/api/auth/request-password-reset"
        ]
        reset_config = middleware.rate_limits["/api/auth/reset-password"]

        assert reset_request_config["max_requests"] == 3
        assert reset_request_config["window_seconds"] == 600
        assert reset_config["max_requests"] == 3
        assert reset_config["window_seconds"] == 600

    def test_rate_limits_default_endpoints(self):
        """Test default rate limits."""
        app = Mock()
        rate_limiter = InMemoryRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter)

        default_config = middleware.rate_limits["default"]

        assert default_config["max_requests"] == 100
        assert default_config["window_seconds"] == 300
