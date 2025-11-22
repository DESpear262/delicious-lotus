"""Pydantic schemas for job API endpoints."""

from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobResponse(BaseModel):
    """Response model for a single job."""

    job_id: str = Field(..., description="Unique job identifier")
    clip_id: str = Field(..., description="Clip identifier from original request")
    status: JobStatus = Field(..., description="Current job status")
    request_id: str = Field(..., description="Request ID this job belongs to")

    # Processing details
    clip_url: str = Field(..., description="URL of the clip being processed")
    callback_url: str = Field(..., description="Callback URL for completion notification")
    operations: list[str] = Field(..., description="List of operations to perform")
    processing_options: dict = Field(..., description="Processing options")

    # Metadata
    metadata: dict[str, str] = Field(default_factory=dict, description="Clip metadata")
    priority: int = Field(..., ge=1, le=10, description="Job priority (1-10)")

    # Timestamps
    queued_at: str = Field(..., description="ISO 8601 timestamp when job was queued")
    started_at: str | None = Field(
        default=None, description="ISO 8601 timestamp when processing started"
    )
    completed_at: str | None = Field(
        default=None, description="ISO 8601 timestamp when job completed"
    )

    # Results (for completed jobs)
    processed_url: str | None = Field(default=None, description="URL of processed clip")
    error: str | None = Field(default=None, description="Error message if job failed")
    progress: int | None = Field(
        default=None, ge=0, le=100, description="Processing progress percentage"
    )


class JobListResponse(BaseModel):
    """Response model for listing jobs."""

    jobs: list[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    offset: int = Field(default=0, description="Pagination offset")
    limit: int = Field(default=50, description="Pagination limit")


class JobCancelResponse(BaseModel):
    """Response model for job cancellation."""

    job_id: str = Field(..., description="Job ID that was cancelled")
    status: JobStatus = Field(..., description="Updated job status")
    message: str = Field(..., description="Cancellation status message")
    cancelled_at: str = Field(..., description="ISO 8601 timestamp when job was cancelled")
