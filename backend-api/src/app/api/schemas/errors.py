"""Error response schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Client errors (4xx)
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    INVALID_TIMELINE = "invalid_timeline"
    DURATION_EXCEEDED = "duration_exceeded"
    UNSUPPORTED_FORMAT = "unsupported_format"
    INVALID_URL = "invalid_url"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    PAYLOAD_TOO_LARGE = "payload_too_large"

    # Server errors (5xx)
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"
    STORAGE_ERROR = "storage_error"
    PROCESSING_ERROR = "processing_error"
    SERVICE_UNAVAILABLE = "service_unavailable"


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: str | None = Field(
        None, description="Field that caused the error (for validation errors)"
    )
    message: str = Field(..., description="Detailed error message")
    error_type: str | None = Field(None, description="Type of error")


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: list[ErrorDetail] | None = Field(
        default=None, description="Additional error details (e.g., validation errors)"
    )
    request_id: str = Field(..., description="Unique request identifier for tracking")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the error occurred"
    )
    suggested_action: str | None = Field(
        None, description="Suggested action for the client to resolve the error"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra: dict = {
            "example": {
                "error_code": "validation_error",
                "message": "Invalid composition request",
                "details": [
                    {
                        "field": "clips",
                        "message": "Total composition duration (200s) exceeds maximum allowed duration (180s / 3 minutes)",
                        "error_type": "value_error",
                    }
                ],
                "request_id": "req_abc123",
                "timestamp": "2024-01-15T10:30:00Z",
                "suggested_action": "Reduce the total duration of clips to 3 minutes or less",
            }
        }
