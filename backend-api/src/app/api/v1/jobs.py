"""Job endpoints for retrieving and managing clip processing jobs."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from workers.redis_pool import get_redis_connection

from ...api.schemas.job import (
    JobCancelResponse,
    JobListResponse,
    JobResponse,
    JobStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_job_data(job_id: str, job_data_str: str) -> JobResponse:
    """Parse job data from Redis string format.

    Args:
        job_id: Job ID
        job_data_str: Job data as string from Redis

    Returns:
        JobResponse: Parsed job response

    Raises:
        ValueError: If job data cannot be parsed
    """
    try:
        # Parse the stored job data
        # Note: The internal API currently stores as str(dict), so we need to parse it
        # In production, this should be JSON serialized
        job_data = eval(job_data_str)  # TODO: Replace with json.loads when storage is updated

        return JobResponse(
            job_id=job_id,
            clip_id=job_data.get("clip_id", ""),
            status=JobStatus(job_data.get("status", "queued")),
            request_id=job_data.get("request_id", ""),
            clip_url=job_data.get("clip_url", ""),
            callback_url=job_data.get("callback_url", ""),
            operations=job_data.get("operations", []),
            processing_options=job_data.get("processing_options", {}),
            metadata=job_data.get("metadata", {}),
            priority=job_data.get("priority", 5),
            queued_at=job_data.get("queued_at", ""),
            started_at=job_data.get("started_at"),
            completed_at=job_data.get("completed_at"),
            processed_url=job_data.get("processed_url"),
            error=job_data.get("error"),
            progress=job_data.get("progress"),
        )
    except (SyntaxError, ValueError, KeyError) as e:
        logger.error(f"Failed to parse job data for {job_id}: {e}")
        raise ValueError(f"Invalid job data format: {e}") from e


@router.get(
    "/",
    response_model=JobListResponse,
    summary="List all jobs",
    description="Retrieve a list of all clip processing jobs with pagination support",
)
async def list_jobs(
    status_filter: JobStatus | None = Query(
        None,
        alias="status",
        description="Filter jobs by status",
    ),
    request_id: str | None = Query(
        None,
        description="Filter jobs by request ID",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Pagination offset",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Pagination limit (max 100)",
    ),
) -> JobListResponse:
    """List all jobs with optional filtering and pagination.

    Args:
        status_filter: Optional status filter
        request_id: Optional request ID filter
        offset: Pagination offset
        limit: Pagination limit

    Returns:
        JobListResponse: List of jobs with pagination info

    Raises:
        HTTPException: If Redis connection fails
    """
    try:
        redis_conn = get_redis_connection()

        # Get all job keys
        job_keys = redis_conn.keys("clip_job:*")

        jobs: list[JobResponse] = []

        for job_key in job_keys:
            try:
                job_id = job_key.decode("utf-8").replace("clip_job:", "")
                job_data_str = redis_conn.get(job_key)

                if not job_data_str:
                    continue

                job_data_str = job_data_str.decode("utf-8")
                job = parse_job_data(job_id, job_data_str)

                # Apply filters
                if status_filter and job.status != status_filter:
                    continue
                if request_id and job.request_id != request_id:
                    continue

                jobs.append(job)

            except Exception as e:
                logger.warning(f"Failed to parse job {job_key}: {e}")
                continue

        # Sort by queued_at (most recent first)
        jobs.sort(key=lambda x: x.queued_at, reverse=True)

        # Apply pagination
        total = len(jobs)
        paginated_jobs = jobs[offset : offset + limit]

        logger.info(
            f"Listed {len(paginated_jobs)} jobs (total: {total})",
            extra={
                "offset": offset,
                "limit": limit,
                "status_filter": status_filter,
                "request_id": request_id,
            },
        )

        return JobListResponse(
            jobs=paginated_jobs,
            total=total,
            offset=offset,
            limit=limit,
        )

    except Exception as e:
        logger.exception("Failed to list jobs", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve jobs from storage",
        ) from e


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
    description="Retrieve detailed information about a specific clip processing job",
)
async def get_job(job_id: str) -> JobResponse:
    """Get a specific job by ID.

    Args:
        job_id: Job identifier

    Returns:
        JobResponse: Job details

    Raises:
        HTTPException: If job not found or Redis connection fails
    """
    try:
        redis_conn = get_redis_connection()

        # Get job data from Redis
        job_key = f"clip_job:{job_id}"
        job_data_str = redis_conn.get(job_key)

        if not job_data_str:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        job_data_str = job_data_str.decode("utf-8")
        job = parse_job_data(job_id, job_data_str)

        logger.info(f"Retrieved job {job_id}", extra={"status": job.status})

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get job {job_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve job from storage",
        ) from e


@router.post(
    "/{job_id}/cancel",
    response_model=JobCancelResponse,
    summary="Cancel a job",
    description="Cancel a queued or processing clip job",
)
async def cancel_job(job_id: str) -> JobCancelResponse:
    """Cancel a specific job.

    Args:
        job_id: Job identifier

    Returns:
        JobCancelResponse: Cancellation result

    Raises:
        HTTPException: If job not found, already completed, or Redis connection fails
    """
    try:
        redis_conn = get_redis_connection()

        # Get job data from Redis
        job_key = f"clip_job:{job_id}"
        job_data_str = redis_conn.get(job_key)

        if not job_data_str:
            logger.warning(f"Job not found for cancellation: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )

        job_data_str = job_data_str.decode("utf-8")
        job = parse_job_data(job_id, job_data_str)

        # Check if job can be cancelled
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            logger.warning(
                f"Cannot cancel job {job_id} with status {job.status}",
                extra={"status": job.status},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status {job.status}",
            )

        # Update job status to cancelled
        job_data = eval(job_data_str)  # TODO: Replace with json.loads
        job_data["status"] = "cancelled"
        job_data["completed_at"] = datetime.now(UTC).isoformat()
        job_data["error"] = "Job cancelled by user"

        # Save updated job data
        redis_conn.setex(
            job_key,
            86400,  # Keep cancelled jobs for 24 hours
            str(job_data),  # TODO: Replace with json.dumps
        )

        cancelled_at = job_data["completed_at"]

        logger.info(f"Cancelled job {job_id}", extra={"previous_status": job.status})

        return JobCancelResponse(
            job_id=job_id,
            status=JobStatus.CANCELLED,
            message=f"Job {job_id} has been cancelled",
            cancelled_at=cancelled_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to cancel job {job_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to cancel job",
        ) from e
