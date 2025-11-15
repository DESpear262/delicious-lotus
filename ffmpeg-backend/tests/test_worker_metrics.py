"""Unit tests for worker metrics integration."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def sample_composition_id() -> uuid.UUID:
    """Create sample composition ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_job_id() -> uuid.UUID:
    """Create sample job ID."""
    return uuid.uuid4()


@pytest.mark.asyncio
async def test_worker_records_job_metrics(
    mock_session: AsyncMock,
    sample_composition_id: uuid.UUID,
    sample_job_id: uuid.UUID,
) -> None:
    """Test that worker job handler records metrics correctly."""
    from src.services.metrics import JobMetricsContext, MetricsCollector

    metrics_collector = MetricsCollector(mock_session)

    # Simulate job execution with metrics context
    async with JobMetricsContext(
        collector=metrics_collector,
        composition_id=sample_composition_id,
        processing_job_id=sample_job_id,
    ):
        # Simulate some work
        import time

        time.sleep(0.1)

    # Verify metrics were recorded
    assert mock_session.add.called
    assert mock_session.flush.called


@pytest.mark.asyncio
async def test_worker_records_ffmpeg_stats(
    mock_session: AsyncMock,
    sample_composition_id: uuid.UUID,
    sample_job_id: uuid.UUID,
) -> None:
    """Test that worker records FFmpeg statistics."""
    from src.services.metrics import MetricsCollector

    metrics_collector = MetricsCollector(mock_session)

    # Record FFmpeg stats
    metrics = await metrics_collector.record_ffmpeg_stats(
        composition_id=sample_composition_id,
        processing_job_id=sample_job_id,
        stats={
            "frame_rate": 30.0,
            "bitrate": 5000.0,
            "file_size": 1024 * 1024 * 10,  # 10MB
        },
    )

    # Verify metrics were created
    assert len(metrics) > 0
    assert metrics[0].__class__.__name__ == "JobMetric"
    assert metrics[0].composition_id == sample_composition_id
    assert metrics[0].processing_job_id == sample_job_id

    # Verify session operations were called
    assert mock_session.add.called
    assert mock_session.flush.called


@pytest.mark.asyncio
async def test_worker_handles_metrics_failure_gracefully(
    sample_composition_id: uuid.UUID,
    sample_job_id: uuid.UUID,
) -> None:
    """Test that worker handles metrics collection failures gracefully."""
    from services.metrics import JobMetricsContext, MetricsCollector

    # Create session that fails on flush
    failing_session = AsyncMock(spec=AsyncSession)
    failing_session.add = Mock()
    failing_session.flush = AsyncMock(side_effect=Exception("Database error"))

    metrics_collector = MetricsCollector(failing_session)

    # Job should still complete even if metrics fail
    try:
        async with JobMetricsContext(
            collector=metrics_collector,
            composition_id=sample_composition_id,
            processing_job_id=sample_job_id,
        ):
            # Simulate some work
            pass
    except Exception:
        # Metrics errors should be caught and logged
        pytest.fail("JobMetricsContext should not raise on metrics errors")


@pytest.mark.asyncio
async def test_metrics_collector_batch_operations(
    mock_session: AsyncMock,
    sample_composition_id: uuid.UUID,
) -> None:
    """Test batch metric collection for multiple operations."""
    from db.models.job import MetricType
    from services.metrics import MetricsCollector

    metrics_collector = MetricsCollector(mock_session)

    # Add multiple metrics to batch
    for i in range(5):
        metrics_collector.add_to_batch(
            metric_type=MetricType.FRAME_RATE,
            value=30.0 + i,
            unit="fps",
            composition_id=sample_composition_id,
        )

    # Flush batch
    count = await metrics_collector.flush_batch()

    assert count == 5
    assert mock_session.add_all.called
    assert mock_session.flush.called
