"""
Custom exceptions and error handling
Block 0: API Skeleton & Core Infrastructure
"""

from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response format"""
    error: Dict[str, Any]


class APIError(Exception):
    """Base exception for API errors"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error for invalid input data"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            details=details
        )


class NotFoundError(APIError):
    """Resource not found error"""

    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"

        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=404
        )


class GenerationError(APIError):
    """Error during video generation"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="GENERATION_ERROR",
            message=message,
            status_code=500,
            details=details
        )


class ExternalServiceError(APIError):
    """Error from external service (Replicate, OpenAI, FFmpeg)"""

    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}",
            status_code=502,
            details=details
        )


class RateLimitError(APIError):
    """Rate limit exceeded"""

    def __init__(self, retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded. Please try again later.",
            status_code=429,
            details=details
        )


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    error_data = {
        "code": code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if request_id:
        error_data["request_id"] = request_id

    if details:
        error_data["details"] = details

    return ErrorResponse(error=error_data)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that converts exceptions to standardized error responses
    """

    # Extract request ID from request state
    request_id = getattr(request.state, "request_id", "unknown")

    # Handle APIError subclasses
    if isinstance(exc, APIError):
        error_response = create_error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
            details=exc.details
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )

    # Handle FastAPI HTTPException
    elif isinstance(exc, HTTPException):
        error_response = create_error_response(
            code="HTTP_EXCEPTION",
            message=exc.detail,
            status_code=exc.status_code,
            request_id=request_id
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )

    # Handle Pydantic validation errors
    elif hasattr(exc, "__class__") and "ValidationError" in str(type(exc)):
        # This handles Pydantic's ValidationError
        error_response = create_error_response(
            code="VALIDATION_ERROR",
            message="Invalid request data",
            status_code=422,
            request_id=request_id,
            details={"validation_errors": str(exc)}
        )
        return JSONResponse(
            status_code=422,
            content=error_response.dict()
        )

    # Handle all other exceptions as internal server errors
    else:
        error_response = create_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            status_code=500,
            request_id=request_id
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )
