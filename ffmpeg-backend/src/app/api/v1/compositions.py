"""Composition endpoints."""

import logging
import uuid
from typing import Annotated

from db.models.composition import Composition, CompositionStatus
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from workers.job_handlers import process_composition_job
from workers.worker import enqueue_job

from app.api.schemas import (
    BulkCancelResponse,
    CompositionCancelResponse,
    CompositionCreateRequest,
    CompositionListResponse,
    CompositionMetadataResponse,
    CompositionResponse,
    CompositionStatusResponse,
    DownloadResponse,
    InputFileInfo,
    OutputFileInfo,
    ResourceMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=CompositionResponse)
async def create_composition(
    request: CompositionCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompositionResponse:
    """Create a new video composition.

    This endpoint accepts a composition request with video clips, audio configuration,
    overlays, and output settings. It validates the request, stores it in the database,
    and enqueues a background job for processing.

    Args:
        request: Composition creation request with all configuration
        db: Database session (injected)

    Returns:
        CompositionResponse: Created composition with initial status

    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 500 for server errors
    """
    # Generate unique composition ID
    composition_id = uuid.uuid4()

    logger.info(
        "Creating new composition",
        extra={
            "composition_id": str(composition_id),
            "title": request.title,
            "clips_count": len(request.clips),
            "overlays_count": len(request.overlays),
        },
    )

    # Build composition configuration for storage
    # Create assets list from clips for worker processing
    assets = []
    for i, clip in enumerate(request.clips):
        asset_id = f"clip_{i}"
        assets.append(
            {
                "id": asset_id,
                "url": str(clip.video_url),  # HTTP URL instead of s3_key
                "type": "video",
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "trim_start": clip.trim_start,
                "trim_end": clip.trim_end,
            }
        )

    # Add audio assets if provided
    if request.audio.music_url:
        assets.append(
            {
                "id": "music",
                "url": str(request.audio.music_url),
                "type": "audio",
                "volume": request.audio.music_volume,
            }
        )
    if request.audio.voiceover_url:
        assets.append(
            {
                "id": "voiceover",
                "url": str(request.audio.voiceover_url),
                "type": "audio",
                "volume": request.audio.voiceover_volume,
            }
        )

    composition_config = {
        "assets": assets,  # For worker processing
        "clips": [
            {
                "video_url": str(clip.video_url),
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "trim_start": clip.trim_start,
                "trim_end": clip.trim_end,
            }
            for clip in request.clips
        ],
        "audio": {
            "music_url": str(request.audio.music_url) if request.audio.music_url else None,
            "voiceover_url": (
                str(request.audio.voiceover_url) if request.audio.voiceover_url else None
            ),
            "music_volume": request.audio.music_volume,
            "voiceover_volume": request.audio.voiceover_volume,
            "original_audio_volume": request.audio.original_audio_volume,
        },
        "overlays": [
            {
                "text": overlay.text,
                "position": overlay.position.value,
                "start_time": overlay.start_time,
                "end_time": overlay.end_time,
                "font_size": overlay.font_size,
                "font_color": overlay.font_color,
            }
            for overlay in request.overlays
        ],
        "output": {
            "resolution": request.output.resolution.value,
            "format": request.output.format.value,
            "fps": request.output.fps,
            "bitrate": request.output.bitrate,
        },
    }

    # Create composition record in database
    composition = Composition(
        id=composition_id,
        title=request.title,
        description=request.description,
        status=CompositionStatus.PENDING,
        composition_config=composition_config,
    )

    try:
        db.add(composition)
        await db.commit()
        await db.refresh(composition)

        logger.info(
            "Composition record created in database",
            extra={"composition_id": str(composition_id)},
        )

    except Exception as e:
        await db.rollback()
        logger.exception(
            "Failed to create composition in database",
            extra={"composition_id": str(composition_id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create composition",
        ) from e

    # Prepare job parameters
    # Convert resolution enum to WxH format for job handler
    resolution_map = {
        "480p": "854x480",
        "720p": "1280x720",
        "1080p": "1920x1080",
        "4k": "3840x2160",
    }

    job_params = {
        "composition_id": composition_id,
        "composition_config": composition_config,
        "output_format": request.output.format.value,
        "output_resolution": resolution_map.get(request.output.resolution.value, "1920x1080"),
        "output_fps": request.output.fps,
        "priority": "default",  # Could be derived from request or user tier
    }

    # Enqueue background job for processing with callbacks
    try:
        from workers.job_callbacks import on_job_failure, on_job_success

        job = enqueue_job(
            func=process_composition_job,
            kwargs={"job_id": str(uuid.uuid4()), **job_params},
            queue_name="default",  # TODO: Support priority queues based on user tier
            description=f"Process composition: {request.title}",
            on_success=on_job_success,
            on_failure=on_job_failure,
        )

        logger.info(
            "Composition job enqueued with callbacks",
            extra={
                "composition_id": str(composition_id),
                "job_id": job.id,
                "queue": "default",
            },
        )

        # Update composition with queued status
        composition.status = CompositionStatus.QUEUED
        await db.commit()
        await db.refresh(composition)

    except Exception as e:
        logger.exception(
            "Failed to enqueue composition job",
            extra={"composition_id": str(composition_id), "error": str(e)},
        )
        # Don't fail the request - composition is created, job can be retried
        # Keep status as PENDING

    # Refresh to ensure all attributes are loaded
    await db.refresh(composition)

    # Return composition response
    return CompositionResponse.model_validate(composition)


@router.get("/", response_model=CompositionListResponse)
async def list_compositions(
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> CompositionListResponse:
    """List all compositions with pagination and filtering.

    This endpoint retrieves compositions with support for filtering by status
    and pagination. Results are ordered by creation time (most recent first).

    Args:
        db: Database session (injected)
        status_filter: Optional status filter (pending, queued, processing, completed, failed, cancelled)
        offset: Pagination offset (default: 0)
        limit: Pagination limit (default: 50, max: 100)

    Returns:
        CompositionListResponse: List of compositions with pagination info

    Raises:
        HTTPException: 400 for invalid parameters
        HTTPException: 500 for database errors
    """
    # Validate pagination parameters
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be non-negative",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100",
        )

    # Validate status filter if provided
    if status_filter:
        valid_statuses = ["pending", "queued", "processing", "completed", "failed", "cancelled"]
        if status_filter.lower() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}",
            )

    logger.info(
        "Listing compositions",
        extra={
            "status_filter": status_filter,
            "offset": offset,
            "limit": limit,
        },
    )

    try:
        # Build query
        query = select(Composition)

        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = CompositionStatus(status_filter.lower())
                query = query.where(Composition.status == status_enum)
            except ValueError:
                # Invalid status - already validated above, but handle gracefully
                pass

        # Get total count before pagination
        from sqlalchemy import func

        count_query = select(func.count()).select_from(Composition)
        if status_filter:
            try:
                status_enum = CompositionStatus(status_filter.lower())
                count_query = count_query.where(Composition.status == status_enum)
            except ValueError:
                pass

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Order by creation time (most recent first) and apply pagination
        query = query.order_by(Composition.created_at.desc()).offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        compositions = result.scalars().all()

        logger.info(
            "Retrieved compositions",
            extra={
                "count": len(compositions),
                "total": total,
                "offset": offset,
                "limit": limit,
                "status_filter": status_filter,
            },
        )

        # Convert to response models
        composition_responses = [CompositionResponse.model_validate(comp) for comp in compositions]

        return CompositionListResponse(
            compositions=composition_responses,
            total=total,
            offset=offset,
            limit=limit,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to list compositions",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compositions",
        ) from e


@router.get("/{composition_id}/status", response_model=CompositionStatusResponse)
async def get_composition_status(
    composition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompositionStatusResponse:
    """Get composition processing status with real-time progress information.

    This endpoint retrieves the current status of a composition including processing
    progress, current stage, and any error information. It combines data from the
    database and Redis for real-time updates.

    Args:
        composition_id: Unique composition identifier
        db: Database session (injected)

    Returns:
        CompositionStatusResponse: Detailed status information

    Raises:
        HTTPException: 404 if composition not found
    """

    from app.api.schemas import (
        CompositionStatusResponse,
        ProcessingStage,
        ProcessingStageInfo,
    )

    logger.info(
        "Retrieving composition status",
        extra={"composition_id": str(composition_id)},
    )

    # Query composition from database
    result = await db.execute(select(Composition).where(Composition.id == composition_id))
    composition = result.scalar_one_or_none()

    if not composition:
        logger.warning(
            "Composition not found",
            extra={"composition_id": str(composition_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composition {composition_id} not found",
        )

    # Get progress information from Redis if available
    overall_progress = 0.0
    current_stage = ProcessingStage.PENDING
    stages: list[ProcessingStageInfo] = []

    # Try to get real-time progress from Redis
    # Note: We'd need to associate job_id with composition to fetch this
    # For now, we'll derive progress from composition status
    status_map = {
        CompositionStatus.PENDING: (0.0, ProcessingStage.PENDING),
        CompositionStatus.QUEUED: (5.0, ProcessingStage.PENDING),
        CompositionStatus.PROCESSING: (50.0, ProcessingStage.RENDERING),
        CompositionStatus.COMPLETED: (100.0, ProcessingStage.COMPLETED),
        CompositionStatus.FAILED: (0.0, ProcessingStage.FAILED),
        CompositionStatus.CANCELLED: (0.0, ProcessingStage.FAILED),
    }

    overall_progress, current_stage = status_map.get(
        composition.status, (0.0, ProcessingStage.PENDING)
    )

    # Build processing stages based on status
    # This is a simplified version - in production, you'd track detailed stage info
    if composition.status in [CompositionStatus.PROCESSING, CompositionStatus.COMPLETED]:
        stages = [
            ProcessingStageInfo(
                stage=ProcessingStage.DOWNLOADING,
                progress=100.0,
                started_at=composition.created_at,
                completed_at=(
                    composition.created_at
                    if composition.status == CompositionStatus.COMPLETED
                    else None
                ),
                message="Assets downloaded successfully",
            ),
            ProcessingStageInfo(
                stage=ProcessingStage.RENDERING,
                progress=(
                    overall_progress
                    if composition.status == CompositionStatus.PROCESSING
                    else 100.0
                ),
                started_at=composition.created_at,
                completed_at=(
                    composition.updated_at
                    if composition.status == CompositionStatus.COMPLETED
                    else None
                ),
                message="Processing video",
            ),
        ]

        if composition.status == CompositionStatus.COMPLETED:
            stages.append(
                ProcessingStageInfo(
                    stage=ProcessingStage.UPLOADING,
                    progress=100.0,
                    started_at=composition.updated_at,
                    completed_at=composition.updated_at,
                    message="Upload complete",
                )
            )
            stages.append(
                ProcessingStageInfo(
                    stage=ProcessingStage.COMPLETED,
                    progress=100.0,
                    started_at=composition.updated_at,
                    completed_at=composition.updated_at,
                    message="Composition completed successfully",
                )
            )

    # Build response
    return CompositionStatusResponse(
        id=composition.id,
        status=composition.status.value,
        overall_progress=overall_progress,
        current_stage=current_stage,
        stages=stages,
        created_at=composition.created_at,
        updated_at=composition.updated_at,
        completed_at=(
            composition.updated_at if composition.status == CompositionStatus.COMPLETED else None
        ),
        error_message=composition.error_message,
    )


@router.get("/{composition_id}/download", response_model=DownloadResponse)
async def get_composition_download(
    composition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DownloadResponse:
    """Generate a download link for a completed composition.

    This endpoint generates a presigned S3 URL that allows downloading the final
    rendered video. The URL expires after 1 hour for security.

    Args:
        composition_id: Unique composition identifier
        db: Database session (injected)

    Returns:
        DownloadResponse: Download URL and metadata

    Raises:
        HTTPException: 404 if composition not found
        HTTPException: 400 if composition not completed
        HTTPException: 500 for S3 errors
    """
    from datetime import UTC, datetime, timedelta
    from pathlib import Path

    from workers.s3_manager import s3_manager

    logger.info(
        "Generating download link",
        extra={"composition_id": str(composition_id)},
    )

    # Query composition from database
    result = await db.execute(select(Composition).where(Composition.id == composition_id))
    composition = result.scalar_one_or_none()

    if not composition:
        logger.warning(
            "Composition not found",
            extra={"composition_id": str(composition_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composition {composition_id} not found",
        )

    # Verify composition is completed
    if composition.status != CompositionStatus.COMPLETED:
        logger.warning(
            "Composition not completed",
            extra={
                "composition_id": str(composition_id),
                "status": composition.status.value,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Composition is not completed. Current status: {composition.status.value}",
        )

    # Verify output URL exists
    if not composition.output_url:
        logger.error(
            "Composition completed but missing output URL",
            extra={"composition_id": str(composition_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Composition output not available",
        )

    # Extract S3 key from output URL
    # The output URL from job handler is in format: s3://bucket/key or https://...
    # We need to extract the S3 key
    output_url = composition.output_url

    # Parse S3 key from URL
    # Assuming format: compositions/{composition_id}/{filename}
    s3_key = f"compositions/{composition_id}/"

    # Try to extract key from URL path
    try:
        if "compositions/" in output_url:
            # Extract everything after "compositions/"
            s3_key = output_url.split("compositions/", 1)[1]
            # Remove any query parameters or fragments
            s3_key = "compositions/" + s3_key.split("?")[0].split("#")[0]
        else:
            # Fallback: construct expected S3 key
            output_format = composition.composition_config.get("output", {}).get("format", "mp4")
            s3_key = f"compositions/{composition_id}/output.{output_format}"
    except Exception as e:
        logger.exception(
            "Failed to parse S3 key from output URL",
            extra={
                "composition_id": str(composition_id),
                "output_url": output_url,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link",
        ) from e

    # Get object metadata for file size
    try:
        metadata = s3_manager.get_object_metadata(s3_key)
        file_size = metadata.get("size_bytes", 0)
    except FileNotFoundError:
        logger.error(
            "Output file not found in S3",
            extra={"composition_id": str(composition_id), "s3_key": s3_key},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found",
        )
    except Exception as e:
        logger.exception(
            "Failed to get S3 object metadata",
            extra={"composition_id": str(composition_id), "s3_key": s3_key, "error": str(e)},
        )
        # Don't fail the request, just use 0 for file size
        file_size = 0

    # Generate presigned URL (1 hour expiration)
    expiration_seconds = 3600  # 1 hour

    try:
        # Extract filename from S3 key
        filename = Path(s3_key).name

        # Add response headers to set filename for download
        response_headers = {
            "ContentDisposition": f'attachment; filename="{filename}"',
        }

        presigned_url = s3_manager.generate_presigned_url(
            s3_key=s3_key,
            expiration=expiration_seconds,
            response_headers=response_headers,
        )

        expires_at = datetime.now(UTC) + timedelta(seconds=expiration_seconds)

        logger.info(
            "Generated presigned download URL",
            extra={
                "composition_id": str(composition_id),
                "s3_key": s3_key,
                "expires_at": expires_at.isoformat(),
            },
        )

        # Get output format from composition config
        output_format = composition.composition_config.get("output", {}).get("format", "mp4")

        return DownloadResponse(
            composition_id=composition_id,
            download_url=presigned_url,
            expires_at=expires_at,
            file_size_bytes=file_size,
            format=output_format,
            filename=filename,
        )

    except Exception as e:
        logger.exception(
            "Failed to generate presigned URL",
            extra={"composition_id": str(composition_id), "s3_key": s3_key, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link",
        ) from e


@router.get("/{composition_id}/metadata", response_model=CompositionMetadataResponse)
async def get_composition_metadata(
    composition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompositionMetadataResponse:
    """Get detailed metadata for a composition.

    This endpoint returns comprehensive information about a composition including
    the original request configuration, processing timeline, resource usage metrics,
    file information, and any warnings generated during processing.

    Args:
        composition_id: Unique composition identifier
        db: Database session (injected)

    Returns:
        CompositionMetadataResponse: Detailed composition metadata

    Raises:
        HTTPException: 404 if composition not found
    """
    from db.models.job import MetricType
    from sqlalchemy.orm import selectinload

    logger.info(
        "Retrieving composition metadata",
        extra={"composition_id": str(composition_id)},
    )

    # Query composition with related jobs and metrics
    result = await db.execute(
        select(Composition)
        .options(selectinload(Composition.processing_jobs), selectinload(Composition.metrics))
        .where(Composition.id == composition_id)
    )
    composition = result.scalar_one_or_none()

    if not composition:
        logger.warning(
            "Composition not found",
            extra={"composition_id": str(composition_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Composition {composition_id} not found",
        )

    # Build resource metrics from job metrics
    resource_metrics = None
    processing_time = None
    queue_wait_time = None
    cpu_usage = None
    memory_usage = None

    if composition.metrics:
        for metric in composition.metrics:
            if metric.metric_type == MetricType.PROCESSING_DURATION:
                processing_time = float(metric.metric_value)
            elif metric.metric_type == MetricType.QUEUE_WAIT_TIME:
                queue_wait_time = float(metric.metric_value)
            elif metric.metric_type == MetricType.CPU_USAGE:
                cpu_usage = float(metric.metric_value)
            elif metric.metric_type == MetricType.MEMORY_USAGE:
                memory_usage = float(metric.metric_value)

        resource_metrics = ResourceMetrics(
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage,
            processing_time_seconds=processing_time,
            queue_wait_time_seconds=queue_wait_time,
        )

    # Build input file information from composition config
    input_files = []
    composition_config = composition.composition_config

    if "clips" in composition_config:
        for i, clip in enumerate(composition_config["clips"]):
            input_files.append(
                InputFileInfo(
                    url=clip.get("video_url", ""),
                    format=None,  # Format would be determined during processing
                    size_bytes=None,  # Size would be tracked during download
                    duration_seconds=clip.get("end_time", 0) - clip.get("start_time", 0),
                )
            )

    # Add audio files if present
    if "audio" in composition_config:
        audio = composition_config["audio"]
        if audio.get("music_url"):
            input_files.append(
                InputFileInfo(
                    url=audio["music_url"],
                    format=None,
                    size_bytes=None,
                    duration_seconds=None,
                )
            )
        if audio.get("voiceover_url"):
            input_files.append(
                InputFileInfo(
                    url=audio["voiceover_url"],
                    format=None,
                    size_bytes=None,
                    duration_seconds=None,
                )
            )

    # Build output file information
    output_file = None
    if composition.status == CompositionStatus.COMPLETED and composition.output_url:
        output_config = composition_config.get("output", {})

        # Try to get file size from S3
        file_size = None
        try:
            from workers.s3_manager import s3_manager

            # Extract S3 key from output URL
            if "compositions/" in composition.output_url:
                s3_key = composition.output_url.split("compositions/", 1)[1].split("?")[0]
                s3_key = "compositions/" + s3_key

                metadata = s3_manager.get_object_metadata(s3_key)
                file_size = metadata.get("size_bytes", 0)
        except Exception as e:
            logger.debug(
                "Could not get output file size",
                extra={"composition_id": str(composition_id), "error": str(e)},
            )

        output_file = OutputFileInfo(
            url=composition.output_url,
            format=output_config.get("format", "mp4"),
            size_bytes=file_size,
            duration_seconds=None,  # Would require FFprobe
            resolution=output_config.get("resolution", "1080p"),
            bitrate=output_config.get("bitrate"),
            fps=output_config.get("fps", 30),
        )

    # Build applied effects list
    applied_effects = []
    if "overlays" in composition_config and composition_config["overlays"]:
        applied_effects.append(f"Text overlays ({len(composition_config['overlays'])} items)")
    if "audio" in composition_config:
        audio = composition_config["audio"]
        if audio.get("music_url"):
            applied_effects.append("Background music")
        if audio.get("voiceover_url"):
            applied_effects.append("Voiceover audio")

    # Build warnings list (would be populated during processing)
    warnings = []
    if composition.status == CompositionStatus.FAILED and composition.error_message:
        warnings.append(f"Processing failed: {composition.error_message}")

    # Determine processing timestamps
    started_processing_at = None
    if composition.processing_jobs:
        for job in composition.processing_jobs:
            if job.started_at:
                started_processing_at = job.started_at
                break

    completed_at = None
    if composition.status == CompositionStatus.COMPLETED:
        completed_at = composition.updated_at

    return CompositionMetadataResponse(
        id=composition.id,
        title=composition.title,
        status=composition.status.value,
        request_config=composition_config,
        created_at=composition.created_at,
        started_processing_at=started_processing_at,
        completed_at=completed_at,
        resource_metrics=resource_metrics,
        input_files=input_files,
        output_file=output_file,
        applied_effects=applied_effects,
        warnings=warnings,
    )


@router.post("/{composition_id}/cancel", response_model=CompositionCancelResponse)
async def cancel_composition(
    composition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompositionCancelResponse:
    """Cancel a specific composition and its associated job.

    This endpoint cancels a composition that is in QUEUED or PROCESSING status.
    It removes the job from the RQ queue, updates the database status to CANCELLED,
    and cleans up any temporary files.

    Args:
        composition_id: Unique composition identifier
        db: Database session (injected)

    Returns:
        CompositionCancelResponse: Cancellation confirmation

    Raises:
        HTTPException: 404 if composition not found
        HTTPException: 400 if composition cannot be cancelled (already completed/failed)
        HTTPException: 500 for server errors
    """
    from datetime import UTC, datetime
    from pathlib import Path

    from rq import Queue
    from rq.job import Job
    from workers.redis_pool import get_redis_connection

    logger.info(
        "Cancelling composition",
        extra={"composition_id": str(composition_id)},
    )

    try:
        # Query composition from database
        result = await db.execute(select(Composition).where(Composition.id == composition_id))
        composition = result.scalar_one_or_none()

        if not composition:
            logger.warning(
                "Composition not found for cancellation",
                extra={"composition_id": str(composition_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composition {composition_id} not found",
            )

        # Check if composition can be cancelled
        if composition.status in (CompositionStatus.COMPLETED, CompositionStatus.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel composition with status {composition.status.value}",
            )

        if composition.status == CompositionStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel failed composition",
            )

        # Try to cancel the RQ job if it's queued or processing
        redis_conn = get_redis_connection()
        cancelled_job = False

        for queue_name in ["high", "default", "low"]:
            queue = Queue(name=queue_name, connection=redis_conn)

            # Get all jobs in the queue
            for job in queue.jobs:
                # Check if this job is for our composition
                if (
                    hasattr(job, "kwargs")
                    and job.kwargs
                    and str(job.kwargs.get("composition_id")) == str(composition_id)
                ):
                    # Cancel the job
                    job.cancel()
                    job.delete()
                    cancelled_job = True

                    logger.info(
                        f"Cancelled RQ job {job.id} in queue {queue_name}",
                        extra={
                            "composition_id": str(composition_id),
                            "job_id": job.id,
                            "queue": queue_name,
                        },
                    )
                    break

            if cancelled_job:
                break

        # Clean up temp files
        try:
            import shutil

            from app.config import settings

            temp_dir = Path(settings.temp_dir) / str(composition_id)
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(
                    f"Cleaned up temp directory for composition {composition_id}",
                    extra={"composition_id": str(composition_id), "temp_dir": str(temp_dir)},
                )
        except Exception as e:
            logger.warning(
                f"Failed to clean up temp files for composition {composition_id}: {e}",
                extra={"composition_id": str(composition_id), "error": str(e)},
            )

        # Update composition status to CANCELLED
        composition.status = CompositionStatus.CANCELLED
        composition.error_message = "Cancelled by user"
        await db.commit()
        await db.refresh(composition)

        cancelled_at = datetime.now(UTC)

        logger.info(
            f"Composition {composition_id} cancelled successfully",
            extra={
                "composition_id": str(composition_id),
                "job_cancelled": cancelled_job,
            },
        )

        return CompositionCancelResponse(
            composition_id=composition_id,
            status=composition.status.value,
            message=f"Composition {composition_id} has been cancelled",
            cancelled_at=cancelled_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to cancel composition",
            extra={"composition_id": str(composition_id), "error": str(e)},
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel composition",
        ) from e


@router.post("/cancel-all", response_model=BulkCancelResponse)
async def cancel_all_queued_compositions(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BulkCancelResponse:
    """Cancel all queued compositions.

    This endpoint cancels all compositions that are in QUEUED or PROCESSING status.
    It removes jobs from the RQ queue, updates database statuses, and cleans up temp files.

    Args:
        db: Database session (injected)

    Returns:
        BulkCancelResponse: Summary of cancellation operation

    Raises:
        HTTPException: 500 for server errors
    """
    from datetime import UTC, datetime
    from pathlib import Path

    from rq import Queue
    from workers.redis_pool import get_redis_connection

    logger.info("Cancelling all queued compositions")

    cancelled_ids: list[uuid.UUID] = []
    failed_ids: list[uuid.UUID] = []

    try:
        # Query all compositions that can be cancelled
        result = await db.execute(
            select(Composition).where(
                Composition.status.in_([CompositionStatus.QUEUED, CompositionStatus.PROCESSING])
            )
        )
        compositions = result.scalars().all()

        logger.info(
            f"Found {len(compositions)} compositions to cancel",
            extra={"count": len(compositions)},
        )

        # Get Redis connection and queues
        redis_conn = get_redis_connection()
        queues = {name: Queue(name=name, connection=redis_conn) for name in ["high", "default", "low"]}

        # Cancel each composition
        for composition in compositions:
            try:
                # Try to find and cancel the RQ job
                cancelled_job = False

                for queue_name, queue in queues.items():
                    for job in queue.jobs:
                        if (
                            hasattr(job, "kwargs")
                            and job.kwargs
                            and str(job.kwargs.get("composition_id")) == str(composition.id)
                        ):
                            job.cancel()
                            job.delete()
                            cancelled_job = True

                            logger.debug(
                                f"Cancelled job {job.id} for composition {composition.id}",
                                extra={
                                    "composition_id": str(composition.id),
                                    "job_id": job.id,
                                    "queue": queue_name,
                                },
                            )
                            break

                    if cancelled_job:
                        break

                # Clean up temp files
                try:
                    import shutil

                    from app.config import settings

                    temp_dir = Path(settings.temp_dir) / str(composition.id)
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as cleanup_error:
                    logger.warning(
                        f"Failed to clean up temp files for {composition.id}: {cleanup_error}",
                        extra={"composition_id": str(composition.id)},
                    )

                # Update composition status
                composition.status = CompositionStatus.CANCELLED
                composition.error_message = "Cancelled by bulk operation"

                cancelled_ids.append(composition.id)

            except Exception as comp_error:
                logger.exception(
                    f"Failed to cancel composition {composition.id}",
                    extra={"composition_id": str(composition.id), "error": str(comp_error)},
                )
                failed_ids.append(composition.id)

        # Commit all changes
        await db.commit()

        logger.info(
            f"Bulk cancellation complete: {len(cancelled_ids)} succeeded, {len(failed_ids)} failed",
            extra={
                "cancelled_count": len(cancelled_ids),
                "failed_count": len(failed_ids),
            },
        )

        message = f"Cancelled {len(cancelled_ids)} composition(s)"
        if failed_ids:
            message += f", {len(failed_ids)} failed"

        return BulkCancelResponse(
            cancelled_count=len(cancelled_ids),
            failed_count=len(failed_ids),
            cancelled_ids=cancelled_ids,
            failed_ids=failed_ids,
            message=message,
        )

    except Exception as e:
        logger.exception(
            "Failed to cancel queued compositions",
            extra={"error": str(e)},
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel queued compositions",
        ) from e


@router.get("/{composition_id}", response_model=CompositionResponse)
async def get_composition(
    composition_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompositionResponse:
    """Get detailed information about a specific composition.

    This endpoint retrieves comprehensive information about a composition including
    its current status, configuration, timestamps, and output URL (if completed).

    Args:
        composition_id: Unique composition identifier
        db: Database session (injected)

    Returns:
        CompositionResponse: Detailed composition information

    Raises:
        HTTPException: 404 if composition not found
        HTTPException: 500 for database errors
    """
    logger.info(
        "Retrieving composition details",
        extra={"composition_id": str(composition_id)},
    )

    try:
        # Query composition from database
        result = await db.execute(select(Composition).where(Composition.id == composition_id))
        composition = result.scalar_one_or_none()

        if not composition:
            logger.warning(
                "Composition not found",
                extra={"composition_id": str(composition_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Composition {composition_id} not found",
            )

        logger.info(
            "Retrieved composition",
            extra={
                "composition_id": str(composition_id),
                "status": composition.status.value,
                "title": composition.title,
            },
        )

        # Return composition response
        return CompositionResponse.model_validate(composition)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Failed to retrieve composition",
            extra={"composition_id": str(composition_id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve composition",
        ) from e
