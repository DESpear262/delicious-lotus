"""Internal API authentication middleware."""

import logging
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

import jwt
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from workers.redis_pool import get_redis_connection

from app.api.schemas.errors import ErrorCode, ErrorResponse
from app.config import get_settings

logger = logging.getLogger(__name__)


class InternalAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce authentication for internal API endpoints."""

    def __init__(self, app, rate_limit_per_key: int = 100) -> None:
        """Initialize internal auth middleware.

        Args:
            app: FastAPI application
            rate_limit_per_key: Max requests per minute per API key (default: 100)
        """
        super().__init__(app)
        self.settings = get_settings()
        self.rate_limit_per_key = rate_limit_per_key
        self.window_seconds = 60  # 1 minute window
        self._redis = get_redis_connection()

        logger.info(
            "Internal auth middleware initialized",
            extra={
                "rate_limit_per_key": rate_limit_per_key,
                "num_api_keys": len(self.settings.internal_api_keys),
            },
        )

    def _should_authenticate(self, request: Request) -> bool:
        """Determine if endpoint requires authentication.

        Args:
            request: FastAPI request

        Returns:
            bool: True if endpoint requires authentication
        """
        path = request.url.path

        # Bypass authentication for health check endpoints
        health_endpoints = ["/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"]
        if any(path.startswith(endpoint) for endpoint in health_endpoints):
            return False

        # Require authentication for internal API endpoints
        if path.startswith("/internal/"):
            return True

        return False

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key against configured keys.

        Args:
            api_key: API key from request header

        Returns:
            bool: True if API key is valid
        """
        if not self.settings.internal_api_keys:
            logger.warning("No internal API keys configured")
            return False

        return api_key in self.settings.internal_api_keys

    def _validate_jwt_token(self, token: str) -> dict[str, Any] | None:
        """Validate JWT token for service-to-service authentication.

        Args:
            token: JWT token from Authorization header

        Returns:
            dict: Decoded token payload if valid, None otherwise
        """
        if not self.settings.jwt_secret_key:
            logger.warning("JWT secret key not configured")
            return None

        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )

            # Check token expiration
            exp = payload.get("exp")
            if exp and exp < time.time():
                logger.warning("JWT token has expired")
                return None

            return payload

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    def _check_rate_limit(self, api_key: str, endpoint: str) -> tuple[bool, int, int]:
        """Check rate limit for API key.

        Args:
            api_key: API key identifier
            endpoint: API endpoint being accessed

        Returns:
            tuple: (is_allowed, current_count, retry_after_seconds)
        """
        try:
            # Create unique key for this API key and endpoint
            key = f"internal_rate_limit:{api_key[:8]}:{endpoint}"
            current_time = int(time.time())
            window_start = current_time - self.window_seconds

            # Use Redis sorted set for sliding window
            pipe = self._redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration on the key
            pipe.expire(key, self.window_seconds + 10)

            results = pipe.execute()

            # Get count after removing old entries
            request_count = results[1]

            if request_count >= self.rate_limit_per_key:
                # Calculate retry after time
                oldest_in_window = self._redis.zrange(key, 0, 0, withscores=True)
                if oldest_in_window:
                    oldest_time = int(oldest_in_window[0][1])
                    retry_after = self.window_seconds - (current_time - oldest_time)
                    retry_after = max(1, retry_after)
                else:
                    retry_after = self.window_seconds

                # Remove the current request since we're rejecting it
                self._redis.zrem(key, str(current_time))

                return False, request_count, retry_after

            return True, request_count + 1, 0

        except Exception as e:
            logger.exception(
                "Rate limit check failed",
                extra={"api_key": api_key[:8], "error": str(e)},
            )
            # On Redis failure, allow the request (fail open)
            return True, 0, 0

    def _create_error_response(
        self,
        request: Request,
        error_code: ErrorCode,
        message: str,
        status_code: int,
        retry_after: int | None = None,
    ) -> JSONResponse:
        """Create a standardized error response.

        Args:
            request: FastAPI request
            error_code: Error code
            message: Error message
            status_code: HTTP status code
            retry_after: Optional retry-after seconds

        Returns:
            JSONResponse: Error response
        """
        request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:16]}")

        error_response = ErrorResponse(
            error_code=error_code,
            message=message,
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

        headers = {"Retry-After": str(retry_after)} if retry_after else None

        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump(mode="json"),
            headers=headers,
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Authenticate request before processing.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response: HTTP response or error response
        """
        # Check if this endpoint requires authentication
        if not self._should_authenticate(request):
            return await call_next(request)

        # Try API key authentication first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if not self._validate_api_key(api_key):
                logger.warning(
                    "Invalid API key",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "api_key_prefix": api_key[:8] if api_key else None,
                    },
                )
                return self._create_error_response(
                    request,
                    ErrorCode.UNAUTHORIZED,
                    "Invalid API key",
                    status.HTTP_401_UNAUTHORIZED,
                )

            # Check rate limit for this API key
            endpoint = f"{request.method}:{request.url.path}"
            is_allowed, current_count, retry_after = self._check_rate_limit(api_key, endpoint)

            if not is_allowed:
                logger.warning(
                    "Rate limit exceeded for API key",
                    extra={
                        "api_key_prefix": api_key[:8],
                        "endpoint": endpoint,
                        "count": current_count,
                        "limit": self.rate_limit_per_key,
                    },
                )
                return self._create_error_response(
                    request,
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    f"Rate limit exceeded: {self.rate_limit_per_key} requests per {self.window_seconds} seconds",
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    retry_after=retry_after,
                )

            # Store authenticated info in request state
            request.state.auth_method = "api_key"
            request.state.api_key = api_key

            # Process request and add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit_per_key)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.rate_limit_per_key - current_count)
            )

            return response

        # Try JWT token authentication
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            payload = self._validate_jwt_token(token)

            if not payload:
                logger.warning(
                    "Invalid JWT token",
                    extra={"path": request.url.path, "method": request.method},
                )
                return self._create_error_response(
                    request,
                    ErrorCode.UNAUTHORIZED,
                    "Invalid or expired JWT token",
                    status.HTTP_401_UNAUTHORIZED,
                )

            # Store authenticated info in request state
            request.state.auth_method = "jwt"
            request.state.jwt_payload = payload

            return await call_next(request)

        # No valid authentication provided
        logger.warning(
            "Missing authentication",
            extra={"path": request.url.path, "method": request.method},
        )
        return self._create_error_response(
            request,
            ErrorCode.UNAUTHORIZED,
            "Authentication required. Provide X-API-Key header or Bearer token",
            status.HTTP_401_UNAUTHORIZED,
        )
