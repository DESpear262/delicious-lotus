"""
Unit tests for Internal API Authentication Middleware.

Tests API key authentication, JWT token validation, rate limiting, and security.
"""

import time
from unittest.mock import MagicMock, patch

import jwt
import pytest
from app.config import Settings
from app.middleware.internal_auth import InternalAuthMiddleware
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


# Test fixtures
@pytest.fixture
def mock_settings():
    """Create mock settings with test API keys and JWT secret."""
    settings = Settings(
        internal_api_keys=["test-key-1", "test-key-2"],
        jwt_secret_key="test-secret-key",
        jwt_algorithm="HS256",
        jwt_expiration_minutes=60,
    )
    return settings


@pytest.fixture
def app_with_auth(mock_settings, mock_redis):
    """Create FastAPI app with authentication middleware."""
    app = FastAPI()

    # Set up exception handlers for the test app
    from app.middleware.exception_handlers import setup_exception_handlers

    setup_exception_handlers(app)

    # Add test endpoints first
    @app.get("/internal/v1/test")
    async def internal_endpoint():
        return {"message": "Internal API endpoint"}

    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    @app.get("/api/v1/public")
    async def public_endpoint():
        return {"message": "Public endpoint"}

    # Patch get_settings and Redis connection before adding middleware
    settings_patcher = patch(
        "app.middleware.internal_auth.get_settings", return_value=mock_settings
    )
    redis_patcher = patch(
        "app.middleware.internal_auth.get_redis_connection", return_value=mock_redis
    )

    settings_patcher.start()
    redis_patcher.start()

    # Add middleware after patching
    app.add_middleware(InternalAuthMiddleware, rate_limit_per_key=10)

    return app


@pytest.fixture
def client(app_with_auth):
    """Create test client with proper exception handling for Python 3.13."""
    # Use raise_server_exceptions=False to properly handle exceptions in middleware
    # This is needed for Python 3.13 where exceptions in anyio TaskGroups get wrapped in ExceptionGroup
    return TestClient(app_with_auth, raise_server_exceptions=False)


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    redis_mock = MagicMock()
    redis_mock.pipeline.return_value = redis_mock
    redis_mock.execute.return_value = [None, 0, None, None]
    redis_mock.zrange.return_value = []
    return redis_mock


class TestInternalAuthMiddleware:
    """Test cases for InternalAuthMiddleware."""

    def test_middleware_initialization(self, mock_settings):
        """Test middleware initializes correctly."""
        with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
            app = FastAPI()
            app.add_middleware(InternalAuthMiddleware, rate_limit_per_key=100)
            # Should initialize without errors
            assert app is not None

    def test_health_endpoint_bypasses_auth(self, client):
        """Test that health check endpoints bypass authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_public_endpoint_no_auth_required(self, client):
        """Test that non-internal endpoints don't require authentication."""
        response = client.get("/api/v1/public")
        assert response.status_code == 200
        assert response.json() == {"message": "Public endpoint"}

    def test_internal_endpoint_requires_auth(self, client):
        """Test that internal endpoints require authentication."""
        response = client.get("/internal/v1/test")
        assert response.status_code == 401
        assert "authentication required" in response.json()["message"].lower()

    def test_valid_api_key_authentication(self, client, mock_redis):
        """Test successful API key authentication."""
        with patch("app.middleware.internal_auth.get_redis_connection", return_value=mock_redis):
            response = client.get(
                "/internal/v1/test",
                headers={"X-API-Key": "test-key-1"},
            )
            assert response.status_code == 200
            assert response.json() == {"message": "Internal API endpoint"}

    def test_invalid_api_key_rejected(self, client):
        """Test that invalid API keys are rejected."""
        response = client.get(
            "/internal/v1/test",
            headers={"X-API-Key": "invalid-key"},
        )
        assert response.status_code == 401
        assert "invalid api key" in response.json()["message"].lower()

    def test_valid_jwt_token_authentication(self, client, mock_settings):
        """Test successful JWT token authentication."""
        # Create valid JWT token
        payload = {
            "sub": "test-service",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        response = client.get(
            "/internal/v1/test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Internal API endpoint"}

    def test_expired_jwt_token_rejected(self, client, mock_settings):
        """Test that expired JWT tokens are rejected."""
        # Create expired JWT token
        payload = {
            "sub": "test-service",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        response = client.get(
            "/internal/v1/test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert "invalid or expired" in response.json()["message"].lower()

    def test_invalid_jwt_token_rejected(self, client):
        """Test that invalid JWT tokens are rejected."""
        response = client.get(
            "/internal/v1/test",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        assert "invalid or expired" in response.json()["message"].lower()

    def test_jwt_token_wrong_secret_rejected(self, client, mock_settings):
        """Test that JWT tokens signed with wrong secret are rejected."""
        # Create token with wrong secret
        payload = {
            "sub": "test-service",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, "wrong-secret", algorithm=mock_settings.jwt_algorithm)

        response = client.get(
            "/internal/v1/test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_rate_limit_headers_included(self, client, mock_redis):
        """Test that rate limit headers are included in response."""
        mock_redis.execute.return_value = [None, 3, None, None]

        with patch("app.middleware.internal_auth.get_redis_connection", return_value=mock_redis):
            response = client.get(
                "/internal/v1/test",
                headers={"X-API-Key": "test-key-1"},
            )

            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_per_api_key_enforced(self, client, mock_redis):
        """Test that rate limiting is enforced per API key."""
        # Simulate rate limit exceeded
        mock_redis.execute.return_value = [None, 10, None, None]
        mock_redis.zrange.return_value = [(b"timestamp", int(time.time()) - 30)]

        with patch("app.middleware.internal_auth.get_redis_connection", return_value=mock_redis):
            response = client.get(
                "/internal/v1/test",
                headers={"X-API-Key": "test-key-1"},
            )

            assert response.status_code == 429
            assert "rate limit exceeded" in response.json()["message"].lower()

    def test_missing_authentication_rejected(self, client):
        """Test that requests without authentication are rejected."""
        response = client.get("/internal/v1/test")
        assert response.status_code == 401
        assert "authentication required" in response.json()["message"].lower()

    def test_malformed_bearer_token_rejected(self, client):
        """Test that malformed Bearer tokens are rejected."""
        response = client.get(
            "/internal/v1/test",
            headers={"Authorization": "Bearer"},
        )
        assert response.status_code == 401

    def test_multiple_api_keys_work(self, client, mock_redis):
        """Test that multiple configured API keys all work."""
        with patch("app.middleware.internal_auth.get_redis_connection", return_value=mock_redis):
            for api_key in ["test-key-1", "test-key-2"]:
                response = client.get(
                    "/internal/v1/test",
                    headers={"X-API-Key": api_key},
                )
                assert response.status_code == 200

    def test_redis_failure_allows_request(self, client):
        """Test that Redis failures fail open (allow request)."""
        # Mock Redis to raise exception
        failing_redis = MagicMock()
        failing_redis.pipeline.side_effect = Exception("Redis connection failed")

        with patch("app.middleware.internal_auth.get_redis_connection", return_value=failing_redis):
            response = client.get(
                "/internal/v1/test",
                headers={"X-API-Key": "test-key-1"},
            )
            # Should allow request even if Redis fails
            assert response.status_code == 200


class TestInternalAuthConfiguration:
    """Test cases for authentication configuration."""

    def test_no_api_keys_configured_rejects_requests(self):
        """Test that requests are rejected when no API keys are configured."""
        settings = Settings(
            internal_api_keys=[],
            jwt_secret_key="",
        )

        app = FastAPI()
        with patch("app.middleware.internal_auth.get_settings", return_value=settings):
            app.add_middleware(InternalAuthMiddleware)

        @app.get("/internal/v1/test")
        async def internal_endpoint():
            return {"message": "test"}

        client = TestClient(app)

        response = client.get(
            "/internal/v1/test",
            headers={"X-API-Key": "any-key"},
        )
        assert response.status_code == 401

    def test_no_jwt_secret_rejects_jwt_auth(self):
        """Test that JWT auth fails when no secret is configured."""
        settings = Settings(
            internal_api_keys=["test-key"],
            jwt_secret_key="",  # No JWT secret configured
        )

        app = FastAPI()
        with patch("app.middleware.internal_auth.get_settings", return_value=settings):
            app.add_middleware(InternalAuthMiddleware)

        @app.get("/internal/v1/test")
        async def internal_endpoint():
            return {"message": "test"}

        client = TestClient(app)

        # Try JWT auth without configured secret
        response = client.get(
            "/internal/v1/test",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 401


class TestInternalAuthHelpers:
    """Test cases for helper methods."""

    def test_should_authenticate_internal_paths(self, mock_settings):
        """Test that internal paths require authentication."""
        with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
            middleware = InternalAuthMiddleware(app=MagicMock(), rate_limit_per_key=10)

            request = MagicMock(spec=Request)
            request.url.path = "/internal/v1/test"

            assert middleware._should_authenticate(request) is True

    def test_should_authenticate_health_bypass(self, mock_settings):
        """Test that health checks bypass authentication."""
        with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
            middleware = InternalAuthMiddleware(app=MagicMock(), rate_limit_per_key=10)

            health_paths = ["/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"]
            for path in health_paths:
                request = MagicMock(spec=Request)
                request.url.path = path

                assert middleware._should_authenticate(request) is False

    def test_validate_api_key_success(self, mock_settings):
        """Test successful API key validation."""
        with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
            middleware = InternalAuthMiddleware(app=MagicMock(), rate_limit_per_key=10)

            assert middleware._validate_api_key("test-key-1") is True
            assert middleware._validate_api_key("test-key-2") is True

    def test_validate_api_key_failure(self, mock_settings):
        """Test failed API key validation."""
        with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
            middleware = InternalAuthMiddleware(app=MagicMock(), rate_limit_per_key=10)

            assert middleware._validate_api_key("invalid-key") is False
            assert middleware._validate_api_key("") is False

    def test_validate_jwt_token_success(self, mock_settings):
        """Test successful JWT token validation."""
        with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
            middleware = InternalAuthMiddleware(app=MagicMock(), rate_limit_per_key=10)

            payload = {
                "sub": "test-service",
                "exp": int(time.time()) + 3600,
            }
            token = jwt.encode(
                payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
            )

            result = middleware._validate_jwt_token(token)
            assert result is not None
            assert result["sub"] == "test-service"

    def test_validate_jwt_token_expired(self, mock_settings):
        """Test JWT token validation with expired token."""
        with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
            middleware = InternalAuthMiddleware(app=MagicMock(), rate_limit_per_key=10)

            payload = {
                "sub": "test-service",
                "exp": int(time.time()) - 3600,
            }
            token = jwt.encode(
                payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
            )

            result = middleware._validate_jwt_token(token)
            assert result is None
