"""
Logging configuration and middleware
Block 0: API Skeleton & Core Infrastructure
"""

import logging
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time


class RequestIDMiddleware:
    """Middleware to add request IDs to all requests for tracing"""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Add request ID to scope for use in logging
        scope["request_id"] = request_id

        # Add request ID to headers for client visibility
        async def send_with_request_id(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append([b"x-request-id", request_id.encode()])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)


def setup_logging(level: str = "INFO") -> None:
    """Configure application logging"""

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Reduce noise from external libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_request_logger(request: Request) -> logging.Logger:
    """Get a logger instance with request ID context"""
    logger = logging.getLogger("app")
    if hasattr(request.state, "request_id"):
        # Add request ID to log record
        extra = {"request_id": request.state.request_id}
        return logging.LoggerAdapter(logger, extra)
    return logger
