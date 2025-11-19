"""Progress tracking using Redis pub/sub for real-time job updates."""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from workers.redis_pool import get_redis_connection

logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """Progress update message structure."""

    job_id: str
    composition_id: str | None
    timestamp: str
    progress_percent: float
    current_operation: str
    frame: int = 0
    fps: float = 0.0
    bitrate_kbps: float = 0.0
    speed: float = 0.0
    eta_seconds: float | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            dict: Serialized progress update
        """
        data = asdict(self)
        # Filter out None values for cleaner output
        return {k: v for k, v in data.items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            str: JSON representation
        """
        return json.dumps(self.to_dict())


class ProgressTracker:
    """Tracks and publishes job progress updates via Redis pub/sub."""

    def __init__(
        self,
        job_id: str,
        composition_id: str | None = None,
        throttle_seconds: float = 0.5,
    ) -> None:
        """Initialize progress tracker.

        Args:
            job_id: Unique job identifier
            composition_id: Optional composition ID
            throttle_seconds: Minimum seconds between progress updates
        """
        self.job_id = job_id
        self.composition_id = composition_id
        self.throttle_seconds = throttle_seconds

        self._redis = get_redis_connection()
        self._last_update_time: float = 0.0
        self._last_progress_percent: float = 0.0

        # Redis keys
        self.channel_name = f"job:progress:{job_id}"
        self.status_key = f"job:status:{job_id}"
        self.progress_key = f"job:progress:data:{job_id}"

        logger.info(
            "Initialized ProgressTracker",
            extra={
                "job_id": job_id,
                "composition_id": composition_id,
                "channel": self.channel_name,
            },
        )

    def publish_progress(
        self,
        progress_percent: float,
        operation: str,
        frame: int = 0,
        fps: float = 0.0,
        bitrate_kbps: float = 0.0,
        speed: float = 0.0,
        eta_seconds: float | None = None,
        force: bool = False,
        **metadata: Any,
    ) -> bool:
        """Publish progress update to Redis pub/sub.

        Args:
            progress_percent: Progress percentage (0-100)
            operation: Current operation description
            frame: Current frame number
            fps: Frames per second
            bitrate_kbps: Bitrate in kbps
            speed: Processing speed multiplier
            eta_seconds: Estimated time to completion
            force: Force publish even if throttled
            **metadata: Additional metadata to include

        Returns:
            bool: True if update was published, False if throttled
        """
        current_time = time.time()

        # Check if we should throttle this update
        time_since_last = current_time - self._last_update_time
        progress_delta = abs(progress_percent - self._last_progress_percent)

        # Skip update if throttled (unless forced or significant progress change)
        if not force and time_since_last < self.throttle_seconds and progress_delta < 5.0:
            return False

        try:
            # Create progress update
            update = ProgressUpdate(
                job_id=self.job_id,
                composition_id=self.composition_id,
                timestamp=datetime.now(UTC).isoformat(),
                progress_percent=round(progress_percent, 2),
                current_operation=operation,
                frame=frame,
                fps=round(fps, 2),
                bitrate_kbps=round(bitrate_kbps, 2),
                speed=round(speed, 2),
                eta_seconds=round(eta_seconds, 2) if eta_seconds else None,
                metadata=metadata if metadata else None,
            )

            # Publish to pub/sub channel
            message = update.to_json()
            subscribers = self._redis.publish(self.channel_name, message)

            # Persist progress data in Redis for status queries (with 24h TTL)
            self._redis.setex(
                self.progress_key,
                86400,  # 24 hours
                message,
            )

            # Update last publish time and progress
            self._last_update_time = current_time
            self._last_progress_percent = progress_percent

            logger.debug(
                f"Published progress update: {progress_percent:.1f}%",
                extra={
                    "job_id": self.job_id,
                    "progress": progress_percent,
                    "operation": operation,
                    "subscribers": subscribers,
                },
            )

            return True

        except Exception as e:
            logger.exception(
                "Failed to publish progress update",
                extra={
                    "job_id": self.job_id,
                    "error": str(e),
                },
            )
            return False

    def update_status(
        self,
        status: str,
        message: str | None = None,
        error: str | None = None,
        ttl: int = 86400,
        **extra_data,
    ) -> None:
        """Update job status in Redis.

        Args:
            status: Job status (pending, in_progress, completed, failed, etc.)
            message: Optional status message
            error: Optional error message if failed
            ttl: TTL for status key in seconds (default 24 hours)
            **extra_data: Additional data to include (e.g., output_url)
        """
        try:
            status_data = {
                "job_id": self.job_id,
                "composition_id": self.composition_id,
                "status": status,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            if message:
                status_data["message"] = message

            if error:
                status_data["error"] = error

            # Add any extra data
            status_data.update(extra_data)

            # Store status in Redis with TTL
            self._redis.setex(
                self.status_key,
                ttl,
                json.dumps(status_data),
            )

            # Also publish status change to progress channel
            publish_data = {
                "job_id": self.job_id,
                "type": "status_update",
                "status": status,
                "message": message,
                "error": error,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            if self.composition_id:
                publish_data["composition_id"] = self.composition_id

            # Add extra data (like output_url) to the published message
            publish_data.update(extra_data)

            # LOG THE FULL MESSAGE BEING SENT
            logger.info(
                f"Publishing WebSocket message: {json.dumps(publish_data, indent=2)}",
                extra={"job_id": self.job_id, "has_output_url": "output_url" in publish_data}
            )

            self._redis.publish(
                self.channel_name,
                json.dumps(publish_data),
            )

            logger.info(
                f"Updated job status: {status}",
                extra={
                    "job_id": self.job_id,
                    "status": status,
                    "status_message": message,
                },
            )

        except Exception as e:
            logger.exception(
                "Failed to update job status",
                extra={
                    "job_id": self.job_id,
                    "status": status,
                    "error": str(e),
                },
            )

    def get_current_progress(self) -> dict[str, Any] | None:
        """Get current progress data from Redis.

        Returns:
            dict | None: Current progress data or None if not found
        """
        try:
            data = self._redis.get(self.progress_key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.exception(
                "Failed to get current progress",
                extra={"job_id": self.job_id, "error": str(e)},
            )
            return None

    def get_current_status(self) -> dict[str, Any] | None:
        """Get current job status from Redis.

        Returns:
            dict | None: Current status data or None if not found
        """
        try:
            data = self._redis.get(self.status_key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.exception(
                "Failed to get current status",
                extra={"job_id": self.job_id, "error": str(e)},
            )
            return None

    def cleanup(self) -> None:
        """Clean up progress tracking data from Redis."""
        try:
            # Delete progress and status keys
            self._redis.delete(self.progress_key, self.status_key)

            logger.debug(
                "Cleaned up progress tracking data",
                extra={"job_id": self.job_id},
            )

        except Exception as e:
            logger.warning(
                f"Failed to cleanup progress data: {e}",
                extra={"job_id": self.job_id, "error": str(e)},
            )


class ProgressSubscriber:
    """Subscribes to job progress updates via Redis pub/sub."""

    def __init__(self, job_id: str) -> None:
        """Initialize progress subscriber.

        Args:
            job_id: Job ID to subscribe to
        """
        self.job_id = job_id
        self.channel_name = f"job:progress:{job_id}"
        self._redis = get_redis_connection()
        self._pubsub = self._redis.pubsub()

        logger.info(
            "Initialized ProgressSubscriber",
            extra={"job_id": job_id, "channel": self.channel_name},
        )

    def subscribe(self) -> None:
        """Subscribe to progress updates for the job."""
        self._pubsub.subscribe(self.channel_name)
        logger.debug(f"Subscribed to channel: {self.channel_name}")

    def unsubscribe(self) -> None:
        """Unsubscribe from progress updates."""
        self._pubsub.unsubscribe(self.channel_name)
        logger.debug(f"Unsubscribed from channel: {self.channel_name}")

    def listen(self, timeout: float | None = None) -> Any:
        """Listen for progress updates.

        Args:
            timeout: Optional timeout in seconds

        Yields:
            dict: Progress update messages
        """
        try:
            for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse progress message: {e}")
                        continue

        except Exception as e:
            logger.exception(f"Error listening to progress updates: {e}")
            raise

    def get_message(self, timeout: float = 1.0) -> dict[str, Any] | None:
        """Get a single progress update message.

        Args:
            timeout: Timeout in seconds

        Returns:
            dict | None: Progress update or None if timeout
        """
        try:
            message = self._pubsub.get_message(timeout=timeout)
            if message and message["type"] == "message":
                return json.loads(message["data"])
            return None

        except Exception as e:
            logger.exception(f"Error getting progress message: {e}")
            return None

    def close(self) -> None:
        """Close the pub/sub connection."""
        try:
            self._pubsub.close()
            logger.debug("Closed pub/sub connection")

        except Exception as e:
            logger.warning(f"Error closing pub/sub connection: {e}")
