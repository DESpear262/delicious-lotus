"""
Pytest configuration and shared fixtures for testing.

Provides comprehensive test fixtures for database, Redis, S3, and FFmpeg mocking.
"""

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Initialize faker for test data generation
fake = Faker()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Provide test database URL.

    Uses in-memory SQLite for fast, isolated tests.

    Returns:
        str: SQLite database URL
    """
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def async_engine(test_database_url: str):
    """
    Create async database engine for tests.

    Uses StaticPool to maintain single connection to in-memory database.

    Args:
        test_database_url: Database URL for tests

    Yields:
        AsyncEngine: Configured test database engine
    """
    from db.base import Base

    engine = create_async_engine(
        test_database_url,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create isolated database session for each test.

    Uses nested transactions to rollback changes after each test.

    Args:
        async_engine: Async database engine

    Yields:
        AsyncSession: Isolated database session
    """
    from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionClass

    connection = await async_engine.connect()
    transaction = await connection.begin()

    session = AsyncSessionClass(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
def sync_db_session(test_database_url: str) -> Generator[Session, None, None]:
    """
    Create synchronous database session for non-async tests.

    Args:
        test_database_url: Database URL for tests

    Yields:
        Session: Synchronous database session
    """
    from db.base import Base

    # Convert async URL to sync
    sync_url = test_database_url.replace("+aiosqlite", "")

    engine = create_engine(
        sync_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session with nested transaction
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


# ============================================================================
# Redis Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def redis_client():
    """
    Create mock Redis client for tests.

    Uses fakeredis for in-memory Redis simulation.

    Yields:
        FakeRedis: Mock Redis client
    """
    import fakeredis

    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    client.flushall()
    client.close()


@pytest.fixture
async def async_redis_client():
    """
    Create async mock Redis client for tests.

    Yields:
        FakeAsyncRedis: Mock async Redis client
    """
    import fakeredis.aioredis

    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest.fixture
def mock_redis_pool(redis_client):
    """
    Mock Redis connection pool for worker tests.

    Args:
        redis_client: Mock Redis client

    Yields:
        MagicMock: Mock connection pool
    """
    with patch("redis.Redis.from_url") as mock_pool:
        mock_pool.return_value = redis_client
        yield mock_pool


@pytest.fixture
def mock_rq_queue(redis_client):
    """
    Mock RQ (Redis Queue) for job testing.

    Args:
        redis_client: Mock Redis client

    Yields:
        MagicMock: Mock RQ queue
    """
    with patch("rq.Queue") as mock_queue:
        queue_instance = MagicMock()
        queue_instance.enqueue = MagicMock()
        queue_instance.count = 0
        mock_queue.return_value = queue_instance
        yield queue_instance


# ============================================================================
# S3 / Object Storage Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def aws_credentials():
    """Set up mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def s3_client(aws_credentials):
    """
    Create mock S3 client for tests.

    Uses moto for S3 mocking.

    Args:
        aws_credentials: Mock AWS credentials

    Yields:
        boto3.client: Mock S3 client
    """
    import boto3

    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        # Create test bucket
        s3.create_bucket(Bucket="test-ffmpeg-bucket")
        yield s3


@pytest.fixture
def s3_resource(aws_credentials):
    """
    Create mock S3 resource for tests.

    Args:
        aws_credentials: Mock AWS credentials

    Yields:
        boto3.resource: Mock S3 resource
    """
    import boto3

    with mock_aws():
        s3 = boto3.resource("s3", region_name="us-east-1")
        # Create test bucket
        s3.create_bucket(Bucket="test-ffmpeg-bucket")
        yield s3


# ============================================================================
# FFmpeg Fixtures
# ============================================================================


@pytest.fixture
def mock_ffmpeg_command():
    """
    Mock FFmpeg command execution.

    Yields:
        MagicMock: Mock FFmpeg command runner
    """
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b"FFmpeg output",
            stderr=b"",
        )
        yield mock_run


@pytest.fixture
def mock_ffmpeg_async():
    """
    Mock async FFmpeg command execution.

    Yields:
        AsyncMock: Mock async FFmpeg runner
    """
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        process = AsyncMock()
        process.communicate = AsyncMock(return_value=(b"output", b""))
        process.returncode = 0
        mock_exec.return_value = process
        yield mock_exec


@pytest.fixture
def mock_ffprobe():
    """
    Mock ffprobe for video metadata extraction.

    Yields:
        MagicMock: Mock ffprobe
    """
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b'{"streams": [{"codec_type": "video", "width": 1920, "height": 1080, "duration": "10.0"}]}',
            stderr=b"",
        )
        yield mock_run


# ============================================================================
# File System Fixtures
# ============================================================================


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create temporary directory for test files.

    Automatically cleaned up after test.

    Yields:
        Path: Temporary directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_video_file(temp_dir: Path) -> Path:
    """
    Create temporary mock video file.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path: Path to mock video file
    """
    video_file = temp_dir / "test_video.mp4"
    video_file.write_bytes(b"MOCK_VIDEO_CONTENT")
    return video_file


@pytest.fixture
def temp_audio_file(temp_dir: Path) -> Path:
    """
    Create temporary mock audio file.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path: Path to mock audio file
    """
    audio_file = temp_dir / "test_audio.mp3"
    audio_file.write_bytes(b"MOCK_AUDIO_CONTENT")
    return audio_file


# ============================================================================
# FastAPI / HTTP Client Fixtures
# ============================================================================


@pytest.fixture
def test_app():
    """
    Create test FastAPI application.

    Returns:
        FastAPI: Test application instance
    """
    from src.app.main import create_app

    app = create_app()
    return app


@pytest.fixture
def client(test_app) -> Generator[TestClient, None, None]:
    """
    Create test HTTP client.

    Args:
        test_app: FastAPI test application

    Yields:
        TestClient: Test HTTP client
    """
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def async_client(test_app):
    """
    Create async test HTTP client.

    Args:
        test_app: FastAPI test application

    Yields:
        AsyncClient: Async test HTTP client
    """
    from httpx import AsyncClient

    async def _client():
        async with AsyncClient(app=test_app, base_url="http://test") as ac:
            yield ac

    return _client


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """
    Create authenticated test client with internal auth token.

    Args:
        client: Base test client

    Returns:
        TestClient: Client with auth headers
    """
    import os

    internal_token = os.getenv("INTERNAL_AUTH_TOKEN", "test-internal-token")
    client.headers["X-Internal-Auth"] = internal_token
    return client


# ============================================================================
# Settings / Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_settings():
    """
    Provide test application settings.

    Returns:
        Settings: Test configuration
    """
    from app.config import Settings

    return Settings(
        environment="testing",
        debug=True,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",
        s3_access_key_id="testing",
        s3_secret_access_key="testing",
        s3_region="us-east-1",
        s3_bucket_name="test-ffmpeg-bucket",
    )


@pytest.fixture
def override_settings(test_settings, monkeypatch):
    """
    Override application settings for tests that need it.

    Args:
        test_settings: Test configuration
        monkeypatch: Pytest monkeypatch fixture
    """

    monkeypatch.setattr("app.config.get_settings", lambda: test_settings)
    return test_settings


# ============================================================================
# Test Data Factories
# ============================================================================


@pytest.fixture
def composition_factory():
    """
    Factory for creating test composition data.

    Returns:
        callable: Factory function
    """

    def _create_composition(**kwargs: Any) -> dict[str, Any]:
        """Create test composition data."""
        default = {
            "title": fake.sentence(nb_words=4),
            "description": fake.text(max_nb_chars=200),
            "clips": [],
            "audio_tracks": [],
            "output_settings": {
                "format": "mp4",
                "resolution": "1920x1080",
                "fps": 30,
            },
        }
        default.update(kwargs)
        return default

    return _create_composition


@pytest.fixture
def clip_factory():
    """
    Factory for creating test clip data.

    Returns:
        callable: Factory function
    """

    def _create_clip(**kwargs: Any) -> dict[str, Any]:
        """Create test clip data."""
        default = {
            "url": fake.url(),
            "start_time": 0.0,
            "duration": 5.0,
            "position": 0,
        }
        default.update(kwargs)
        return default

    return _create_clip


# ============================================================================
# Async Helpers
# ============================================================================


@pytest.fixture
def event_loop():
    """
    Create event loop for async tests.

    Yields:
        asyncio.EventLoop: Event loop
    """
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Logging Configuration for Tests
# ============================================================================


@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configure logging for tests to reduce noise."""
    import logging

    # Reduce logging verbosity during tests
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("faker").setLevel(logging.WARNING)
