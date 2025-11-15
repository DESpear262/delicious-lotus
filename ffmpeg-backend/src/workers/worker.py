"""RQ worker entry point with multi-queue support and configuration."""

import logging
import signal
import sys
import time
from typing import Any

from app.config import settings
from rq import Queue, Worker
from rq.job import Job

from workers.redis_pool import get_redis_connection, redis_connection_manager

logger = logging.getLogger(__name__)

# Global shutdown flag
_shutdown_requested = False
_active_worker: Worker | None = None

# Queue names with priority ordering
QUEUE_HIGH = "high"
QUEUE_DEFAULT = "default"
QUEUE_LOW = "low"

# Queue priority ordering (first queue has highest priority)
QUEUE_PRIORITY = [QUEUE_HIGH, QUEUE_DEFAULT, QUEUE_LOW]


class VideoWorker(Worker):
    """Custom RQ Worker with enhanced logging, monitoring, and graceful shutdown."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize VideoWorker with custom configuration.

        Args:
            *args: Positional arguments passed to Worker
            **kwargs: Keyword arguments passed to Worker
        """
        super().__init__(*args, **kwargs)
        self._shutdown_timeout = 300  # 5 minutes for graceful shutdown
        self._active_jobs: set[str] = set()

        self.log.info(
            "Initialized VideoWorker",
            extra={
                "worker_name": self.name,
                "queues": [q.name for q in self.queues],
                "shutdown_timeout": self._shutdown_timeout,
            },
        )

    def execute_job(self, job: Job, queue: Queue) -> bool:
        """Execute a job with enhanced logging and shutdown handling.

        Args:
            job: Job to execute
            queue: Queue the job came from

        Returns:
            bool: True if job executed successfully
        """
        # Track active job
        self._active_jobs.add(job.id)

        self.log.info(
            f"Starting job execution: {job.id}",
            extra={
                "job_id": job.id,
                "job_func": job.func_name,
                "queue": queue.name,
                "timeout": job.timeout,
                "created_at": job.created_at.isoformat() if job.created_at else None,
            },
        )

        try:
            result = super().execute_job(job, queue)

            self.log.info(
                f"Completed job execution: {job.id}",
                extra={
                    "job_id": job.id,
                    "job_func": job.func_name,
                    "queue": queue.name,
                    "result": str(result)[:200],  # Truncate long results
                },
            )

            return result

        except Exception as e:
            self.log.exception(
                f"Job execution failed: {job.id}",
                extra={
                    "job_id": job.id,
                    "job_func": job.func_name,
                    "queue": queue.name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

        finally:
            # Remove from active jobs
            self._active_jobs.discard(job.id)

    def handle_job_failure(self, job: Job, **exc_info: Any) -> None:
        """Handle job failure with enhanced logging.

        Args:
            job: Failed job
            **exc_info: Exception information
        """
        super().handle_job_failure(job, **exc_info)

        self.log.error(
            f"Job failed: {job.id}",
            extra={
                "job_id": job.id,
                "job_func": job.func_name,
                "retry_attempts": job.retries_left if hasattr(job, "retries_left") else 0,
                "exception_type": exc_info.get("exc_type"),
                "exception_value": str(exc_info.get("exc_value"))[:500],
            },
        )

    def handle_job_success(self, job: Job, queue: Queue, started_job_registry: Any) -> None:
        """Handle job success with enhanced logging.

        Args:
            job: Successful job
            queue: Queue the job came from
            started_job_registry: Started job registry
        """
        super().handle_job_success(job, queue, started_job_registry)

        self.log.info(
            f"Job succeeded: {job.id}",
            extra={
                "job_id": job.id,
                "job_func": job.func_name,
                "queue": queue.name,
                "execution_time": (
                    (job.ended_at - job.started_at).total_seconds()
                    if job.ended_at and job.started_at
                    else None
                ),
            },
        )

    def request_stop(self, signum: int | None = None, frame: Any | None = None) -> None:
        """Request graceful shutdown of worker.

        Args:
            signum: Signal number (from signal handler)
            frame: Current stack frame (from signal handler)
        """
        global _shutdown_requested

        if _shutdown_requested:
            self.log.warning("Shutdown already requested, forcing termination")
            self.request_force_stop()
            return

        _shutdown_requested = True

        signal_name = signal.Signals(signum).name if signum else "UNKNOWN"

        self.log.warning(
            f"Received shutdown signal {signal_name}, initiating graceful shutdown",
            extra={
                "signal": signal_name,
                "active_jobs": len(self._active_jobs),
                "shutdown_timeout": self._shutdown_timeout,
            },
        )

        # Call parent's request_stop
        super().request_stop(signum, frame)

    def cleanup_resources(self) -> None:
        """Clean up worker resources during shutdown."""
        self.log.info("Cleaning up worker resources")

        try:
            # Close Redis connections
            self.log.debug("Closing Redis connections")
            redis_connection_manager.close()

            # Clean up temp files (if any)
            from pathlib import Path

            temp_dir = Path(settings.temp_dir)
            if temp_dir.exists():
                self.log.debug(f"Cleaning up temp directory: {temp_dir}")
                # Don't delete everything, just mark for cleanup
                # The cleanup job will handle actual deletion

            self.log.info("Resource cleanup completed")

        except Exception as e:
            self.log.exception(f"Error during resource cleanup: {e}")

    def shutdown_with_timeout(self, timeout: int | None = None) -> None:
        """Shutdown worker with timeout for active jobs.

        Args:
            timeout: Timeout in seconds (defaults to _shutdown_timeout)
        """
        timeout = timeout or self._shutdown_timeout
        start_time = time.time()

        self.log.info(
            f"Waiting for {len(self._active_jobs)} active jobs to complete",
            extra={
                "active_jobs": len(self._active_jobs),
                "timeout": timeout,
                "job_ids": list(self._active_jobs),
            },
        )

        # Wait for active jobs to complete
        while self._active_jobs and (time.time() - start_time) < timeout:
            time.sleep(1)

            # Log progress every 10 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0:
                self.log.info(
                    f"Still waiting for {len(self._active_jobs)} jobs (elapsed: {elapsed:.0f}s)",
                    extra={"active_jobs": len(self._active_jobs), "elapsed": elapsed},
                )

        # Check if we timed out
        if self._active_jobs:
            self.log.warning(
                f"Shutdown timeout reached with {len(self._active_jobs)} jobs still active",
                extra={
                    "remaining_jobs": len(self._active_jobs),
                    "job_ids": list(self._active_jobs),
                },
            )
        else:
            self.log.info("All active jobs completed successfully")

        # Clean up resources
        self.cleanup_resources()

        # Report final status
        self.log.info(
            "Worker shutdown complete",
            extra={
                "total_shutdown_time": time.time() - start_time,
                "incomplete_jobs": len(self._active_jobs),
            },
        )


def create_queues(connection: Any) -> list[Queue]:
    """Create RQ queues with proper configuration.

    Args:
        connection: Redis connection instance

    Returns:
        list[Queue]: List of configured queues in priority order
    """
    queues = []

    for queue_name in QUEUE_PRIORITY:
        queue = Queue(
            name=queue_name,
            connection=connection,
            default_timeout=settings.rq_default_timeout,
        )
        queues.append(queue)

        logger.info(
            f"Created queue: {queue_name}",
            extra={
                "queue_name": queue_name,
                "default_timeout": settings.rq_default_timeout,
            },
        )

    return queues


def get_worker_name() -> str:
    """Generate a unique worker name.

    Returns:
        str: Worker name with hostname and PID
    """
    import os
    import socket

    hostname = socket.gethostname()
    pid = os.getpid()
    return f"video-worker-{hostname}-{pid}"


def create_worker(
    queues: list[Queue],
    connection: Any,
    worker_name: str | None = None,
) -> VideoWorker:
    """Create and configure an RQ worker.

    Args:
        queues: List of queues to process
        connection: Redis connection instance
        worker_name: Custom worker name (optional)

    Returns:
        VideoWorker: Configured worker instance
    """
    if worker_name is None:
        worker_name = get_worker_name()

    worker = VideoWorker(
        queues=queues,
        connection=connection,
        name=worker_name,
        # Worker configuration
        default_result_ttl=settings.rq_result_ttl,
        default_worker_ttl=420,  # 7 minutes
        # Job configuration
        job_monitoring_interval=10,  # Check for new jobs every 10 seconds
    )

    logger.info(
        "Created worker",
        extra={
            "worker_name": worker_name,
            "queues": [q.name for q in queues],
            "result_ttl": settings.rq_result_ttl,
            "failure_ttl": settings.rq_failure_ttl,
        },
    )

    return worker


def _shutdown_handler(signum: int, frame: Any) -> None:
    """Global shutdown signal handler.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global _active_worker

    signal_name = signal.Signals(signum).name

    logger.warning(
        f"Received {signal_name} signal, initiating graceful shutdown",
        extra={"signal": signal_name},
    )

    if _active_worker:
        _active_worker.request_stop(signum, frame)


def start_worker(
    worker_name: str | None = None,
    burst: bool = False,
    logging_level: str = "INFO",
) -> None:
    """Start the RQ worker to process jobs from queues with graceful shutdown.

    Args:
        worker_name: Custom worker name (optional)
        burst: Run in burst mode (process available jobs then exit)
        logging_level: Logging level for worker

    Raises:
        SystemExit: On worker shutdown
    """
    global _active_worker

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, logging_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("Starting RQ worker with graceful shutdown support")

    try:
        # Get Redis connection
        redis_conn = get_redis_connection()
        logger.info("Connected to Redis successfully")

        # Create queues in priority order
        queues = create_queues(redis_conn)

        # Create worker
        worker = create_worker(queues, redis_conn, worker_name)
        _active_worker = worker

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, _shutdown_handler)
        signal.signal(signal.SIGINT, _shutdown_handler)

        logger.info(
            "Signal handlers registered for graceful shutdown",
            extra={"signals": ["SIGTERM", "SIGINT"]},
        )

        # Log worker configuration
        logger.info(
            "Worker configuration",
            extra={
                "worker_name": worker.name,
                "queues": QUEUE_PRIORITY,
                "burst_mode": burst,
                "log_level": logging_level,
                "redis_url": str(settings.redis_url),
            },
        )

        # Start processing jobs
        logger.info(
            f"Worker {worker.name} starting - listening to queues: {', '.join(QUEUE_PRIORITY)}"
        )

        try:
            worker.work(
                burst=burst,
                logging_level=logging_level,
                with_scheduler=False,  # We'll use a separate scheduler process if needed
            )

        except (KeyboardInterrupt, SystemExit):
            logger.info("Worker interrupted, initiating graceful shutdown")

            # Perform graceful shutdown with timeout
            worker.shutdown_with_timeout()

            logger.info("Worker shutdown completed")
            sys.exit(0)

    except Exception as e:
        logger.exception(
            "Worker failed to start",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        sys.exit(1)

    finally:
        # Clean up global reference
        _active_worker = None


def enqueue_job(
    func: Any,
    args: tuple = (),
    kwargs: dict | None = None,
    queue_name: str = QUEUE_DEFAULT,
    job_timeout: int | None = None,
    result_ttl: int | None = None,
    failure_ttl: int | None = None,
    job_id: str | None = None,
    description: str | None = None,
) -> Job:
    """Enqueue a job to be processed by a worker.

    Args:
        func: Function to execute
        args: Positional arguments for function
        kwargs: Keyword arguments for function
        queue_name: Queue to enqueue to (high, default, low)
        job_timeout: Job execution timeout in seconds
        result_ttl: How long to keep job result (seconds)
        failure_ttl: How long to keep failed job info (seconds)
        job_id: Custom job ID (optional)
        description: Job description (optional)

    Returns:
        Job: Enqueued job instance

    Raises:
        ValueError: If queue_name is invalid
    """
    if queue_name not in QUEUE_PRIORITY:
        raise ValueError(f"Invalid queue name: {queue_name}. Must be one of {QUEUE_PRIORITY}")

    redis_conn = get_redis_connection()
    queue = Queue(name=queue_name, connection=redis_conn)

    job = queue.enqueue(
        func,
        args=args,
        kwargs=kwargs or {},
        job_timeout=job_timeout or settings.rq_default_timeout,
        result_ttl=result_ttl or settings.rq_result_ttl,
        failure_ttl=failure_ttl or settings.rq_failure_ttl,
        job_id=job_id,
        description=description,
    )

    logger.info(
        f"Enqueued job: {job.id}",
        extra={
            "job_id": job.id,
            "job_func": func.__name__ if hasattr(func, "__name__") else str(func),
            "queue": queue_name,
            "timeout": job.timeout,
            "description": description,
        },
    )

    return job


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start RQ worker for video processing")
    parser.add_argument(
        "--name",
        type=str,
        help="Custom worker name",
        default=None,
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Run in burst mode (process available jobs then exit)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    args = parser.parse_args()

    start_worker(
        worker_name=args.name,
        burst=args.burst,
        logging_level=args.log_level,
    )
