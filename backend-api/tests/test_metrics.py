"""Unit tests for metrics collection system."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import JobMetric, MetricType
from src.services.metrics import JobMetricsContext, MetricsCollector


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.add_all = Mock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def metrics_collector(mock_session: AsyncMock) -> MetricsCollector:
    """Create MetricsCollector instance with mock session."""
    return MetricsCollector(session=mock_session)


@pytest.fixture
def sample_composition_id() -> uuid.UUID:
    """Generate sample composition ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_job_id() -> uuid.UUID:
    """Generate sample processing job ID."""
    return uuid.uuid4()


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    @pytest.mark.asyncio
    async def test_record_metric(
        self,
        metrics_collector: MetricsCollector,
        mock_session: AsyncMock,
        sample_composition_id: uuid.UUID,
        sample_job_id: uuid.UUID,
    ) -> None:
        """Test recording a single metric."""
        metric = await metrics_collector.record_metric(
            metric_type=MetricType.PROCESSING_DURATION,
            value=10.5,
            unit="seconds",
            composition_id=sample_composition_id,
            processing_job_id=sample_job_id,
        )

        # Verify metric was added to session
        assert mock_session.add.called
        assert mock_session.flush.called

        # Verify metric properties
        assert isinstance(metric, JobMetric)
        assert metric.metric_type == MetricType.PROCESSING_DURATION
        assert metric.metric_value == Decimal("10.5")
        assert metric.metric_unit == "seconds"
        assert metric.composition_id == sample_composition_id
        assert metric.processing_job_id == sample_job_id

    @pytest.mark.asyncio
    async def test_record_metric_with_float_value(
        self,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
    ) -> None:
        """Test that float values are converted to Decimal."""
        metric = await metrics_collector.record_metric(
            metric_type=MetricType.MEMORY_USAGE,
            value=1024.5678,
            unit="MB",
            composition_id=sample_composition_id,
        )

        assert isinstance(metric.metric_value, Decimal)
        assert metric.metric_value == Decimal("1024.5678")

    @pytest.mark.asyncio
    async def test_batch_metrics(
        self,
        metrics_collector: MetricsCollector,
        mock_session: AsyncMock,
        sample_composition_id: uuid.UUID,
    ) -> None:
        """Test batch metric collection."""
        # Add metrics to batch
        for i in range(5):
            metrics_collector.add_to_batch(
                metric_type=MetricType.FRAME_RATE,
                value=30.0 + i,
                unit="fps",
                composition_id=sample_composition_id,
            )

        # Verify batch is populated
        assert len(metrics_collector._batch) == 5

        # Flush batch
        count = await metrics_collector.flush_batch()

        # Verify all metrics were flushed
        assert count == 5
        assert len(metrics_collector._batch) == 0
        assert mock_session.add_all.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_flush_empty_batch(
        self, metrics_collector: MetricsCollector, mock_session: AsyncMock
    ) -> None:
        """Test flushing empty batch returns 0."""
        count = await metrics_collector.flush_batch()

        assert count == 0
        assert not mock_session.add_all.called

    @pytest.mark.asyncio
    async def test_record_job_duration(
        self,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
        sample_job_id: uuid.UUID,
    ) -> None:
        """Test recording job duration."""
        start_time = datetime.now(UTC)
        end_time = start_time + timedelta(seconds=10)

        metric = await metrics_collector.record_job_duration(
            composition_id=sample_composition_id,
            processing_job_id=sample_job_id,
            start_time=start_time,
            end_time=end_time,
        )

        assert metric.metric_type == MetricType.PROCESSING_DURATION
        assert metric.metric_unit == "seconds"
        assert float(metric.metric_value) == 10.0

    @pytest.mark.asyncio
    async def test_record_queue_wait_time(
        self,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
        sample_job_id: uuid.UUID,
    ) -> None:
        """Test recording queue wait time."""
        queued_at = datetime.now(UTC)
        started_at = queued_at + timedelta(seconds=5)

        metric = await metrics_collector.record_queue_wait_time(
            composition_id=sample_composition_id,
            processing_job_id=sample_job_id,
            queued_at=queued_at,
            started_at=started_at,
        )

        assert metric.metric_type == MetricType.QUEUE_WAIT_TIME
        assert metric.metric_unit == "seconds"
        assert float(metric.metric_value) == 5.0

    @pytest.mark.asyncio
    @patch("src.services.metrics.psutil.Process")
    async def test_record_memory_usage(
        self,
        mock_process_class: Mock,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
    ) -> None:
        """Test recording memory usage."""
        # Mock process memory info
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100 MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        metric = await metrics_collector.record_memory_usage(
            composition_id=sample_composition_id,
        )

        assert metric.metric_type == MetricType.MEMORY_USAGE
        assert metric.metric_unit == "MB"
        assert float(metric.metric_value) == 100.0

    @pytest.mark.asyncio
    async def test_record_cpu_usage(
        self,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
    ) -> None:
        """Test recording CPU usage."""
        metric = await metrics_collector.record_cpu_usage(
            composition_id=sample_composition_id,
            cpu_seconds=15.5,
        )

        assert metric.metric_type == MetricType.CPU_USAGE
        assert metric.metric_unit == "cpu_seconds"
        assert float(metric.metric_value) == 15.5

    @pytest.mark.asyncio
    async def test_record_ffmpeg_stats(
        self,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
        sample_job_id: uuid.UUID,
    ) -> None:
        """Test recording FFmpeg statistics."""
        stats = {
            "frame_rate": 30.0,
            "bitrate": 5000.0,
            "file_size": 1024000,
        }

        metrics = await metrics_collector.record_ffmpeg_stats(
            composition_id=sample_composition_id,
            processing_job_id=sample_job_id,
            stats=stats,
        )

        assert len(metrics) == 3

        # Verify frame rate metric
        frame_rate_metric = metrics[0]
        assert frame_rate_metric.metric_type == MetricType.FRAME_RATE
        assert frame_rate_metric.metric_unit == "fps"
        assert float(frame_rate_metric.metric_value) == 30.0

        # Verify bitrate metric
        bitrate_metric = metrics[1]
        assert bitrate_metric.metric_type == MetricType.BITRATE
        assert bitrate_metric.metric_unit == "kbps"
        assert float(bitrate_metric.metric_value) == 5000.0

        # Verify file size metric
        file_size_metric = metrics[2]
        assert file_size_metric.metric_type == MetricType.FILE_SIZE
        assert file_size_metric.metric_unit == "bytes"
        assert float(file_size_metric.metric_value) == 1024000

    @pytest.mark.asyncio
    async def test_get_metric_summary(
        self,
        metrics_collector: MetricsCollector,
        mock_session: AsyncMock,
        sample_composition_id: uuid.UUID,
    ) -> None:
        """Test getting metric summary statistics."""
        # Mock query result
        mock_result = Mock()
        mock_row = Mock()
        mock_row.count = 10
        mock_row.avg = Decimal("5.5")
        mock_row.min = Decimal("1.0")
        mock_row.max = Decimal("10.0")
        mock_row.sum = Decimal("55.0")
        mock_result.one.return_value = mock_row
        mock_session.execute.return_value = mock_result

        summary = await metrics_collector.get_metric_summary(
            metric_type=MetricType.PROCESSING_DURATION,
            composition_id=sample_composition_id,
        )

        assert summary["metric_type"] == "processing_duration"
        assert summary["count"] == 10
        assert summary["average"] == 5.5
        assert summary["minimum"] == 1.0
        assert summary["maximum"] == 10.0
        assert summary["total"] == 55.0

    @pytest.mark.asyncio
    async def test_get_hourly_aggregates(
        self,
        metrics_collector: MetricsCollector,
        mock_session: AsyncMock,
    ) -> None:
        """Test getting hourly aggregated metrics."""
        # Mock query result
        mock_result = Mock()
        mock_rows = [
            Mock(
                hour=datetime(2025, 11, 14, 10, 0, 0, tzinfo=UTC),
                count=5,
                avg=Decimal("5.0"),
                min=Decimal("3.0"),
                max=Decimal("7.0"),
            ),
            Mock(
                hour=datetime(2025, 11, 14, 11, 0, 0, tzinfo=UTC),
                count=8,
                avg=Decimal("6.5"),
                min=Decimal("4.0"),
                max=Decimal("9.0"),
            ),
        ]
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        start_time = datetime(2025, 11, 14, 10, 0, 0, tzinfo=UTC)
        end_time = datetime(2025, 11, 14, 12, 0, 0, tzinfo=UTC)

        aggregates = await metrics_collector.get_hourly_aggregates(
            metric_type=MetricType.PROCESSING_DURATION,
            start_time=start_time,
            end_time=end_time,
        )

        assert len(aggregates) == 2
        assert aggregates[0]["count"] == 5
        assert aggregates[0]["average"] == 5.0
        assert aggregates[1]["count"] == 8
        assert aggregates[1]["average"] == 6.5


class TestJobMetricsContext:
    """Tests for JobMetricsContext context manager."""

    @pytest.mark.asyncio
    @patch("src.services.metrics.psutil.Process")
    async def test_job_metrics_context(
        self,
        mock_process_class: Mock,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
        sample_job_id: uuid.UUID,
    ) -> None:
        """Test JobMetricsContext records metrics."""
        # Mock process for CPU and memory tracking
        mock_process = Mock()
        mock_cpu_times = Mock()
        mock_cpu_times.user = 1.0
        mock_cpu_times.system = 0.5
        mock_process.cpu_times.return_value = mock_cpu_times
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 50  # 50 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        async with JobMetricsContext(
            collector=metrics_collector,
            composition_id=sample_composition_id,
            processing_job_id=sample_job_id,
        ):
            # Simulate some work
            # CPU time increases
            mock_cpu_times.user = 2.0
            mock_cpu_times.system = 1.0

        # Verify session operations were called
        # Should have called add (for initial memory + duration + cpu + final memory)
        assert metrics_collector.session.add.call_count >= 3
        assert metrics_collector.session.flush.called

    @pytest.mark.asyncio
    @patch("src.services.metrics.psutil.Process")
    async def test_job_metrics_context_with_exception(
        self,
        mock_process_class: Mock,
        metrics_collector: MetricsCollector,
        sample_composition_id: uuid.UUID,
        sample_job_id: uuid.UUID,
    ) -> None:
        """Test JobMetricsContext still records metrics on exception."""
        mock_process = Mock()
        mock_cpu_times = Mock()
        mock_cpu_times.user = 1.0
        mock_cpu_times.system = 0.5
        mock_process.cpu_times.return_value = mock_cpu_times
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 50
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        with pytest.raises(ValueError):
            async with JobMetricsContext(
                collector=metrics_collector,
                composition_id=sample_composition_id,
                processing_job_id=sample_job_id,
            ):
                raise ValueError("Test error")

        # Metrics should still be recorded despite exception
        assert metrics_collector.session.add.called
        assert metrics_collector.session.flush.called
