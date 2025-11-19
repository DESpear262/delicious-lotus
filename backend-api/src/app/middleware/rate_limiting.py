"""Rate limiting middleware using Redis."""

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from workers.redis_pool import get_redis_connection

from app.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits using Redis."""

    def __init__(self, app, requests_per_minute: int = 10) -> None:
        """Initialize rate limit middleware.

        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests allowed per minute (default: 10)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60  # 1 minute window
        self._redis = get_redis_connection()

        logger.info(
            "Rate limit middleware initialized",
            extra={"requests_per_minute": requests_per_minute},
        )

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for the client.

        Uses X-Forwarded-For if behind proxy, otherwise client IP.

        Args:
            request: FastAPI request

        Returns:
            str: Client identifier
        """
        # Try to get real IP from X-Forwarded-For header (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one (client IP)
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # Fallback to direct client IP
            client_ip = request.client.host if request.client else "unknown"

        # Could also use API key if implementing authentication:
        # api_key = request.headers.get("X-API-Key")
        # if api_key:
        #     return f"api_key:{api_key}"

        return f"ip:{client_ip}"

    def _should_rate_limit(self, request: Request) -> bool:
        """Determine if endpoint should be rate limited.

        Args:
            request: FastAPI request

        Returns:
            bool: True if endpoint should be rate limited
        """
        # Rate limit POST endpoints more strictly
        if request.method == "POST":
            # Composition creation endpoint
            if "/compositions" in request.url.path and not request.url.path.endswith(
                "/compositions"
            ):
                return False  # Don't rate limit nested routes like /compositions/{id}/...
            return True

        # Don't rate limit GET requests as heavily (they're read-only)
        # Could implement separate limits for GET if needed
        return False

    def _check_rate_limit(self, client_id: str, endpoint: str) -> tuple[bool, int, int]:
        """Check if client has exceeded rate limit.

        Uses sliding window algorithm with Redis.

        Args:
            client_id: Unique client identifier
            endpoint: API endpoint being accessed

        Returns:
            tuple: (is_allowed, current_count, retry_after_seconds)
        """
        try:
            # Create unique key for this client and endpoint
            key = f"rate_limit:{client_id}:{endpoint}"
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

            if request_count >= self.requests_per_minute:
                # Calculate retry after time
                # Get oldest request in window
                oldest_in_window = self._redis.zrange(key, 0, 0, withscores=True)
                if oldest_in_window:
                    oldest_time = int(oldest_in_window[0][1])
                    retry_after = self.window_seconds - (current_time - oldest_time)
                    retry_after = max(1, retry_after)  # At least 1 second
                else:
                    retry_after = self.window_seconds

                # Remove the current request since we're rejecting it
                self._redis.zrem(key, str(current_time))

                return False, request_count, retry_after

            return True, request_count + 1, 0

        except Exception as e:
            logger.exception(
                "Rate limit check failed",
                extra={"client_id": client_id, "error": str(e)},
            )
            # On Redis failure, allow the request (fail open)
            return True, 0, 0

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Check rate limits before processing request.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response: HTTP response

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        # Check if this endpoint should be rate limited
        if not self._should_rate_limit(request):
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_identifier(request)

        # Create endpoint identifier (method + path)
        endpoint = f"{request.method}:{request.url.path}"

        # Check rate limit
        is_allowed, current_count, retry_after = self._check_rate_limit(client_id, endpoint)

        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_id": client_id,
                    "endpoint": endpoint,
                    "count": current_count,
                    "limit": self.requests_per_minute,
                    "retry_after": retry_after,
                },
            )

            raise RateLimitExceededError(
                limit=self.requests_per_minute,
                window=self.window_seconds,
                retry_after=retry_after,
            )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add rate limit info to response headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - current_count)
        )
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_seconds)

        return response
