"""Metrics collection service for job and performance monitoring."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import psutil
from app.logging_config import get_logger
from db.models import JobMetric, MetricType
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class MetricsCollector:
    """
    Service for collecting and storing performance metrics.

    Provides methods for recording job metrics, FFmpeg statistics,
    and system resource usage.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize metrics collector with database session.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session
        self._batch: list[JobMetric] = []

    async def record_metric(
        self,
        metric_type: MetricType,
        value: float | Decimal,
        unit: str,
        composition_id: uuid.UUID,
        processing_job_id: uuid.UUID | None = None,
        recorded_at: datetime | None = None,
    ) -> JobMetric:
        """
        Record a single metric to the database.

        Args:
            metric_type: Type of metric being recorded
            value: Numeric value of the metric
            unit: Unit of measurement (e.g., 'seconds', 'bytes', 'mbps')
            composition_id: UUID of the composition
            processing_job_id: Optional UUID of the processing job
            recorded_at: When the metric was recorded (defaults to now)

        Returns:
            JobMetric: The created metric object
        """
        if recorded_at is None:
            recorded_at = datetime.now(UTC)

        # Convert to Decimal for database storage
        if isinstance(value, float):
            value = Decimal(str(value))

        metric = JobMetric(
            composition_id=composition_id,
            processing_job_id=processing_job_id,
            metric_type=metric_type,
            metric_value=value,
            metric_unit=unit,
            recorded_at=recorded_at,
        )

        self.session.add(metric)
        await self.session.flush()

        logger.debug(
            f"Recorded metric: {metric_type.value}={value} {unit}",
            extra={
                "composition_id": str(composition_id),
                "processing_job_id": str(processing_job_id) if processing_job_id else None,
                "metric_type": metric_type.value,
            },
        )

        return metric

    def add_to_batch(
        self,
        metric_type: MetricType,
        value: float | Decimal,
        unit: str,
        composition_id: uuid.UUID,
        processing_job_id: uuid.UUID | None = None,
        recorded_at: datetime | None = None,
    ) -> None:
        """
        Add metric to batch for bulk insertion.

        Use this for high-volume metrics collection to improve performance.
        Call flush_batch() to insert all batched metrics.

        Args:
            metric_type: Type of metric being recorded
            value: Numeric value of the metric
            unit: Unit of measurement
            composition_id: UUID of the composition
            processing_job_id: Optional UUID of the processing job
            recorded_at: When the metric was recorded (defaults to now)
        """
        if recorded_at is None:
            recorded_at = datetime.now(UTC)

        if isinstance(value, float):
            value = Decimal(str(value))

        metric = JobMetric(
            composition_id=composition_id,
            processing_job_id=processing_job_id,
            metric_type=metric_type,
            metric_value=value,
            metric_unit=unit,
            recorded_at=recorded_at,
        )

        self._batch.append(metric)

    async def flush_batch(self) -> int:
        """
        Flush all batched metrics to the database.

        Returns:
            int: Number of metrics inserted
        """
        if not self._batch:
            return 0

        count = len(self._batch)
        self.session.add_all(self._batch)
        await self.session.flush()

        logger.info(f"Flushed {count} metrics to database")
        self._batch.clear()

        return count

    async def record_job_duration(
        self,
        composition_id: uuid.UUID,
        processing_job_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> JobMetric:
        """
        Record job processing duration.

        Args:
            composition_id: UUID of the composition
            processing_job_id: UUID of the processing job
            start_time: When the job started
            end_time: When the job ended (defaults to now)

        Returns:
            JobMetric: The created metric
        """
        if end_time is None:
            end_time = datetime.now(UTC)

        duration = (end_time - start_time).total_seconds()

        return await self.record_metric(
            metric_type=MetricType.PROCESSING_DURATION,
            value=duration,
            unit="seconds",
            composition_id=composition_id,
            processing_job_id=processing_job_id,
            recorded_at=end_time,
        )

    async def record_queue_wait_time(
        self,
        composition_id: uuid.UUID,
        processing_job_id: uuid.UUID,
        queued_at: datetime,
        started_at: datetime | None = None,
    ) -> JobMetric:
        """
        Record time job spent waiting in queue.

        Args:
            composition_id: UUID of the composition
            processing_job_id: UUID of the processing job
            queued_at: When the job was queued
            started_at: When the job started (defaults to now)

        Returns:
            JobMetric: The created metric
        """
        if started_at is None:
            started_at = datetime.now(UTC)

        wait_time = (started_at - queued_at).total_seconds()

        return await self.record_metric(
            metric_type=MetricType.QUEUE_WAIT_TIME,
            value=wait_time,
            unit="seconds",
            composition_id=composition_id,
            processing_job_id=processing_job_id,
            recorded_at=started_at,
        )

    async def record_memory_usage(
        self,
        composition_id: uuid.UUID,
        processing_job_id: uuid.UUID | None = None,
    ) -> JobMetric:
        """
        Record current memory usage.

        Args:
            composition_id: UUID of the composition
            processing_job_id: Optional UUID of the processing job

        Returns:
            JobMetric: The created metric
        """
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)

        return await self.record_metric(
            metric_type=MetricType.MEMORY_USAGE,
            value=memory_mb,
            unit="MB",
            composition_id=composition_id,
            processing_job_id=processing_job_id,
        )

    async def record_cpu_usage(
        self,
        composition_id: uuid.UUID,
        cpu_seconds: float,
        processing_job_id: uuid.UUID | None = None,
    ) -> JobMetric:
        """
        Record CPU time used.

        Args:
            composition_id: UUID of the composition
            cpu_seconds: CPU time in seconds
            processing_job_id: Optional UUID of the processing job

        Returns:
            JobMetric: The created metric
        """
        return await self.record_metric(
            metric_type=MetricType.CPU_USAGE,
            value=cpu_seconds,
            unit="cpu_seconds",
            composition_id=composition_id,
            processing_job_id=processing_job_id,
        )

    async def record_ffmpeg_stats(
        self,
        composition_id: uuid.UUID,
        processing_job_id: uuid.UUID,
        stats: dict[str, Any],
    ) -> list[JobMetric]:
        """
        Record FFmpeg processing statistics.

        Args:
            composition_id: UUID of the composition
            processing_job_id: UUID of the processing job
            stats: Dictionary containing FFmpeg stats
                Expected keys: frame_rate, bitrate, file_size

        Returns:
            list[JobMetric]: List of created metrics
        """
        metrics = []

        # Record frame rate
        if "frame_rate" in stats:
            metric = await self.record_metric(
                metric_type=MetricType.FRAME_RATE,
                value=stats["frame_rate"],
                unit="fps",
                composition_id=composition_id,
                processing_job_id=processing_job_id,
            )
            metrics.append(metric)

        # Record bitrate
        if "bitrate" in stats:
            metric = await self.record_metric(
                metric_type=MetricType.BITRATE,
                value=stats["bitrate"],
                unit="kbps",
                composition_id=composition_id,
                processing_job_id=processing_job_id,
            )
            metrics.append(metric)

        # Record file size
        if "file_size" in stats:
            metric = await self.record_metric(
                metric_type=MetricType.FILE_SIZE,
                value=stats["file_size"],
                unit="bytes",
                composition_id=composition_id,
                processing_job_id=processing_job_id,
            )
            metrics.append(metric)

        return metrics

    async def get_metric_summary(
        self,
        metric_type: MetricType,
        composition_id: uuid.UUID | None = None,
        processing_job_id: uuid.UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get aggregated summary statistics for a metric type.

        Args:
            metric_type: Type of metric to summarize
            composition_id: Optional filter by composition
            processing_job_id: Optional filter by processing job
            start_time: Optional start of time range
            end_time: Optional end of time range

        Returns:
            dict: Summary statistics including count, avg, min, max, sum
        """
        query = select(
            func.count(JobMetric.id).label("count"),
            func.avg(JobMetric.metric_value).label("avg"),
            func.min(JobMetric.metric_value).label("min"),
            func.max(JobMetric.metric_value).label("max"),
            func.sum(JobMetric.metric_value).label("sum"),
        ).where(JobMetric.metric_type == metric_type)

        if composition_id:
            query = query.where(JobMetric.composition_id == composition_id)

        if processing_job_id:
            query = query.where(JobMetric.processing_job_id == processing_job_id)

        if start_time:
            query = query.where(JobMetric.recorded_at >= start_time)

        if end_time:
            query = query.where(JobMetric.recorded_at <= end_time)

        result = await self.session.execute(query)
        row = result.one()

        return {
            "metric_type": metric_type.value,
            "count": row.count or 0,
            "average": float(row.avg) if row.avg is not None else 0.0,
            "minimum": float(row.min) if row.min is not None else 0.0,
            "maximum": float(row.max) if row.max is not None else 0.0,
            "total": float(row.sum) if row.sum is not None else 0.0,
        }

    async def get_hourly_aggregates(
        self,
        metric_type: MetricType,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get hourly aggregated metrics.

        Args:
            metric_type: Type of metric to aggregate
            start_time: Start of time range
            end_time: End of time range (defaults to now)

        Returns:
            list[dict]: Hourly aggregates with timestamp, count, avg, min, max
        """
        if end_time is None:
            end_time = datetime.now(UTC)

        query = (
            select(
                func.date_trunc("hour", JobMetric.recorded_at).label("hour"),
                func.count(JobMetric.id).label("count"),
                func.avg(JobMetric.metric_value).label("avg"),
                func.min(JobMetric.metric_value).label("min"),
                func.max(JobMetric.metric_value).label("max"),
            )
            .where(
                JobMetric.metric_type == metric_type,
                JobMetric.recorded_at >= start_time,
                JobMetric.recorded_at <= end_time,
            )
            .group_by(func.date_trunc("hour", JobMetric.recorded_at))
            .order_by(func.date_trunc("hour", JobMetric.recorded_at))
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "hour": row.hour.isoformat(),
                "count": row.count,
                "average": float(row.avg),
                "minimum": float(row.min),
                "maximum": float(row.max),
            }
            for row in rows
        ]


class JobMetricsContext:
    """
    Context manager for collecting metrics during job processing.

    Automatically records job duration, memory usage, and CPU time.
    """

    def __init__(
        self,
        collector: MetricsCollector,
        composition_id: uuid.UUID,
        processing_job_id: uuid.UUID,
    ) -> None:
        """
        Initialize job metrics context.

        Args:
            collector: MetricsCollector instance
            composition_id: UUID of the composition
            processing_job_id: UUID of the processing job
        """
        self.collector = collector
        self.composition_id = composition_id
        self.processing_job_id = processing_job_id
        self.start_time: datetime | None = None
        self.start_cpu_time: float = 0.0

    async def __aenter__(self) -> "JobMetricsContext":
        """Start metrics collection.

        Catches and logs any errors to ensure metrics failures don't impact job processing.
        """
        try:
            self.start_time = datetime.now(UTC)
            process = psutil.Process()
            self.start_cpu_time = process.cpu_times().user + process.cpu_times().system

            # Record initial memory usage
            await self.collector.record_memory_usage(
                composition_id=self.composition_id,
                processing_job_id=self.processing_job_id,
            )
        except Exception as e:
            # Log error but don't fail the job
            logger.error(
                "Failed to initialize job metrics",
                extra={
                    "composition_id": str(self.composition_id),
                    "processing_job_id": str(self.processing_job_id),
                    "error": str(e),
                },
                exc_info=True,
            )

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End metrics collection and record final metrics.

        Catches and logs any errors to ensure metrics failures don't impact job processing.
        """
        if self.start_time is None:
            return

        try:
            end_time = datetime.now(UTC)

            # Record job duration
            await self.collector.record_job_duration(
                composition_id=self.composition_id,
                processing_job_id=self.processing_job_id,
                start_time=self.start_time,
                end_time=end_time,
            )

            # Record CPU usage
            process = psutil.Process()
            end_cpu_time = process.cpu_times().user + process.cpu_times().system
            cpu_seconds = end_cpu_time - self.start_cpu_time

            await self.collector.record_cpu_usage(
                composition_id=self.composition_id,
                cpu_seconds=cpu_seconds,
                processing_job_id=self.processing_job_id,
            )

            # Record final memory usage
            await self.collector.record_memory_usage(
                composition_id=self.composition_id,
                processing_job_id=self.processing_job_id,
            )

            # Flush any batched metrics
            await self.collector.flush_batch()
        except Exception as e:
            # Log error but don't fail the job
            logger.error(
                "Failed to finalize job metrics",
                extra={
                    "composition_id": str(self.composition_id),
                    "processing_job_id": str(self.processing_job_id),
                    "error": str(e),
                },
                exc_info=True,
            )
