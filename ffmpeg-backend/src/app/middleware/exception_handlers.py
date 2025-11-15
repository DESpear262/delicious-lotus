"""Global exception handlers for FastAPI application."""

import logging
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.errors import ErrorCode, ErrorDetail, ErrorResponse
from app.exceptions import (
    CompositionNotFoundError,
    DatabaseError,
    DurationExceededError,
    FFmpegBackendError,
    InvalidTimelineError,
    InvalidURLError,
    ProcessingError,
    RateLimitExceededError,
    S3Error,
    UnauthorizedError,
    UnsupportedFormatError,
)

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    """Get or generate request ID for tracking.

    Args:
        request: FastAPI request

    Returns:
        str: Request ID from header or generated UUID
    """
    # Try to get request ID from header (set by client or load balancer)
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        # Try from state (set by middleware)
        request_id = getattr(request.state, "request_id", None)

    if not request_id:
        # Generate new request ID
        request_id = f"req_{uuid.uuid4().hex[:16]}"

    return request_id


async def ffmpeg_backend_exception_handler(
    request: Request,
    exc: FFmpegBackendError,
) -> JSONResponse:
    """Handle custom FFmpeg backend exceptions.

    Args:
        request: FastAPI request
        exc: Custom exception

    Returns:
        JSONResponse: Standardized error response
    """
    request_id = get_request_id(request)

    # Map exception types to HTTP status codes
    status_code_map = {
        CompositionNotFoundError: status.HTTP_404_NOT_FOUND,
        InvalidTimelineError: status.HTTP_400_BAD_REQUEST,
        DurationExceededError: status.HTTP_400_BAD_REQUEST,
        UnsupportedFormatError: status.HTTP_400_BAD_REQUEST,
        InvalidURLError: status.HTTP_400_BAD_REQUEST,
        UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
        RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        S3Error: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ProcessingError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    http_status = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Map exception types to suggested actions
    suggested_actions = {
        CompositionNotFoundError: "Verify the composition ID is correct",
        InvalidTimelineError: "Check that clips don't overlap and are properly sequenced",
        DurationExceededError: "Reduce the total duration of clips to 3 minutes or less",
        UnsupportedFormatError: "Use one of the supported video formats (mp4, mov, avi)",
        InvalidURLError: "Ensure all media URLs are accessible and valid",
        UnauthorizedError: "Provide valid authentication credentials (X-API-Key header or Bearer token)",
        RateLimitExceededError: "Wait before making more requests",
        DatabaseError: "Retry the request. If the problem persists, contact support",
        S3Error: "Retry the request. If the problem persists, contact support",
        ProcessingError: "Check composition configuration and retry",
    }

    suggested_action = suggested_actions.get(type(exc))

    # Log the error
    logger.error(
        f"Application error: {exc.error_code}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "error_message": exc.message,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
        },
        exc_info=http_status >= 500,  # Include traceback for 5xx errors
    )

    # Build error response
    error_response = ErrorResponse(
        error_code=ErrorCode(exc.error_code),
        message=exc.message,
        request_id=request_id,
        timestamp=datetime.utcnow(),
        suggested_action=suggested_action,
    )

    return JSONResponse(
        status_code=http_status,
        content=error_response.model_dump(mode="json"),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError | ValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSONResponse: Standardized error response with field details
    """
    request_id = get_request_id(request)

    # Extract validation errors
    errors = exc.errors() if hasattr(exc, "errors") else []

    details = []
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_type = error.get("type", "value_error")

        details.append(
            ErrorDetail(
                field=field if field else None,
                message=message,
                error_type=error_type,
            )
        )

    # Log validation error
    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": errors,
        },
    )

    error_response = ErrorResponse(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow(),
        suggested_action="Check the request payload and ensure all required fields are valid",
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode="json"),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle HTTP exceptions.

    Args:
        request: FastAPI request
        exc: HTTP exception

    Returns:
        JSONResponse: Standardized error response
    """
    request_id = get_request_id(request)

    # Map status codes to error codes
    error_code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        413: ErrorCode.PAYLOAD_TOO_LARGE,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    # Log based on status code
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code} error",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            },
        )
    else:
        logger.warning(
            f"HTTP {exc.status_code} error",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            },
        )

    error_response = ErrorResponse(
        error_code=error_code,
        message=str(exc.detail),
        request_id=request_id,
        timestamp=datetime.utcnow(),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Handle SQLAlchemy database errors.

    Args:
        request: FastAPI request
        exc: Database error

    Returns:
        JSONResponse: Standardized error response
    """
    request_id = get_request_id(request)

    logger.exception(
        "Database error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error": str(exc),
        },
    )

    error_response = ErrorResponse(
        error_code=ErrorCode.DATABASE_ERROR,
        message="A database error occurred",
        request_id=request_id,
        timestamp=datetime.utcnow(),
        suggested_action="Retry the request. If the problem persists, contact support",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: FastAPI request
        exc: Unexpected exception

    Returns:
        JSONResponse: Standardized error response
    """
    request_id = get_request_id(request)

    logger.exception(
        "Unexpected error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "exception_type": type(exc).__name__,
        },
    )

    error_response = ErrorResponse(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
        request_id=request_id,
        timestamp=datetime.utcnow(),
        suggested_action="Retry the request. If the problem persists, contact support",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json"),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(FFmpegBackendError, ffmpeg_backend_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Database errors
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)

    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
