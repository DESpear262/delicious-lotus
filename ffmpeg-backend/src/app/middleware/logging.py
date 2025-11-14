"""Logging middleware with structured JSON output."""

import json
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .request_id import get_request_id

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Log request and response information.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response: HTTP response
        """
        start_time = time.time()

        # Log request
        request_log = {
            "event": "request_started",
            "request_id": get_request_id(),
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        logger.info(json.dumps(request_log))

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log error
            duration = time.time() - start_time
            error_log = {
                "event": "request_error",
                "request_id": get_request_id(),
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration * 1000, 2),
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
            logger.error(json.dumps(error_log))
            raise

        # Log response
        duration = time.time() - start_time
        response_log = {
            "event": "request_completed",
            "request_id": get_request_id(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }

        # Use different log levels based on status code
        if response.status_code >= 500:
            logger.error(json.dumps(response_log))
        elif response.status_code >= 400:
            logger.warning(json.dumps(response_log))
        else:
            logger.info(json.dumps(response_log))

        return response
