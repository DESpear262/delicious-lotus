"""Error handling middleware for consistent error responses."""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .request_id import get_request_id

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Handle errors and return consistent JSON responses.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            Response: HTTP response or error response
        """
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = get_request_id()

            # Log the exception
            logger.exception(
                f"Unhandled exception for request {request_id}: {exc!s}",
                extra={"request_id": request_id, "path": request.url.path},
            )

            # Determine status code based on exception type
            status_code = 500
            error_type = "internal_server_error"
            error_message = "An internal server error occurred"

            # You can add custom exception handling here
            # For example:
            # if isinstance(exc, CustomNotFoundException):
            #     status_code = 404
            #     error_type = "not_found"
            #     error_message = str(exc)

            # Return consistent error response
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": {
                        "type": error_type,
                        "message": error_message,
                        "request_id": request_id,
                    }
                },
            )
