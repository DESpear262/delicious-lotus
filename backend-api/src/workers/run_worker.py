#!/usr/bin/env python3
"""RQ worker script for processing background jobs.

This script starts an RQ worker that listens to specified queues
and processes background jobs like video imports, thumbnail generation, etc.

Usage:
    python -m workers.run_worker

Environment variables:
    REDIS_URL: Redis connection URL (default: redis://localhost:6379/0)
    WORKER_QUEUES: Comma-separated list of queues to listen on (default: media_import,default)
    WORKER_NAME: Worker name for identification (default: auto-generated)
"""

import logging
import os
import sys

from rq import Worker
from rq.queue import Queue
from workers.redis_pool import get_redis_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """Start RQ worker."""
    # Get queue names from environment or use defaults
    queue_names = os.getenv("WORKER_QUEUES", "media_import,default").split(",")
    queue_names = [q.strip() for q in queue_names if q.strip()]

    # Get worker name from environment or use default
    worker_name = os.getenv("WORKER_NAME", None)

    logger.info(
        "Starting RQ worker",
        extra={
            "queues": queue_names,
            "worker_name": worker_name or "auto",
        },
    )

    try:
        # Get Redis connection for worker (binary mode for RQ pickle serialization)
        redis_conn = get_redis_connection(for_worker=True)

        # Test Redis connection
        redis_conn.ping()
        logger.info("Redis connection established")

        # Create queue objects
        queues = [Queue(name, connection=redis_conn) for name in queue_names]

        # Start worker
        worker = Worker(
            queues,
            name=worker_name,
            connection=redis_conn,
        )

        logger.info(
            f"Worker '{worker.name}' started, listening on queues: {', '.join(queue_names)}"
        )

        # Run worker (blocks until stopped)
        worker.work(with_scheduler=True)

    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
