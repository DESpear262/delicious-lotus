"""
Unit tests for v1 API jobs endpoints.

Tests GET /api/v1/jobs, GET /api/v1/jobs/{job_id}, and POST /api/v1/jobs/{job_id}/cancel.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    redis_mock = MagicMock()
    return redis_mock


@pytest.fixture
def client(mock_redis):
    """Create test client with mocked dependencies."""
    with patch("app.api.v1.jobs.get_redis_connection", return_value=mock_redis):
        app = create_app()
        yield TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "request_id": "req_test123",
        "job_id": "job_clip1_abc123",
        "clip_id": "clip1",
        "clip_url": "https://example.com/video.mp4",
        "callback_url": "https://example.com/callback",
        "operations": ["normalize"],
        "processing_options": {
            "target_resolution": "720p",
            "target_fps": 30,
            "video_codec": "libx264",
        },
        "metadata": {"source": "test"},
        "priority": 5,
        "queued_at": datetime.now(UTC).isoformat(),
        "status": "queued",
    }


class TestListJobsEndpoint:
    """Test cases for GET /api/v1/jobs endpoint."""

    def test_list_jobs_empty(self, client, mock_redis):
        """Test listing jobs when no jobs exist."""
        mock_redis.keys.return_value = []

        response = client.get("/api/v1/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["jobs"] == []
        assert data["total"] == 0
        assert data["offset"] == 0
        assert data["limit"] == 50

    def test_list_jobs_single(self, client, mock_redis, sample_job_data):
        """Test listing jobs with one job."""
        job_key = b"clip_job:job_clip1_abc123"
        mock_redis.keys.return_value = [job_key]
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")

        response = client.get("/api/v1/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["total"] == 1
        assert data["jobs"][0]["job_id"] == "job_clip1_abc123"
        assert data["jobs"][0]["clip_id"] == "clip1"
        assert data["jobs"][0]["status"] == "queued"

    def test_list_jobs_multiple(self, client, mock_redis, sample_job_data):
        """Test listing multiple jobs."""
        job_keys = [
            b"clip_job:job_clip1_abc123",
            b"clip_job:job_clip2_def456",
            b"clip_job:job_clip3_ghi789",
        ]
        mock_redis.keys.return_value = job_keys

        def get_side_effect(key):
            if b"clip1" in key:
                data = sample_job_data.copy()
                data["clip_id"] = "clip1"
                return str(data).encode("utf-8")
            elif b"clip2" in key:
                data = sample_job_data.copy()
                data["clip_id"] = "clip2"
                data["status"] = "processing"
                return str(data).encode("utf-8")
            elif b"clip3" in key:
                data = sample_job_data.copy()
                data["clip_id"] = "clip3"
                data["status"] = "completed"
                return str(data).encode("utf-8")
            return None

        mock_redis.get.side_effect = get_side_effect

        response = client.get("/api/v1/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 3
        assert data["total"] == 3

    def test_list_jobs_with_status_filter(self, client, mock_redis, sample_job_data):
        """Test listing jobs filtered by status."""
        job_keys = [
            b"clip_job:job_clip1_abc123",
            b"clip_job:job_clip2_def456",
        ]
        mock_redis.keys.return_value = job_keys

        def get_side_effect(key):
            if b"clip1" in key:
                data = sample_job_data.copy()
                data["status"] = "queued"
                return str(data).encode("utf-8")
            elif b"clip2" in key:
                data = sample_job_data.copy()
                data["status"] = "completed"
                return str(data).encode("utf-8")
            return None

        mock_redis.get.side_effect = get_side_effect

        response = client.get("/api/v1/jobs?status=queued")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["status"] == "queued"

    def test_list_jobs_with_request_id_filter(self, client, mock_redis, sample_job_data):
        """Test listing jobs filtered by request ID."""
        job_keys = [b"clip_job:job_clip1_abc123"]
        mock_redis.keys.return_value = job_keys
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")

        response = client.get("/api/v1/jobs?request_id=req_test123")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["request_id"] == "req_test123"

    def test_list_jobs_with_pagination(self, client, mock_redis, sample_job_data):
        """Test listing jobs with pagination."""
        # Create 5 job keys
        job_keys = [f"clip_job:job_clip{i}_test".encode() for i in range(5)]
        mock_redis.keys.return_value = job_keys

        def get_side_effect(key):
            data = sample_job_data.copy()
            return str(data).encode("utf-8")

        mock_redis.get.side_effect = get_side_effect

        # Test first page
        response = client.get("/api/v1/jobs?offset=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2
        assert data["total"] == 5
        assert data["offset"] == 0
        assert data["limit"] == 2

        # Test second page
        response = client.get("/api/v1/jobs?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2
        assert data["offset"] == 2

    def test_list_jobs_redis_error(self, client, mock_redis):
        """Test handling of Redis connection errors."""
        mock_redis.keys.side_effect = Exception("Redis connection failed")

        response = client.get("/api/v1/jobs")

        assert response.status_code == 503
        assert "Failed to retrieve jobs" in response.json()["detail"]


class TestGetJobEndpoint:
    """Test cases for GET /api/v1/jobs/{job_id} endpoint."""

    def test_get_job_success(self, client, mock_redis, sample_job_data):
        """Test successfully retrieving a job."""
        job_id = "job_clip1_abc123"
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")

        response = client.get(f"/api/v1/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["clip_id"] == "clip1"
        assert data["status"] == "queued"
        assert data["request_id"] == "req_test123"

    def test_get_job_not_found(self, client, mock_redis):
        """Test retrieving a non-existent job."""
        mock_redis.get.return_value = None

        response = client.get("/api/v1/jobs/nonexistent_job")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_redis_error(self, client, mock_redis):
        """Test handling of Redis errors when getting a job."""
        mock_redis.get.side_effect = Exception("Redis error")

        response = client.get("/api/v1/jobs/job_test")

        assert response.status_code == 503
        assert "Failed to retrieve job" in response.json()["detail"]


class TestCancelJobEndpoint:
    """Test cases for POST /api/v1/jobs/{job_id}/cancel endpoint."""

    def test_cancel_job_success(self, client, mock_redis, sample_job_data):
        """Test successfully cancelling a queued job."""
        job_id = "job_clip1_abc123"
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")
        mock_redis.setex.return_value = True

        response = client.post(f"/api/v1/jobs/{job_id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "cancelled"
        assert "cancelled" in data["message"].lower()
        assert "cancelled_at" in data

        # Verify Redis was updated
        mock_redis.setex.assert_called_once()

    def test_cancel_processing_job(self, client, mock_redis, sample_job_data):
        """Test cancelling a job that's currently processing."""
        job_id = "job_clip1_abc123"
        sample_job_data["status"] = "processing"
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")
        mock_redis.setex.return_value = True

        response = client.post(f"/api/v1/jobs/{job_id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_cancel_completed_job(self, client, mock_redis, sample_job_data):
        """Test attempting to cancel a completed job (should fail)."""
        job_id = "job_clip1_abc123"
        sample_job_data["status"] = "completed"
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")

        response = client.post(f"/api/v1/jobs/{job_id}/cancel")

        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]

    def test_cancel_failed_job(self, client, mock_redis, sample_job_data):
        """Test attempting to cancel a failed job (should fail)."""
        job_id = "job_clip1_abc123"
        sample_job_data["status"] = "failed"
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")

        response = client.post(f"/api/v1/jobs/{job_id}/cancel")

        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]

    def test_cancel_already_cancelled_job(self, client, mock_redis, sample_job_data):
        """Test attempting to cancel an already cancelled job (should fail)."""
        job_id = "job_clip1_abc123"
        sample_job_data["status"] = "cancelled"
        mock_redis.get.return_value = str(sample_job_data).encode("utf-8")

        response = client.post(f"/api/v1/jobs/{job_id}/cancel")

        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]

    def test_cancel_nonexistent_job(self, client, mock_redis):
        """Test attempting to cancel a non-existent job."""
        mock_redis.get.return_value = None

        response = client.post("/api/v1/jobs/nonexistent_job/cancel")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_cancel_job_redis_error(self, client, mock_redis):
        """Test handling of Redis errors when cancelling a job."""
        mock_redis.get.side_effect = Exception("Redis error")

        response = client.post("/api/v1/jobs/job_test/cancel")

        assert response.status_code == 503
        assert "Failed to cancel job" in response.json()["detail"]
