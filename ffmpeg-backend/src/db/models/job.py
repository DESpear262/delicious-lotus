"""
Processing job and metrics models for tracking composition processing.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import BaseModel


class JobType(str, enum.Enum):
    """Type of processing job."""

    COMPOSITION_RENDER = "composition_render"
    VIDEO_TRANSCODE = "video_transcode"
    AUDIO_PROCESS = "audio_process"
    THUMBNAIL_GENERATE = "thumbnail_generate"


class JobStatus(str, enum.Enum):
    """Status of processing job."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ProcessingJob(BaseModel):
    """
    Model for tracking individual processing jobs.

    Each composition may have multiple processing jobs associated with it
    (e.g., rendering, transcoding, thumbnail generation).

    Attributes:
        id: UUID primary key
        composition_id: Foreign key to Composition
        job_type: Type of processing job
        status: Current job status
        started_at: When the job started processing
        completed_at: When the job completed (success or failure)
        error_message: Error message if job failed
        retry_count: Number of times this job has been retried
    """

    __tablename__ = "processing_jobs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to composition
    composition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job details
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type"), nullable=False, index=True
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Timing fields
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Relationships
    composition: Mapped["Composition"] = relationship(  # type: ignore[name-defined]
        "Composition", back_populates="processing_jobs"
    )

    metrics: Mapped[list["JobMetric"]] = relationship(  # type: ignore[name-defined]
        "JobMetric",
        back_populates="processing_job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_processing_jobs_composition_status", "composition_id", "status"),
        Index("ix_processing_jobs_type_status", "job_type", "status"),
        Index("ix_processing_jobs_status_created_at", "status", "created_at"),
        CheckConstraint("retry_count >= 0", name="ck_processing_jobs_retry_count_positive"),
    )

    def __repr__(self) -> str:
        """String representation of ProcessingJob."""
        return (
            f"<ProcessingJob(id={self.id}, type={self.job_type}, "
            f"status={self.status}, composition_id={self.composition_id})>"
        )


class MetricType(str, enum.Enum):
    """Type of performance metric."""

    PROCESSING_DURATION = "processing_duration"
    FILE_SIZE = "file_size"
    BITRATE = "bitrate"
    FRAME_RATE = "frame_rate"
    RESOLUTION = "resolution"
    QUEUE_WAIT_TIME = "queue_wait_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


class JobMetric(BaseModel):
    """
    Model for storing performance metrics for jobs.

    Allows tracking various metrics like processing duration, file sizes,
    bitrates, and resource usage.

    Attributes:
        id: UUID primary key
        composition_id: Foreign key to Composition
        processing_job_id: Optional foreign key to ProcessingJob
        metric_type: Type of metric being recorded
        metric_value: Numeric value of the metric
        metric_unit: Unit of measurement (e.g., 'seconds', 'bytes', 'mbps')
        recorded_at: When the metric was recorded
    """

    __tablename__ = "job_metrics"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    composition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    processing_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Metric details
    metric_type: Mapped[MetricType] = mapped_column(
        Enum(MetricType, name="metric_type"), nullable=False, index=True
    )

    metric_value: Mapped[Decimal] = mapped_column(Numeric(precision=20, scale=4), nullable=False)

    metric_unit: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timestamp for when metric was recorded
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Relationships
    composition: Mapped["Composition"] = relationship(  # type: ignore[name-defined]
        "Composition", back_populates="metrics"
    )

    processing_job: Mapped["ProcessingJob"] = relationship(  # type: ignore[name-defined]
        "ProcessingJob", back_populates="metrics"
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_job_metrics_composition_type", "composition_id", "metric_type"),
        Index("ix_job_metrics_job_type", "processing_job_id", "metric_type"),
        Index("ix_job_metrics_type_recorded", "metric_type", "recorded_at"),
        CheckConstraint("metric_value >= 0", name="ck_job_metrics_value_positive"),
    )

    def __repr__(self) -> str:
        """String representation of JobMetric."""
        return (
            f"<JobMetric(id={self.id}, type={self.metric_type}, "
            f"value={self.metric_value} {self.metric_unit})>"
        )
