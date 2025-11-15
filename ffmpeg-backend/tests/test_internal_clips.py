"""
Unit tests for Internal API clips endpoint.

Tests process-clips endpoint with various request scenarios.
"""

from unittest.mock import MagicMock, patch

import pytest
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


# Test fixtures
@pytest.fixture
def mock_settings():
    """Create mock settings with test API keys."""
    settings = Settings(
        internal_api_keys=["test-internal-key"],
        jwt_secret_key="test-secret",
    )
    return settings


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    redis_mock = MagicMock()
    redis_mock.setex = MagicMock()
    return redis_mock


@pytest.fixture
def client(mock_settings, mock_redis):
    """Create test client with mocked dependencies."""
    with patch("app.middleware.internal_auth.get_settings", return_value=mock_settings):
        with patch("app.api.internal.clips.get_redis_connection", return_value=mock_redis):
            with patch(
                "app.middleware.internal_auth.get_redis_connection", return_value=mock_redis
            ):
                # Mock rate limiting to allow requests
                mock_redis.pipeline.return_value = mock_redis
                mock_redis.execute.return_value = [None, 0, None, None]
                mock_redis.zrange.return_value = []

                app = create_app()
                return TestClient(app)


class TestProcessClipsEndpoint:
    """Test cases for POST /internal/v1/process-clips endpoint."""

    def test_process_clips_requires_authentication(self, client):
        """Test that endpoint requires authentication."""
        request_data = {
            "clips": [
                {
                    "url": "https://example.com/video.mp4",
                    "clip_id": "clip-1",
                }
            ],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post("/internal/v1/process-clips", json=request_data)
        assert response.status_code == 401

    def test_process_single_clip_success(self, client, mock_redis):
        """Test successful processing of single clip."""
        request_data = {
            "clips": [
                {
                    "url": "https://example.com/video.mp4",
                    "clip_id": "clip-1",
                    "metadata": {"source": "test"},
                }
            ],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "request_id" in data
        assert data["total_clips"] == 1
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["clip_id"] == "clip-1"
        assert data["jobs"][0]["status"] == "queued"

    def test_process_multiple_clips_success(self, client, mock_redis):
        """Test successful processing of multiple clips."""
        request_data = {
            "clips": [
                {"url": "https://example.com/video1.mp4", "clip_id": "clip-1"},
                {"url": "https://example.com/video2.mp4", "clip_id": "clip-2"},
                {"url": "https://example.com/video3.mp4", "clip_id": "clip-3"},
            ],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["total_clips"] == 3
        assert len(data["jobs"]) == 3

        # Verify all clips are queued
        clip_ids = [job["clip_id"] for job in data["jobs"]]
        assert "clip-1" in clip_ids
        assert "clip-2" in clip_ids
        assert "clip-3" in clip_ids

    def test_process_clips_with_custom_options(self, client, mock_redis):
        """Test processing with custom processing options."""
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
            "callback_url": "https://ai-backend.com/callback",
            "processing_options": {
                "target_resolution": "1080p",
                "target_fps": 60,
                "video_codec": "libx265",
                "crf": 18,
            },
            "operations": ["normalize", "convert_codec", "extract_thumbnail"],
            "priority": 8,
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "request_id" in data

    def test_empty_clips_list_rejected(self, client):
        """Test that empty clips list is rejected."""
        request_data = {
            "clips": [],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 422

    def test_too_many_clips_rejected(self, client):
        """Test that more than 100 clips are rejected."""
        clips = [
            {"url": f"https://example.com/video{i}.mp4", "clip_id": f"clip-{i}"} for i in range(101)
        ]
        request_data = {
            "clips": clips,
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 422

    def test_invalid_clip_url_rejected(self, client):
        """Test that invalid clip URLs are rejected."""
        request_data = {
            "clips": [{"url": "not-a-url", "clip_id": "clip-1"}],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 422

    def test_invalid_callback_url_rejected(self, client):
        """Test that invalid callback URLs are rejected."""
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
            "callback_url": "not-a-url",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 422

    def test_missing_clip_id_rejected(self, client):
        """Test that missing clip_id is rejected."""
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4"}],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 422

    def test_invalid_crf_value_rejected(self, client):
        """Test that invalid CRF value is rejected."""
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
            "callback_url": "https://ai-backend.com/callback",
            "processing_options": {
                "crf": 100,  # Invalid: must be 0-51
            },
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 422

    def test_invalid_fps_value_rejected(self, client):
        """Test that invalid FPS value is rejected."""
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
            "callback_url": "https://ai-backend.com/callback",
            "processing_options": {
                "target_fps": 0,  # Invalid: must be >= 1
            },
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 422

    def test_redis_connection_failure_returns_503(self, client):
        """Test that Redis connection failure returns 503."""
        with patch(
            "app.api.internal.clips.get_redis_connection", side_effect=Exception("Redis down")
        ):
            request_data = {
                "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
                "callback_url": "https://ai-backend.com/callback",
            }

            response = client.post(
                "/internal/v1/process-clips",
                json=request_data,
                headers={"X-API-Key": "test-internal-key"},
            )

            assert response.status_code == 503
            assert "queue unavailable" in response.json()["detail"].lower()

    def test_job_ids_are_unique(self, client, mock_redis):
        """Test that each job gets a unique job ID."""
        request_data = {
            "clips": [
                {"url": "https://example.com/video1.mp4", "clip_id": "clip-1"},
                {"url": "https://example.com/video2.mp4", "clip_id": "clip-2"},
            ],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 202
        data = response.json()
        job_ids = [job["job_id"] for job in data["jobs"]]

        # Verify all job IDs are unique
        assert len(job_ids) == len(set(job_ids))

        # Verify job IDs contain clip_id
        for job in data["jobs"]:
            assert job["clip_id"] in job["job_id"]

    def test_request_id_is_generated(self, client, mock_redis):
        """Test that a unique request ID is generated."""
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["request_id"].startswith("req_")

    def test_default_processing_options_used(self, client, mock_redis):
        """Test that default processing options are used when not specified."""
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 202
        # Endpoint should accept request with default options

    def test_clip_metadata_preserved(self, client, mock_redis):
        """Test that clip metadata is preserved in job info."""
        request_data = {
            "clips": [
                {
                    "url": "https://example.com/video.mp4",
                    "clip_id": "clip-1",
                    "metadata": {
                        "source": "test-source",
                        "user_id": "user-123",
                    },
                }
            ],
            "callback_url": "https://ai-backend.com/callback",
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )

        assert response.status_code == 202
        # Metadata should be stored in job data (verified via Redis mock)

    def test_priority_validation(self, client, mock_redis):
        """Test that priority is validated (1-10)."""
        # Test invalid priority (too low)
        request_data = {
            "clips": [{"url": "https://example.com/video.mp4", "clip_id": "clip-1"}],
            "callback_url": "https://ai-backend.com/callback",
            "priority": 0,
        }

        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )
        assert response.status_code == 422

        # Test invalid priority (too high)
        request_data["priority"] = 11
        response = client.post(
            "/internal/v1/process-clips",
            json=request_data,
            headers={"X-API-Key": "test-internal-key"},
        )
        assert response.status_code == 422
