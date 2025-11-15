"""Request ID middleware for tracking requests through the system."""

import uuid
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging_config import clear_context, set_request_id

# Context variable to store request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get the current request ID from context.

    Returns:
        str: Current request ID or empty string if not set
    """
    return request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process request and add request ID header.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response: HTTP response with X-Request-ID header
        """
        # Clear previous request context
        clear_context()

        # Try to get request ID from header, otherwise generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in context variable for use in logging and error handling
        request_id_var.set(request_id)

        # Also set in logging context for structured logging
        set_request_id(request_id)

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
