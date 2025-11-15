"""Global exception handlers for FastAPI application with error tracking."""

import hashlib
import logging
import platform
import sys
import traceback
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.errors import ErrorCode, ErrorDetail, ErrorResponse
from app.config import get_settings
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

# Error occurrence tracking for fingerprinting
error_occurrences: dict[str, int] = {}


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


def generate_error_fingerprint(
    exc: Exception, request_path: str, include_line_number: bool = True
) -> str:
    """Generate a unique fingerprint for an error to group similar occurrences.

    Args:
        exc: Exception instance
        request_path: Request path where error occurred
        include_line_number: Whether to include line number in fingerprint

    Returns:
        str: MD5 hash fingerprint for the error
    """
    # Extract traceback information
    tb = traceback.extract_tb(exc.__traceback__)
    if tb:
        last_frame = tb[-1]
        file_name = last_frame.filename
        func_name = last_frame.name
        line_no = last_frame.lineno if include_line_number else 0
    else:
        file_name = "unknown"
        func_name = "unknown"
        line_no = 0

    # Create fingerprint from error type, location, and message pattern
    error_type = type(exc).__name__
    error_msg_pattern = str(exc)[:100]  # First 100 chars to group similar errors

    fingerprint_data = (
        f"{error_type}:{file_name}:{func_name}:{line_no}:{error_msg_pattern}:{request_path}"
    )
    return hashlib.md5(fingerprint_data.encode(), usedforsecurity=False).hexdigest()


def track_error_occurrence(fingerprint: str) -> int:
    """Track and return the occurrence count for an error fingerprint.

    Args:
        fingerprint: Error fingerprint hash

    Returns:
        int: Number of times this error has occurred
    """
    error_occurrences[fingerprint] = error_occurrences.get(fingerprint, 0) + 1
    return error_occurrences[fingerprint]


def extract_error_context(request: Request, exc: Exception) -> dict[str, Any]:
    """Extract comprehensive context information about an error.

    Args:
        request: FastAPI request
        exc: Exception instance

    Returns:
        dict: Context information including request data, system state, and stack trace
    """
    # Extract traceback with local variables
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    stack_trace = "".join(tb_lines)

    # Get the settings
    settings = get_settings()

    # Build context
    context = {
        "exception": {
            "type": type(exc).__name__,
            "message": str(exc),
            "module": exc.__class__.__module__,
        },
        "stack_trace": stack_trace,
        "request": {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                k: v
                for k, v in request.headers.items()
                if k.lower() not in ["authorization", "cookie", "x-api-key", "x-auth-token"]
            },
            "client_host": request.client.host if request.client else None,
        },
        "system": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "environment": settings.environment,
        },
        "timing": {
            "timestamp": datetime.utcnow().isoformat(),
        },
    }

    # Add user context if available
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        context["user"] = {"user_id": user_id}

    # Add composition context if available
    composition_id = getattr(request.state, "composition_id", None)
    if composition_id:
        context["composition"] = {"composition_id": composition_id}

    return context


def is_transient_error(exc: Exception) -> bool:
    """Determine if an error is transient and retryable.

    Args:
        exc: Exception instance

    Returns:
        bool: True if error is likely transient
    """
    # List of transient error indicators
    transient_errors = [
        DatabaseError,
        S3Error,
    ]

    transient_messages = [
        "timeout",
        "connection",
        "temporary",
        "unavailable",
        "503",
        "504",
    ]

    # Check if exception type is known to be transient
    if any(isinstance(exc, err_type) for err_type in transient_errors):
        return True

    # Check if error message indicates transient issue
    error_message = str(exc).lower()
    return any(msg in error_message for msg in transient_messages)


async def ffmpeg_backend_exception_handler(
    request: Request,
    exc: FFmpegBackendError,
) -> JSONResponse:
    """Handle custom FFmpeg backend exceptions with enhanced tracking.

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

    # Generate error fingerprint and track occurrences
    fingerprint = generate_error_fingerprint(exc, request.url.path)
    occurrence_count = track_error_occurrence(fingerprint)

    # Extract error context for 5xx errors
    extra_context = {}
    if http_status >= 500:
        error_context = extract_error_context(request, exc)
        extra_context = error_context

    # Log the error with enhanced context
    logger.error(
        f"Application error: {exc.error_code}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "error_message": exc.message,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "error_fingerprint": fingerprint,
            "occurrence_count": occurrence_count,
            **extra_context,
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

    # Add retry header for transient errors
    headers = {}
    if is_transient_error(exc):
        headers["Retry-After"] = "5"

    return JSONResponse(
        status_code=http_status,
        content=error_response.model_dump(mode="json"),
        headers=headers if headers else None,
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
    """Handle SQLAlchemy database errors with context tracking.

    Args:
        request: FastAPI request
        exc: Database error

    Returns:
        JSONResponse: Standardized error response
    """
    request_id = get_request_id(request)

    # Generate error fingerprint
    fingerprint = generate_error_fingerprint(exc, request.url.path)
    occurrence_count = track_error_occurrence(fingerprint)

    # Extract error context
    error_context = extract_error_context(request, exc)

    logger.exception(
        "Database error",
        extra={
            "request_id": request_id,
            "error_fingerprint": fingerprint,
            "occurrence_count": occurrence_count,
            **error_context,
        },
    )

    error_response = ErrorResponse(
        error_code=ErrorCode.DATABASE_ERROR,
        message="A database error occurred",
        request_id=request_id,
        timestamp=datetime.utcnow(),
        suggested_action="This appears to be a database connectivity issue. Please retry the request.",
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(mode="json"),
        headers={"Retry-After": "3"},  # Database errors are usually transient
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions with comprehensive error tracking.

    Args:
        request: FastAPI request
        exc: Unexpected exception

    Returns:
        JSONResponse: Standardized error response
    """
    request_id = get_request_id(request)

    # Generate error fingerprint for grouping
    fingerprint = generate_error_fingerprint(exc, request.url.path)
    occurrence_count = track_error_occurrence(fingerprint)

    # Extract full error context
    error_context = extract_error_context(request, exc)

    # Check if error is transient
    is_retryable = is_transient_error(exc)

    # Log with comprehensive context
    logger.exception(
        "Unexpected error",
        extra={
            "request_id": request_id,
            "error_fingerprint": fingerprint,
            "occurrence_count": occurrence_count,
            "is_retryable": is_retryable,
            **error_context,
        },
    )

    # Provide retry suggestion for transient errors
    suggested_action = (
        "This appears to be a temporary issue. Please retry the request."
        if is_retryable
        else "Retry the request. If the problem persists, contact support"
    )

    error_response = ErrorResponse(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
        request_id=request_id,
        timestamp=datetime.utcnow(),
        suggested_action=suggested_action,
    )

    # Add retry hint if transient
    if is_retryable:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump(mode="json"),
            headers={"Retry-After": "5"},  # Suggest retry after 5 seconds
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
