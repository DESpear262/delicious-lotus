"""Unit tests for health check endpoints."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)


def test_basic_health_check():
    """Test basic /health endpoint returns healthy status."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_detailed_health_check_all_healthy():
    """Test /healthz returns healthy when all components are up."""
    with (
        patch("src.app.api.v1.health.check_database") as mock_db,
        patch("src.app.api.v1.health.check_redis") as mock_redis,
        patch("src.app.api.v1.health.check_s3") as mock_s3,
        patch("src.app.api.v1.health.check_ffmpeg") as mock_ffmpeg,
        patch("src.app.api.v1.health.get_system_metrics") as mock_metrics,
    ):
        # Mock all components as healthy
        from src.app.api.v1.health import ComponentStatus

        mock_db.return_value = ComponentStatus(
            name="database",
            status="healthy",
            response_time_ms=10.5,
            details={"type": "postgresql"},
        )
        mock_redis.return_value = ComponentStatus(
            name="redis", status="healthy", response_time_ms=5.2
        )
        mock_s3.return_value = ComponentStatus(name="s3", status="healthy", response_time_ms=15.3)
        mock_ffmpeg.return_value = ComponentStatus(
            name="ffmpeg", status="healthy", response_time_ms=20.1
        )
        mock_metrics.return_value = {
            "cpu_percent": 25.5,
            "memory_percent": 60.2,
        }

        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert len(data["components"]) == 4
        assert "system" in data
        assert data["system"]["cpu_percent"] == 25.5


@pytest.mark.asyncio
async def test_detailed_health_check_critical_unhealthy():
    """Test /healthz returns 503 when critical component is unhealthy."""
    with (
        patch("src.app.api.v1.health.check_database") as mock_db,
        patch("src.app.api.v1.health.check_redis") as mock_redis,
        patch("src.app.api.v1.health.check_s3") as mock_s3,
        patch("src.app.api.v1.health.check_ffmpeg") as mock_ffmpeg,
        patch("src.app.api.v1.health.get_system_metrics") as mock_metrics,
    ):
        from src.app.api.v1.health import ComponentStatus

        # Mock database as unhealthy (critical component)
        mock_db.return_value = ComponentStatus(
            name="database",
            status="unhealthy",
            response_time_ms=100.0,
            error="Connection refused",
        )
        mock_redis.return_value = ComponentStatus(
            name="redis", status="healthy", response_time_ms=5.2
        )
        mock_s3.return_value = ComponentStatus(name="s3", status="healthy", response_time_ms=15.3)
        mock_ffmpeg.return_value = ComponentStatus(
            name="ffmpeg", status="healthy", response_time_ms=20.1
        )
        mock_metrics.return_value = {"cpu_percent": 25.5}

        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_detailed_health_check_non_critical_degraded():
    """Test /healthz returns degraded when non-critical component fails."""
    with (
        patch("src.app.api.v1.health.check_database") as mock_db,
        patch("src.app.api.v1.health.check_redis") as mock_redis,
        patch("src.app.api.v1.health.check_s3") as mock_s3,
        patch("src.app.api.v1.health.check_ffmpeg") as mock_ffmpeg,
        patch("src.app.api.v1.health.get_system_metrics") as mock_metrics,
    ):
        from src.app.api.v1.health import ComponentStatus

        # All critical components healthy, but S3 degraded
        mock_db.return_value = ComponentStatus(
            name="database", status="healthy", response_time_ms=10.5
        )
        mock_redis.return_value = ComponentStatus(
            name="redis", status="healthy", response_time_ms=5.2
        )
        mock_s3.return_value = ComponentStatus(
            name="s3",
            status="degraded",
            response_time_ms=0.0,
            details={"message": "S3 bucket not configured"},
        )
        mock_ffmpeg.return_value = ComponentStatus(
            name="ffmpeg", status="healthy", response_time_ms=20.1
        )
        mock_metrics.return_value = {"cpu_percent": 25.5}

        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


@pytest.mark.asyncio
async def test_check_database_healthy():
    """Test database health check returns healthy status."""
    from src.app.api.v1.health import check_database

    with patch("src.app.api.v1.health.get_db_session") as mock_get_session:
        # Mock database session
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        mock_get_session.return_value.__aenter__.return_value = mock_session

        result = await check_database()

        assert result.name == "database"
        assert result.status == "healthy"
        assert result.response_time_ms is not None
        assert result.response_time_ms > 0
        assert result.details["type"] == "postgresql"


@pytest.mark.asyncio
async def test_check_database_unhealthy():
    """Test database health check returns unhealthy on connection error."""
    from src.app.api.v1.health import check_database

    with patch("src.app.api.v1.health.get_db_session") as mock_get_session:
        # Mock database connection failure
        mock_get_session.return_value.__aenter__.side_effect = Exception("Connection refused")

        result = await check_database()

        assert result.name == "database"
        assert result.status == "unhealthy"
        assert result.error == "Connection refused"


@pytest.mark.asyncio
async def test_check_redis_healthy():
    """Test Redis health check returns healthy status."""
    from src.app.api.v1.health import check_redis

    with patch("src.app.api.v1.health.Redis") as mock_redis_class:
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.set.return_value = True
        mock_redis.get.return_value = "ok"
        mock_redis.delete.return_value = True
        mock_redis_class.from_url.return_value = mock_redis

        result = await check_redis()

        assert result.name == "redis"
        assert result.status == "healthy"
        assert result.response_time_ms is not None
        mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_check_redis_unhealthy():
    """Test Redis health check returns unhealthy on connection error."""
    from src.app.api.v1.health import check_redis

    with patch("src.app.api.v1.health.Redis") as mock_redis_class:
        # Mock Redis connection failure
        mock_redis_class.from_url.side_effect = Exception("Connection refused")

        result = await check_redis()

        assert result.name == "redis"
        assert result.status == "unhealthy"
        assert result.error == "Connection refused"


@pytest.mark.asyncio
async def test_check_s3_healthy():
    """Test S3 health check returns healthy status."""
    from src.app.api.v1.health import check_s3

    with (
        patch("boto3.client") as mock_boto3_client,
        patch("src.app.api.v1.health.settings") as mock_settings,
    ):
        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_client.list_objects_v2.return_value = {"Contents": []}
        mock_boto3_client.return_value = mock_s3_client
        mock_settings.s3_bucket_name = "test-bucket"
        mock_settings.s3_region = "us-east-1"
        mock_settings.s3_access_key_id = "test-key"
        mock_settings.s3_secret_access_key = "test-secret"  # noqa: S105
        mock_settings.s3_endpoint_url = None

        result = await check_s3()

        assert result.name == "s3"
        assert result.status == "healthy"
        assert result.details["bucket"] == "test-bucket"


@pytest.mark.asyncio
async def test_check_s3_degraded_no_bucket():
    """Test S3 health check returns degraded when bucket not configured."""
    from src.app.api.v1.health import check_s3

    with patch("src.app.api.v1.health.settings") as mock_settings:
        mock_settings.s3_bucket_name = ""
        mock_settings.s3_region = "us-east-1"
        mock_settings.s3_access_key_id = None
        mock_settings.s3_secret_access_key = None
        mock_settings.s3_endpoint_url = None

        result = await check_s3()

        assert result.name == "s3"
        assert result.status == "degraded"
        assert "not configured" in result.details["message"]


@pytest.mark.asyncio
async def test_check_ffmpeg_healthy():
    """Test FFmpeg health check returns healthy status."""
    from src.app.api.v1.health import check_ffmpeg

    with (
        patch("src.app.api.v1.health.os.path.exists") as mock_exists,
        patch("src.app.api.v1.health.subprocess.run") as mock_run,
        patch("src.app.api.v1.health.settings") as mock_settings,
    ):
        mock_settings.ffmpeg_path = "/usr/bin/ffmpeg"
        mock_exists.return_value = True
        mock_result = Mock()
        mock_result.stdout = "ffmpeg version 6.0\ncopyright info"
        mock_run.return_value = mock_result

        result = await check_ffmpeg()

        assert result.name == "ffmpeg"
        assert result.status == "healthy"
        assert "ffmpeg version" in result.details["version"]


@pytest.mark.asyncio
async def test_check_ffmpeg_unhealthy_not_found():
    """Test FFmpeg health check returns unhealthy when binary not found."""
    from src.app.api.v1.health import check_ffmpeg

    with (
        patch("src.app.api.v1.health.os.path.exists") as mock_exists,
        patch("src.app.api.v1.health.settings") as mock_settings,
    ):
        mock_settings.ffmpeg_path = "/usr/bin/ffmpeg"
        mock_exists.return_value = False

        result = await check_ffmpeg()

        assert result.name == "ffmpeg"
        assert result.status == "unhealthy"
        assert "not found" in result.error


def test_get_system_metrics():
    """Test system metrics collection."""
    from src.app.api.v1.health import get_system_metrics

    metrics = get_system_metrics()

    assert "cpu_percent" in metrics
    assert "memory_total_mb" in metrics
    assert "memory_used_mb" in metrics
    assert "memory_percent" in metrics
    assert "disk_total_gb" in metrics
    assert "disk_used_gb" in metrics
    assert "disk_percent" in metrics

    # Verify values are reasonable
    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["memory_percent"] <= 100
    assert 0 <= metrics["disk_percent"] <= 100
