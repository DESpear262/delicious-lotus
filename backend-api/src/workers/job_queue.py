"""Job queue management using Redis Queue (RQ) for background tasks."""

import logging
import uuid

from rq import Queue
from workers.redis_pool import get_redis_connection

logger = logging.getLogger(__name__)

# Job queue names
MEDIA_IMPORT_QUEUE = "media_import"
DEFAULT_QUEUE = "default"

# Job timeout (seconds)
DEFAULT_JOB_TIMEOUT = 600  # 10 minutes
VIDEO_IMPORT_TIMEOUT = 1800  # 30 minutes for video processing


def get_queue(name: str = DEFAULT_QUEUE) -> Queue:
    """Get RQ queue instance.

    Args:
        name: Queue name (default: "default")

    Returns:
        Queue: RQ Queue instance
    """
    redis_conn = get_redis_connection()
    return Queue(name, connection=redis_conn)


def enqueue_video_import(
    url: str,
    name: str,
    user_id: str,
    asset_id: str,
    metadata: dict | None = None,
) -> str:
    """Enqueue a video import job.

    Args:
        url: External URL to download video from
        name: Filename for the video
        user_id: User UUID string
        asset_id: MediaAsset UUID string
        metadata: Optional additional metadata dict

    Returns:
        str: Job ID for tracking

    Raises:
        Exception: If job enqueue fails
    """
    from workers.video_import_job import import_video_from_url_job

    queue = get_queue(MEDIA_IMPORT_QUEUE)

    job = queue.enqueue(
        import_video_from_url_job,
        url=url,
        name=name,
        user_id=user_id,
        asset_id=asset_id,
        metadata=metadata,
        job_timeout=VIDEO_IMPORT_TIMEOUT,
        result_ttl=86400,  # Keep result for 24 hours
        failure_ttl=86400,  # Keep failed job info for 24 hours
    )

    logger.info(
        f"Enqueued video import job: {job.id}",
        extra={
            "job_id": job.id,
            "asset_id": asset_id,
            "url": url,
        },
    )

    return job.id


def enqueue_image_import(
    url: str,
    name: str,
    user_id: str,
    asset_id: str,
    metadata: dict | None = None,
) -> str:
    """Enqueue an image import job.

    Args:
        url: External URL to download image from
        name: Filename for the image
        user_id: User UUID string
        asset_id: MediaAsset UUID string
        metadata: Optional additional metadata dict

    Returns:
        str: Job ID for tracking

    Raises:
        Exception: If job enqueue fails
    """
    from workers.video_import_job import import_image_from_url_job

    queue = get_queue(MEDIA_IMPORT_QUEUE)

    job = queue.enqueue(
        import_image_from_url_job,
        url=url,
        name=name,
        user_id=user_id,
        asset_id=asset_id,
        metadata=metadata,
        job_timeout=DEFAULT_JOB_TIMEOUT,
        result_ttl=86400,
        failure_ttl=86400,
    )

    logger.info(
        f"Enqueued image import job: {job.id}",
        extra={
            "job_id": job.id,
            "asset_id": asset_id,
            "url": url,
        },
    )

    return job.id


def enqueue_ken_burns_video_generation(
    image_urls: list[str],
    duration: float,
    user_id: str,
    width: int | None = None,
    height: int | None = None,
) -> str:
    """Enqueue a Ken Burns video generation job.

    Args:
        image_urls: List of image URLs
        duration: Total duration of the video
        user_id: User ID
        width: Optional target video width
        height: Optional target video height

    Returns:
        str: Job ID for tracking
    """
    from workers.ken_burns_worker import create_video_from_images_job

    queue = get_queue(MEDIA_IMPORT_QUEUE) # Reuse media import queue or use default
    
    tracking_id = str(uuid.uuid4())

    job = queue.enqueue(
        create_video_from_images_job,
        image_urls=image_urls,
        duration=duration,
        user_id=user_id,
        tracking_id=tracking_id, # Pass tracking_id to the worker function
        job_id=tracking_id, # Use our generated ID as the logical RQ job ID
        width=width,
        height=height,
        job_timeout=VIDEO_IMPORT_TIMEOUT,
        result_ttl=86400,
    )

    logger.info(
        f"Enqueued Ken Burns job: {job.id}",
        extra={
            "job_id": job.id,
            "tracking_id": tracking_id,
            "user_id": user_id,
            "image_count": len(image_urls),
            "width": width,
            "height": height,
        },
    )

    return job.id


def get_job_status(job_id: str) -> dict:
    """Get status of a background job.

    Args:
        job_id: Job ID returned from enqueue

    Returns:
        dict: Job status with keys:
            - status: "queued", "started", "finished", "failed", "canceled", "not_found"
            - result: Job result if finished
            - error: Error message if failed
            - progress: Progress info if available
    """
    from rq.job import Job

    redis_conn = get_redis_connection()

    try:
        job = Job.fetch(job_id, connection=redis_conn)

        status = job.get_status()
        result = None
        error = None

        if status == "finished":
            result = job.result
        elif status == "failed":
            error = str(job.exc_info) if job.exc_info else "Unknown error"

        return {
            "status": status,
            "result": result,
            "error": error,
            "progress": job.meta.get("progress") if hasattr(job, "meta") else None,
        }

    except Exception as e:
        logger.warning(f"Failed to fetch job {job_id}: {e}")
        return {
            "status": "not_found",
            "result": None,
            "error": str(e),
            "progress": None,
        }


def cancel_job(job_id: str) -> bool:
    """Cancel a queued or running job.

    Args:
        job_id: Job ID to cancel

    Returns:
        bool: True if canceled, False otherwise
    """
    from rq.job import Job

    redis_conn = get_redis_connection()

    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        logger.info(f"Canceled job: {job_id}")
        return True

    except Exception as e:
        logger.warning(f"Failed to cancel job {job_id}: {e}")
        return False
