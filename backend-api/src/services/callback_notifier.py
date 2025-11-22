"""
Callback Notification Service for internal API.

This module provides functionality to send HTTP callbacks to AI Backend
when clip processing completes, with retry logic and signature verification.
"""

import hashlib
import hmac
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class CallbackStatus(str, Enum):
    """Status of callback delivery."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class CallbackAttempt:
    """Record of a callback attempt.

    Attributes:
        attempt_number: Attempt number (1-indexed)
        timestamp: When attempt was made
        status_code: HTTP status code (if received)
        success: Whether attempt succeeded
        error: Error message if failed
        retry_after: Seconds until next retry
    """

    attempt_number: int
    timestamp: datetime
    status_code: int | None = None
    success: bool = False
    error: str | None = None
    retry_after: float | None = None


@dataclass
class CallbackResult:
    """Result of callback delivery.

    Attributes:
        success: Whether callback was delivered successfully
        attempts: List of delivery attempts
        final_status_code: Final HTTP status code
        total_time: Total time spent including retries (seconds)
        error: Error message if failed
    """

    success: bool
    attempts: list[CallbackAttempt]
    final_status_code: int | None = None
    total_time: float | None = None
    error: str | None = None


class CallbackNotifierError(Exception):
    """Exception raised for callback notification errors."""

    pass


class CallbackNotifier:
    """
    Service for sending HTTP callbacks to AI Backend.

    Implements retry logic with exponential backoff, webhook signature
    verification, and timeout handling.
    """

    def __init__(
        self,
        webhook_secret: str | None = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        base_retry_delay: float = 1.0,
    ) -> None:
        """Initialize callback notifier.

        Args:
            webhook_secret: Secret key for webhook signature (optional)
            max_retries: Maximum number of retry attempts
            timeout: HTTP request timeout in seconds
            base_retry_delay: Base delay for exponential backoff (seconds)
        """
        settings = get_settings()

        self.webhook_secret = webhook_secret or getattr(settings, "webhook_secret", None)
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_retry_delay = base_retry_delay

        logger.info(
            "Initialized CallbackNotifier",
            extra={
                "max_retries": max_retries,
                "timeout": timeout,
                "has_webhook_secret": self.webhook_secret is not None,
            },
        )

    def send_callback(
        self,
        callback_url: str,
        payload: dict[str, Any],
        request_id: str | None = None,
    ) -> CallbackResult:
        """Send HTTP callback with retry logic.

        Args:
            callback_url: URL to send callback to
            payload: Callback payload dict
            request_id: Optional request ID for tracking

        Returns:
            CallbackResult with delivery details

        Raises:
            CallbackNotifierError: If all retry attempts fail
        """
        start_time = time.time()
        attempts: list[CallbackAttempt] = []

        logger.info(
            "Sending callback",
            extra={
                "callback_url": callback_url,
                "request_id": request_id,
                "max_retries": self.max_retries,
            },
        )

        for attempt_num in range(1, self.max_retries + 1):
            # Calculate retry delay using exponential backoff
            if attempt_num > 1:
                retry_delay = self._calculate_retry_delay(attempt_num - 1)
                logger.info(
                    f"Retrying callback (attempt {attempt_num}/{self.max_retries})",
                    extra={
                        "callback_url": callback_url,
                        "retry_delay": retry_delay,
                    },
                )
                time.sleep(retry_delay)

            # Make HTTP request
            attempt = self._make_callback_request(
                callback_url=callback_url,
                payload=payload,
                attempt_number=attempt_num,
                request_id=request_id,
            )

            attempts.append(attempt)

            if attempt.success:
                total_time = time.time() - start_time

                logger.info(
                    "Callback delivered successfully",
                    extra={
                        "callback_url": callback_url,
                        "attempts": attempt_num,
                        "total_time": round(total_time, 2),
                    },
                )

                return CallbackResult(
                    success=True,
                    attempts=attempts,
                    final_status_code=attempt.status_code,
                    total_time=total_time,
                )

            # Log failure
            logger.warning(
                f"Callback attempt {attempt_num} failed",
                extra={
                    "callback_url": callback_url,
                    "status_code": attempt.status_code,
                    "error": attempt.error,
                },
            )

        # All attempts failed
        total_time = time.time() - start_time
        final_error = attempts[-1].error if attempts else "Unknown error"

        logger.error(
            "Callback delivery failed after all retries",
            extra={
                "callback_url": callback_url,
                "attempts": len(attempts),
                "total_time": round(total_time, 2),
            },
        )

        return CallbackResult(
            success=False,
            attempts=attempts,
            final_status_code=attempts[-1].status_code if attempts else None,
            total_time=total_time,
            error=f"Failed after {len(attempts)} attempts: {final_error}",
        )

    def _make_callback_request(
        self,
        callback_url: str,
        payload: dict[str, Any],
        attempt_number: int,
        request_id: str | None = None,
    ) -> CallbackAttempt:
        """Make a single HTTP callback request.

        Args:
            callback_url: URL to send callback to
            payload: Callback payload
            attempt_number: Current attempt number
            request_id: Optional request ID

        Returns:
            CallbackAttempt with attempt details
        """
        attempt_time = datetime.now(UTC)

        try:
            # Generate webhook signature if secret is configured
            headers = {"Content-Type": "application/json"}

            if self.webhook_secret:
                signature = self._generate_signature(payload)
                headers["X-Webhook-Signature"] = signature

            if request_id:
                headers["X-Request-ID"] = request_id

            # Make HTTP POST request with timeout
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    callback_url,
                    json=payload,
                    headers=headers,
                )

                # Check if status code indicates success (2xx)
                if 200 <= response.status_code < 300:
                    return CallbackAttempt(
                        attempt_number=attempt_number,
                        timestamp=attempt_time,
                        status_code=response.status_code,
                        success=True,
                    )
                else:
                    return CallbackAttempt(
                        attempt_number=attempt_number,
                        timestamp=attempt_time,
                        status_code=response.status_code,
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                    )

        except httpx.TimeoutException:
            logger.warning(
                f"Callback request timed out after {self.timeout}s",
                extra={"callback_url": callback_url, "attempt": attempt_number},
            )
            return CallbackAttempt(
                attempt_number=attempt_number,
                timestamp=attempt_time,
                success=False,
                error=f"Request timed out after {self.timeout}s",
            )

        except httpx.HTTPError as e:
            logger.warning(
                f"HTTP error during callback: {e}",
                extra={"callback_url": callback_url, "attempt": attempt_number},
            )
            return CallbackAttempt(
                attempt_number=attempt_number,
                timestamp=attempt_time,
                success=False,
                error=f"HTTP error: {e!s}",
            )

        except Exception as e:
            logger.exception(
                "Unexpected error during callback",
                extra={"callback_url": callback_url, "attempt": attempt_number},
            )
            return CallbackAttempt(
                attempt_number=attempt_number,
                timestamp=attempt_time,
                success=False,
                error=f"Unexpected error: {e!s}",
            )

    def _generate_signature(self, payload: dict[str, Any]) -> str:
        """Generate HMAC signature for webhook verification.

        Args:
            payload: Callback payload dict

        Returns:
            str: Hex-encoded HMAC signature
        """
        import json

        # Serialize payload to JSON (deterministic)
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        return f"sha256={signature}"

    @staticmethod
    def verify_signature(
        payload: dict[str, Any],
        signature: str,
        secret: str,
    ) -> bool:
        """Verify webhook signature.

        Args:
            payload: Callback payload dict
            signature: Signature from header (format: "sha256=<hex>")
            secret: Webhook secret key

        Returns:
            bool: True if signature is valid
        """
        import json

        if not signature.startswith("sha256="):
            return False

        expected_sig = signature[7:]  # Remove "sha256=" prefix

        # Generate expected signature
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        calculated_sig = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        # Compare using constant-time comparison
        return hmac.compare_digest(expected_sig, calculated_sig)

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate retry delay using exponential backoff.

        Args:
            retry_count: Number of retries so far (0-indexed)

        Returns:
            float: Delay in seconds
        """
        # Exponential backoff: delay = base * (2 ^ retry_count)
        # With jitter to avoid thundering herd
        import random

        delay = self.base_retry_delay * (2**retry_count)

        # Add jitter (±25%)
        jitter = random.uniform(0.75, 1.25)  # noqa: S311
        delay = delay * jitter

        # Cap maximum delay at 60 seconds
        delay = min(delay, 60.0)

        return delay

    def send_processing_complete_callback(
        self,
        callback_url: str,
        request_id: str,
        results: list[dict[str, Any]],
    ) -> CallbackResult:
        """Send callback for completed clip processing.

        Args:
            callback_url: URL to send callback to
            request_id: Original request ID
            results: List of processing results

        Returns:
            CallbackResult with delivery details
        """
        # Count successful and failed clips
        successful = sum(1 for r in results if r.get("status") == "completed")
        failed = sum(1 for r in results if r.get("status") == "failed")

        # Build callback payload
        payload = {
            "request_id": request_id,
            "completed_at": datetime.now(UTC).isoformat(),
            "results": results,
            "total_successful": successful,
            "total_failed": failed,
        }

        return self.send_callback(
            callback_url=callback_url,
            payload=payload,
            request_id=request_id,
        )
