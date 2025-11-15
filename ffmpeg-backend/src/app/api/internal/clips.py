"""Internal API endpoints for clip processing."""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from workers.redis_pool import get_redis_connection

from ...dependencies import require_internal_auth
from ..schemas.internal import (
    ProcessClipsRequest,
    ProcessClipsResponse,
    ProcessingJobInfo,
    ProcessingJobStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_request_id() -> str:
    """Generate unique request ID.

    Returns:
        str: Unique request ID in format 'req_<uuid>'
    """
    return f"req_{uuid.uuid4().hex[:16]}"


def generate_job_id(clip_id: str) -> str:
    """Generate unique job ID for a clip.

    Args:
        clip_id: Original clip ID from request

    Returns:
        str: Unique job ID in format 'job_<clip_id>_<uuid>'
    """
    # Sanitize clip_id to ensure it's safe for job ID
    safe_clip_id = clip_id.replace("/", "_").replace("\\", "_")[:50]
    return f"job_{safe_clip_id}_{uuid.uuid4().hex[:8]}"


def validate_callback_url_reachability(callback_url: str) -> bool:
    """Validate that callback URL is reachable (basic check).

    Args:
        callback_url: URL to validate

    Returns:
        bool: True if URL appears valid

    Note:
        This is a basic validation. In production, you might want to:
        - Verify DNS resolution
        - Check if port is open
        - Perform test HTTP request
        For now, we just validate the format via Pydantic
    """
    # Additional validation logic can be added here
    # For example, DNS lookup, port check, etc.
    return True


@router.post(
    "/process-clips",
    response_model=ProcessClipsResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process video clips",
    description="Submit clips for processing with normalization, codec conversion, and thumbnail generation",
    dependencies=[Depends(require_internal_auth)],
)
async def process_clips(
    request_body: ProcessClipsRequest,
    request: Request,
) -> ProcessClipsResponse:
    """Process clips with specified operations.

    This endpoint accepts clip URLs and processing options, enqueues jobs
    for processing, and returns job IDs for tracking. When processing completes,
    a callback will be sent to the provided callback URL.

    Args:
        request_body: Processing request with clips, callback URL, and options
        request: FastAPI request object

    Returns:
        ProcessClipsResponse: Response with request ID and job information

    Raises:
        HTTPException: If validation fails or enqueueing fails
    """
    # Generate unique request ID
    request_id = generate_request_id()

    # Get authentication context from middleware
    auth_context = getattr(request.state, "auth_method", "unknown")

    logger.info(
        "Processing clips request received",
        extra={
            "request_id": request_id,
            "num_clips": len(request_body.clips),
            "auth_method": auth_context,
            "callback_url": str(request_body.callback_url),
            "operations": [op.value for op in request_body.operations],
        },
    )

    # Validate callback URL reachability
    if not validate_callback_url_reachability(str(request_body.callback_url)):
        logger.warning(
            "Callback URL validation failed",
            extra={"request_id": request_id, "callback_url": str(request_body.callback_url)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Callback URL is not reachable",
        )

    # Get Redis connection for job queue
    try:
        redis_conn = get_redis_connection()
        # queue = Queue("clip_processing", connection=redis_conn)  # TODO: Implement RQ worker
    except Exception as e:
        logger.exception(
            "Failed to connect to job queue",
            extra={"request_id": request_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job queue unavailable",
        ) from e

    # Enqueue processing jobs for each clip
    jobs: list[ProcessingJobInfo] = []
    queued_at = datetime.now(UTC).isoformat()

    for clip in request_body.clips:
        try:
            # Generate unique job ID
            job_id = generate_job_id(clip.clip_id)

            # Prepare job data
            job_data = {
                "request_id": request_id,
                "job_id": job_id,
                "clip_id": clip.clip_id,
                "clip_url": str(clip.url),
                "callback_url": str(request_body.callback_url),
                "operations": [op.value for op in request_body.operations],
                "processing_options": request_body.processing_options.model_dump(),
                "metadata": clip.metadata,
                "priority": request_body.priority,
                "queued_at": queued_at,
            }

            # Enqueue job (for now, we'll create a placeholder)
            # In the future, this will call actual worker function
            # job = queue.enqueue(
            #     'workers.clip_processor.process_clip',
            #     job_data,
            #     job_id=job_id,
            #     timeout='1h',
            #     result_ttl=86400,  # Keep results for 24 hours
            # )

            # For now, store job data in Redis for tracking
            job_key = f"clip_job:{job_id}"
            redis_conn.setex(
                job_key,
                86400,  # 24 hour TTL
                str(job_data),  # In production, use JSON serialization
            )

            jobs.append(
                ProcessingJobInfo(
                    job_id=job_id,
                    clip_id=clip.clip_id,
                    status=ProcessingJobStatus.QUEUED,
                    queued_at=queued_at,
                )
            )

            logger.info(
                "Clip processing job enqueued",
                extra={
                    "request_id": request_id,
                    "job_id": job_id,
                    "clip_id": clip.clip_id,
                },
            )

        except Exception as e:
            logger.exception(
                "Failed to enqueue clip processing job",
                extra={
                    "request_id": request_id,
                    "clip_id": clip.clip_id,
                    "error": str(e),
                },
            )
            # Continue with other clips, but log the error
            # In production, you might want to fail the entire request
            # or return partial success
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to enqueue job for clip {clip.clip_id}",
            ) from e

    # Store request metadata for callback tracking
    request_key = f"clip_request:{request_id}"
    request_metadata = {
        "request_id": request_id,
        "callback_url": str(request_body.callback_url),
        "total_clips": len(request_body.clips),
        "job_ids": [job.job_id for job in jobs],
        "queued_at": queued_at,
    }
    redis_conn.setex(
        request_key,
        86400,  # 24 hour TTL
        str(request_metadata),  # In production, use JSON serialization
    )

    logger.info(
        "All clips queued successfully",
        extra={
            "request_id": request_id,
            "total_clips": len(jobs),
        },
    )

    return ProcessClipsResponse(
        request_id=request_id,
        jobs=jobs,
        total_clips=len(request_body.clips),
        message=f"Successfully queued {len(jobs)} clip(s) for processing",
    )
