"""Custom exception classes for domain-specific errors."""


class FFmpegBackendError(Exception):
    """Base exception for all FFmpeg backend errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize exception with message and error code.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "internal_error"


class CompositionNotFoundError(FFmpegBackendError):
    """Raised when a composition is not found."""

    def __init__(self, composition_id: str) -> None:
        """Initialize with composition ID.

        Args:
            composition_id: ID of the composition that was not found
        """
        super().__init__(
            message=f"Composition {composition_id} not found",
            error_code="not_found",
        )
        self.composition_id = composition_id


class InvalidTimelineError(FFmpegBackendError):
    """Raised when composition timeline is invalid."""

    def __init__(self, message: str) -> None:
        """Initialize with specific timeline error message.

        Args:
            message: Description of the timeline validation error
        """
        super().__init__(message=message, error_code="invalid_timeline")


class DurationExceededError(FFmpegBackendError):
    """Raised when composition duration exceeds maximum allowed."""

    def __init__(self, duration: float, max_duration: float = 180.0) -> None:
        """Initialize with duration details.

        Args:
            duration: Actual composition duration in seconds
            max_duration: Maximum allowed duration in seconds (default 3 minutes)
        """
        super().__init__(
            message=f"Composition duration ({duration}s) exceeds maximum allowed ({max_duration}s)",
            error_code="duration_exceeded",
        )
        self.duration = duration
        self.max_duration = max_duration


class UnsupportedFormatError(FFmpegBackendError):
    """Raised when an unsupported media format is encountered."""

    def __init__(self, format_type: str, supported_formats: list[str]) -> None:
        """Initialize with format details.

        Args:
            format_type: The unsupported format that was provided
            supported_formats: List of supported formats
        """
        super().__init__(
            message=f"Unsupported format: {format_type}. Supported formats: {', '.join(supported_formats)}",
            error_code="unsupported_format",
        )
        self.format_type = format_type
        self.supported_formats = supported_formats


class InvalidURLError(FFmpegBackendError):
    """Raised when a media URL is invalid or inaccessible."""

    def __init__(self, url: str, reason: str = "Invalid or inaccessible URL") -> None:
        """Initialize with URL details.

        Args:
            url: The invalid URL
            reason: Reason why the URL is invalid
        """
        super().__init__(
            message=f"Invalid URL: {url}. {reason}",
            error_code="invalid_url",
        )
        self.url = url
        self.reason = reason


class DatabaseError(FFmpegBackendError):
    """Raised when a database operation fails."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize with database error details.

        Args:
            message: Description of the database error
            original_error: Original exception that caused the database error
        """
        super().__init__(message=message, error_code="database_error")
        self.original_error = original_error


class S3Error(FFmpegBackendError):
    """Raised when an S3 operation fails."""

    def __init__(
        self, message: str, s3_key: str | None = None, original_error: Exception | None = None
    ) -> None:
        """Initialize with S3 error details.

        Args:
            message: Description of the S3 error
            s3_key: S3 key that caused the error
            original_error: Original exception that caused the S3 error
        """
        super().__init__(message=message, error_code="storage_error")
        self.s3_key = s3_key
        self.original_error = original_error


class RateLimitExceededError(FFmpegBackendError):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: int, window: int, retry_after: int | None = None) -> None:
        """Initialize with rate limit details.

        Args:
            limit: Maximum requests allowed
            window: Time window in seconds
            retry_after: Seconds to wait before retrying
        """
        message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        super().__init__(message=message, error_code="rate_limit_exceeded")
        self.limit = limit
        self.window = window
        self.retry_after = retry_after


class ProcessingError(FFmpegBackendError):
    """Raised when video processing fails."""

    def __init__(self, message: str, composition_id: str | None = None) -> None:
        """Initialize with processing error details.

        Args:
            message: Description of the processing error
            composition_id: ID of the composition being processed
        """
        super().__init__(message=message, error_code="processing_error")
        self.composition_id = composition_id
