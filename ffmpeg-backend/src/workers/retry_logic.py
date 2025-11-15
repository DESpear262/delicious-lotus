"""Retry logic and timeout handling for job execution."""

import functools
import logging
import signal
import time
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from app.config import settings
from botocore.exceptions import BotoCoreError, ClientError
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class FailureType(str, Enum):
    """Classification of job failures."""

    TRANSIENT = "transient"  # Retryable (network, timeout, etc.)
    PERMANENT = "permanent"  # Not retryable (invalid params, etc.)
    TIMEOUT = "timeout"  # Job exceeded timeout limit


# Exceptions that are considered transient and can be retried
TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    RedisConnectionError,
    RedisTimeoutError,
    ClientError,  # S3 errors
    BotoCoreError,
)

# Exceptions that are permanent and should not be retried
PERMANENT_EXCEPTIONS = (
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
    FileNotFoundError,
)


class JobTimeoutError(Exception):
    """Raised when a job exceeds its timeout limit."""

    pass


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exceeded."""

    pass


def classify_failure(exception: Exception) -> FailureType:
    """Classify failure type based on exception.

    Args:
        exception: The exception that occurred

    Returns:
        FailureType: Classification of the failure
    """
    if isinstance(exception, JobTimeoutError):
        return FailureType.TIMEOUT

    if isinstance(exception, TRANSIENT_EXCEPTIONS):
        return FailureType.TRANSIENT

    if isinstance(exception, PERMANENT_EXCEPTIONS):
        return FailureType.PERMANENT

    # Check S3 error codes for classification
    if isinstance(exception, ClientError):
        error_code = exception.response.get("Error", {}).get("Code")

        # Throttling errors are transient
        if error_code in {"Throttling", "RequestLimitExceeded", "ServiceUnavailable"}:
            return FailureType.TRANSIENT

        # Not found or access denied are permanent
        if error_code in {"404", "403", "NoSuchKey", "AccessDenied"}:
            return FailureType.PERMANENT

    # Default to permanent for unknown exceptions
    return FailureType.PERMANENT


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter

    Returns:
        float: Delay in seconds
    """
    import random

    # Calculate exponential delay: base * 2^attempt
    delay = base_delay * (2**attempt)

    # Cap at max delay
    delay = min(delay, max_delay)

    # Add jitter to avoid thundering herd
    if jitter:
        delay = delay * (0.5 + random.random())  # Random between 50-100% of delay

    return delay


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: tuple[type[Exception], ...] = TRANSIENT_EXCEPTIONS,
) -> Callable[[F], F]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries
        retry_on: Tuple of exception types to retry on

    Returns:
        Callable: Decorated function with retry logic

    Example:
        @retry_with_backoff(max_retries=3)
        def upload_to_s3(file_path):
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except retry_on as e:
                    last_exception = e

                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "error": str(e),
                            },
                        )
                        raise MaxRetriesExceededError(
                            f"Max retries exceeded after {max_retries} attempts: {e}"
                        ) from e

                    # Calculate backoff delay
                    delay = exponential_backoff(
                        attempt=attempt,
                        base_delay=base_delay,
                        max_delay=max_delay,
                    )

                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {delay:.2f}s",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    time.sleep(delay)

            # Should not reach here, but if it does, raise last exception
            if last_exception:
                raise last_exception

        return wrapper  # type: ignore

    return decorator


class TimeoutManager:
    """Manages timeout for long-running operations."""

    def __init__(self, timeout_seconds: int) -> None:
        """Initialize timeout manager.

        Args:
            timeout_seconds: Timeout in seconds
        """
        self.timeout_seconds = timeout_seconds
        self._old_handler: Any = None

    def _timeout_handler(self, signum: int, frame: Any) -> None:
        """Signal handler for timeout.

        Args:
            signum: Signal number
            frame: Current stack frame

        Raises:
            JobTimeoutError: Always raises timeout error
        """
        raise JobTimeoutError(f"Operation exceeded timeout of {self.timeout_seconds} seconds")

    def __enter__(self) -> "TimeoutManager":
        """Enter timeout context.

        Returns:
            TimeoutManager: Self
        """
        # Set up timeout handler
        self._old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.timeout_seconds)

        logger.debug(f"Started timeout timer: {self.timeout_seconds}s")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit timeout context.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        # Cancel alarm and restore old handler
        signal.alarm(0)
        if self._old_handler:
            signal.signal(signal.SIGALRM, self._old_handler)

        logger.debug("Cancelled timeout timer")


def with_timeout(timeout_seconds: int | None = None) -> Callable[[F], F]:
    """Decorator for adding timeout to functions.

    Args:
        timeout_seconds: Timeout in seconds (defaults to settings.rq_default_timeout)

    Returns:
        Callable: Decorated function with timeout

    Example:
        @with_timeout(300)
        def process_video():
            ...
    """
    if timeout_seconds is None:
        timeout_seconds = settings.rq_default_timeout

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with TimeoutManager(timeout_seconds):
                return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def should_retry(exception: Exception, attempt: int, max_retries: int) -> bool:
    """Determine if an exception should be retried.

    Args:
        exception: The exception that occurred
        attempt: Current attempt number (0-indexed)
        max_retries: Maximum number of retries

    Returns:
        bool: True if should retry, False otherwise
    """
    # Don't retry if max retries exceeded
    if attempt >= max_retries:
        return False

    # Check failure classification
    failure_type = classify_failure(exception)

    # Only retry transient failures
    if failure_type != FailureType.TRANSIENT:
        logger.info(
            f"Not retrying {failure_type.value} failure: {exception}",
            extra={
                "failure_type": failure_type.value,
                "exception": str(exception),
            },
        )
        return False

    return True
