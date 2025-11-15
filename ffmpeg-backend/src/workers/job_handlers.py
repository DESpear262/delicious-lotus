"""Job handlers for video composition and processing tasks."""

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.config import settings
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class JobContext:
    """Context for tracking job execution state."""

    job_id: str
    composition_id: UUID | None = None
    status: JobStatus = JobStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    error_traceback: str | None = None
    progress_percent: float = 0.0
    current_operation: str = "Initializing"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        """Calculate job duration in seconds.

        Returns:
            float | None: Duration in seconds or None if not completed
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_running(self) -> bool:
        """Check if job is currently running.

        Returns:
            bool: True if job is in progress
        """
        return self.status == JobStatus.IN_PROGRESS

    @property
    def is_complete(self) -> bool:
        """Check if job is complete (success or failure).

        Returns:
            bool: True if job is in terminal state
        """
        return self.status in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.TIMEOUT,
            JobStatus.CANCELLED,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for serialization.

        Returns:
            dict: Serialized job context
        """
        return {
            "job_id": self.job_id,
            "composition_id": str(self.composition_id) if self.composition_id else None,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "progress_percent": self.progress_percent,
            "current_operation": self.current_operation,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


class CompositionJobParams(BaseModel):
    """Parameters for composition job."""

    composition_id: UUID = Field(..., description="ID of composition to process")
    composition_config: dict[str, Any] = Field(
        ..., description="Composition configuration including assets and layout"
    )
    output_format: str = Field(default="mp4", description="Output video format")
    output_resolution: str = Field(default="1920x1080", description="Output resolution (WxH)")
    output_fps: int = Field(default=30, ge=1, le=120, description="Output frame rate")
    priority: str = Field(default="default", description="Job priority (high/default/low)")

    @field_validator("output_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate output format is supported.

        Args:
            v: Format to validate

        Returns:
            str: Validated format

        Raises:
            ValueError: If format not supported
        """
        supported = settings.supported_video_formats
        if v not in supported:
            raise ValueError(f"Unsupported output format: {v}. Must be one of {supported}")
        return v

    @field_validator("output_resolution")
    @classmethod
    def validate_resolution(cls, v: str) -> str:
        """Validate resolution format.

        Args:
            v: Resolution string to validate

        Returns:
            str: Validated resolution

        Raises:
            ValueError: If resolution format invalid
        """
        try:
            width, height = v.split("x")
            w, h = int(width), int(height)
            if w <= 0 or h <= 0:
                raise ValueError("Resolution dimensions must be positive")
            if w > 7680 or h > 4320:  # Max 8K
                raise ValueError("Resolution exceeds maximum (8K)")
            return v
        except Exception as e:
            raise ValueError(
                f"Invalid resolution format: {v}. Expected WxH (e.g., 1920x1080)"
            ) from e

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is valid queue name.

        Args:
            v: Priority to validate

        Returns:
            str: Validated priority

        Raises:
            ValueError: If priority invalid
        """
        valid_priorities = ["high", "default", "low"]
        if v not in valid_priorities:
            raise ValueError(f"Invalid priority: {v}. Must be one of {valid_priorities}")
        return v


class CompositionJobHandler:
    """Handler for video composition jobs."""

    def __init__(self, job_id: str) -> None:
        """Initialize composition job handler.

        Args:
            job_id: Unique job identifier
        """
        self.job_id = job_id
        self.context = JobContext(job_id=job_id)
        self.logger = logger.getChild(f"job.{job_id[:8]}")
        self.progress_tracker: Any = None  # Will be initialized in execute

        self.logger.info(
            "Initialized CompositionJobHandler",
            extra={"job_id": job_id},
        )

    def validate_params(self, params: dict[str, Any]) -> CompositionJobParams:
        """Validate and sanitize job parameters.

        Args:
            params: Raw job parameters

        Returns:
            CompositionJobParams: Validated parameters

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            validated = CompositionJobParams(**params)

            self.logger.info(
                "Job parameters validated successfully",
                extra={
                    "job_id": self.job_id,
                    "composition_id": str(validated.composition_id),
                    "output_format": validated.output_format,
                    "output_resolution": validated.output_resolution,
                },
            )

            return validated

        except Exception as e:
            self.logger.exception(
                "Job parameter validation failed",
                extra={
                    "job_id": self.job_id,
                    "error": str(e),
                    "params": params,
                },
            )
            raise ValueError(f"Invalid job parameters: {e}") from e

    def _update_context(
        self,
        status: JobStatus | None = None,
        progress: float | None = None,
        operation: str | None = None,
        error: str | None = None,
        **metadata: Any,
    ) -> None:
        """Update job context state and publish progress to Redis.

        Args:
            status: New job status
            progress: Progress percentage (0-100)
            operation: Current operation description
            error: Error message if failed
            **metadata: Additional metadata to store
        """
        if status is not None:
            self.context.status = status

            # Set timestamps based on status
            if status == JobStatus.IN_PROGRESS and self.context.started_at is None:
                self.context.started_at = datetime.now(UTC)
            elif status in {
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.TIMEOUT,
                JobStatus.CANCELLED,
            }:
                self.context.completed_at = datetime.now(UTC)

        if progress is not None:
            self.context.progress_percent = max(0.0, min(100.0, progress))

        if operation is not None:
            self.context.current_operation = operation

        if error is not None:
            self.context.error_message = error

        if metadata:
            self.context.metadata.update(metadata)

        # Publish progress update to Redis if tracker is initialized
        if self.progress_tracker and progress is not None:
            self.progress_tracker.publish_progress(
                progress_percent=self.context.progress_percent,
                operation=self.context.current_operation,
                **metadata,
            )

        # Update status in Redis if tracker is initialized and status changed
        if self.progress_tracker and status is not None:
            self.progress_tracker.update_status(
                status=status.value,
                message=operation,
                error=error,
            )

        # Log context update
        self.logger.debug(
            "Job context updated",
            extra={
                "job_id": self.job_id,
                "status": self.context.status.value if status else None,
                "progress": self.context.progress_percent,
                "operation": self.context.current_operation,
            },
        )

    async def _collect_metrics_async(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute job with async metrics collection.

        Args:
            params: Job parameters

        Returns:
            dict: Job execution result
        """
        from db.session import get_db_session
        from services.metrics import JobMetricsContext, MetricsCollector

        validated_params = self.validate_params(params)
        self.context.composition_id = validated_params.composition_id

        # Execute job with metrics collection
        async with get_db_session() as session:
            metrics_collector = MetricsCollector(session)

            async with JobMetricsContext(
                collector=metrics_collector,
                composition_id=validated_params.composition_id,
                processing_job_id=None,  # ProcessingJob record not created yet
            ):
                # Initialize progress tracker
                from workers.progress_tracker import ProgressTracker

                self.progress_tracker = ProgressTracker(
                    job_id=self.job_id,
                    composition_id=str(validated_params.composition_id),
                    throttle_seconds=0.5,  # Update at most every 0.5 seconds
                )

                # Update status to in progress
                self._update_context(
                    status=JobStatus.IN_PROGRESS,
                    operation="Job initialized",
                    progress=0.0,
                )

                # Execute job
                result = self._execute_job(validated_params)

                # Record FFmpeg stats if available in metadata
                if "ffmpeg_stats" in self.context.metadata:
                    ffmpeg_stats = self.context.metadata["ffmpeg_stats"]
                    await metrics_collector.record_ffmpeg_stats(
                        composition_id=validated_params.composition_id,
                        processing_job_id=UUID(self.job_id),
                        stats={
                            "frame_rate": ffmpeg_stats.get("fps", 0.0),
                            "bitrate": ffmpeg_stats.get("bitrate_kbps", 0.0),
                            "encoding_speed": ffmpeg_stats.get("speed", 0.0),
                        },
                    )

                # Mark as completed
                self._update_context(
                    status=JobStatus.COMPLETED,
                    operation="Job completed successfully",
                    progress=100.0,
                )

                return result

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the composition job.

        Args:
            params: Job parameters

        Returns:
            dict: Job execution result

        Raises:
            Exception: If job execution fails
        """
        start_time = time.time()

        try:
            # Validate parameters
            self.logger.info(
                "Starting job execution",
                extra={"job_id": self.job_id, "params": params},
            )

            # Execute job with metrics collection (run async code in sync context)
            result = asyncio.run(self._collect_metrics_async(params))

            execution_time = time.time() - start_time

            self.logger.info(
                "Job execution completed successfully",
                extra={
                    "job_id": self.job_id,
                    "composition_id": str(self.context.composition_id),
                    "execution_time": execution_time,
                    "result": result,
                },
            )

            return {
                "success": True,
                "job_id": self.job_id,
                "composition_id": str(self.context.composition_id),
                "execution_time": execution_time,
                "result": result,
                "context": self.context.to_dict(),
            }

        except Exception as e:
            from workers.retry_logic import JobTimeoutError, classify_failure

            execution_time = time.time() - start_time
            error_msg = str(e)
            error_trace = traceback.format_exc()

            # Classify failure type
            failure_type = classify_failure(e)

            # Determine job status based on failure type
            job_status = JobStatus.TIMEOUT if isinstance(e, JobTimeoutError) else JobStatus.FAILED

            # Update context with error
            self._update_context(
                status=job_status,
                error=error_msg,
                operation=f"Job failed ({failure_type.value})",
                failure_type=failure_type.value,
            )
            self.context.error_traceback = error_trace

            self.logger.exception(
                "Job execution failed",
                extra={
                    "job_id": self.job_id,
                    "error": error_msg,
                    "failure_type": failure_type.value,
                    "execution_time": execution_time,
                },
            )

            return {
                "success": False,
                "job_id": self.job_id,
                "error": error_msg,
                "error_traceback": error_trace,
                "failure_type": failure_type.value,
                "execution_time": execution_time,
                "context": self.context.to_dict(),
            }

    def _execute_job(self, params: CompositionJobParams) -> dict[str, Any]:
        """Execute the actual job logic with FFmpeg pipeline.

        Args:
            params: Validated job parameters

        Returns:
            dict: Job result including output S3 URL

        Raises:
            Exception: If job execution fails
        """
        from pathlib import Path
        from uuid import uuid4

        from workers.ffmpeg_pipeline import FFmpegPipeline, FFmpegProgress
        from workers.s3_manager import s3_manager

        self.logger.info(
            "Executing composition job",
            extra={
                "job_id": self.job_id,
                "composition_id": str(params.composition_id),
            },
        )

        # Create temp directory for this job
        job_temp_dir = Path(settings.temp_dir) / self.job_id
        job_temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Download assets from S3
            self._update_context(
                operation="Downloading assets from S3",
                progress=10.0,
            )

            assets = params.composition_config.get("assets", [])
            if not assets:
                raise ValueError("No assets provided in composition config")

            downloaded_files = s3_manager.download_assets(
                assets=assets,
                temp_dir=job_temp_dir,
                progress_callback=lambda asset_id, downloaded, total: self.logger.debug(
                    f"Asset {asset_id} download progress: {downloaded}/{total} bytes"
                ),
            )

            self.logger.info(
                f"Downloaded {len(downloaded_files)} assets",
                extra={"asset_count": len(downloaded_files)},
            )

            self._update_context(
                operation="Assets downloaded",
                progress=30.0,
            )

            # Step 2: Execute FFmpeg composition
            self._update_context(
                operation="Processing video with FFmpeg",
                progress=40.0,
            )

            pipeline = FFmpegPipeline(temp_dir=job_temp_dir)

            # Generate output filename
            output_filename = f"{params.composition_id}_{uuid4().hex[:8]}.{params.output_format}"

            # Track last FFmpeg progress for metrics
            last_ffmpeg_progress = None

            # Progress callback for FFmpeg
            def ffmpeg_progress_callback(progress: FFmpegProgress) -> None:
                nonlocal last_ffmpeg_progress
                last_ffmpeg_progress = progress

                # Map FFmpeg progress (0-100%) to job progress (40-80%)
                job_progress = 40.0 + (progress.progress_percent * 0.4)

                # Publish detailed progress with FFmpeg stats
                if self.progress_tracker:
                    self.progress_tracker.publish_progress(
                        progress_percent=job_progress,
                        operation=f"Processing video (frame {progress.frame}, {progress.fps:.1f} fps)",
                        frame=progress.frame,
                        fps=progress.fps,
                        bitrate_kbps=progress.bitrate_kbps,
                        speed=progress.speed,
                    )

                # Also update context (without Redis publish since we just did it)
                self.context.progress_percent = job_progress
                self.context.current_operation = (
                    f"Processing video (frame {progress.frame}, {progress.fps:.1f} fps)"
                )

            # Execute FFmpeg composition with timeout
            output_file = pipeline.execute_composition(
                input_files=downloaded_files,
                output_filename=output_filename,
                composition_config=params.composition_config,
                resolution=params.output_resolution,
                fps=params.output_fps,
                progress_callback=ffmpeg_progress_callback,
                timeout=settings.rq_default_timeout,  # Use configured timeout
            )

            self.logger.info(
                "FFmpeg composition completed",
                extra={"output_file": str(output_file)},
            )

            # Store FFmpeg stats in metadata for metrics collection
            if last_ffmpeg_progress:
                self.context.metadata["ffmpeg_stats"] = {
                    "frames": last_ffmpeg_progress.frame,
                    "fps": last_ffmpeg_progress.fps,
                    "speed": last_ffmpeg_progress.speed,
                    "bitrate_kbps": last_ffmpeg_progress.bitrate_kbps,
                }

            self._update_context(
                operation="Video processing complete",
                progress=80.0,
            )

            # Step 3: Upload output to S3
            self._update_context(
                operation="Uploading output to S3",
                progress=85.0,
            )

            # Generate S3 key for output
            s3_output_key = f"compositions/{params.composition_id}/{output_filename}"

            # Upload with progress tracking
            s3_url = s3_manager.upload_file(
                local_path=output_file,
                s3_key=s3_output_key,
                progress_callback=lambda uploaded, total: self.logger.debug(
                    f"Upload progress: {uploaded}/{total} bytes"
                ),
                extra_args={
                    "ContentType": f"video/{params.output_format}",
                    "Metadata": {
                        "composition_id": str(params.composition_id),
                        "job_id": self.job_id,
                    },
                },
            )

            self.logger.info(
                "Output uploaded to S3",
                extra={"s3_url": s3_url, "s3_key": s3_output_key},
            )

            self._update_context(
                operation="Upload complete",
                progress=95.0,
            )

            # Step 4: Cleanup temp files
            self._update_context(
                operation="Cleaning up temporary files",
                progress=98.0,
            )

            pipeline.cleanup_temp_files(preserve_output=False)

            # Remove job temp directory
            import shutil

            shutil.rmtree(job_temp_dir, ignore_errors=True)

            self.logger.info("Cleanup completed")

            # Return result
            result = {
                "composition_id": str(params.composition_id),
                "output_url": s3_url,
                "output_s3_key": s3_output_key,
                "output_format": params.output_format,
                "resolution": params.output_resolution,
                "fps": params.output_fps,
                "status": "completed",
            }

            return result

        except Exception as e:
            self.logger.exception(
                "Job execution failed",
                extra={"error": str(e)},
            )

            # Cleanup on failure
            import shutil

            shutil.rmtree(job_temp_dir, ignore_errors=True)

            raise

    def cleanup(self) -> None:
        """Cleanup job resources.

        This method should be called after job completion to cleanup
        temporary files, close connections, etc.
        """
        self.logger.info(
            "Cleaning up job resources",
            extra={"job_id": self.job_id},
        )

        # Cleanup logic will be expanded in later subtasks
        # For now, just log the cleanup
        self.logger.debug(
            "Job cleanup completed",
            extra={
                "job_id": self.job_id,
                "status": self.context.status.value,
            },
        )


def process_composition_job(job_id: str, **params: Any) -> dict[str, Any]:
    """Main entry point for processing composition jobs.

    This function is called by RQ workers to process composition jobs.

    Args:
        job_id: Unique job identifier
        **params: Job parameters

    Returns:
        dict: Job execution result
    """
    handler = CompositionJobHandler(job_id=job_id)

    try:
        result = handler.execute(params)
        return result

    finally:
        # Always cleanup, even if job failed
        handler.cleanup()
