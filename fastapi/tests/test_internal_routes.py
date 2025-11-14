"""
Unit tests for internal API v1 routes
PR #004: Internal Service Contract & Callouts (FFmpeg Integration Skeleton)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import create_application


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    app = create_application()
    return TestClient(app)


class TestInternalRoutes:
    """Test cases for internal API routes"""

    def test_internal_v1_root(self, client):
        """Test internal API v1 root endpoint"""
        response = client.get("/internal/v1/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AI Video Generation Pipeline Internal API v1" in data["message"]
        assert data["status"] == "active"

    def test_audio_analysis_valid_request(self, client):
        """Test audio analysis endpoint with valid request"""
        request_data = {
            "job_id": "gen_abc123xyz",
            "audio": {"url": "s3://bucket/audio.mp3"},
            "options": {
                "analysis_types": ["beat", "sections", "energy"],
                "beat_resolution_seconds": 0.02
            }
        }

        response = client.post("/internal/v1/audio-analysis", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == "gen_abc123xyz"
        assert "beat_analysis" in data
        assert "bpm" in data["beat_analysis"]
        assert isinstance(data["beat_analysis"]["beats"], list)
        assert "sections" in data
        assert "energy_curve" in data

    def test_audio_analysis_minimal_request(self, client):
        """Test audio analysis endpoint with minimal request"""
        request_data = {
            "job_id": "gen_minimal123",
            "audio": {"url": "s3://bucket/audio.mp3"}
        }

        response = client.post("/internal/v1/audio-analysis", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == "gen_minimal123"

    def test_audio_analysis_invalid_request(self, client):
        """Test audio analysis endpoint with invalid request (missing job_id)"""
        request_data = {
            "audio": {"url": "s3://bucket/audio.mp3"}
        }

        response = client.post("/internal/v1/audio-analysis", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_process_clips_valid_request(self, client):
        """Test process clips endpoint with valid request"""
        request_data = {
            "job_id": "gen_abc123xyz",
            "clips": [
                {
                    "clip_id": "clip_001",
                    "source_url": "s3://bucket/clips/clip_001.mp4",
                    "duration": 6.0,
                    "metadata": {
                        "scene_number": 1,
                        "prompt": "Opening shot of luxury watch",
                        "style_vector": [0.8, 0.2, 0.5]
                    }
                }
            ],
            "instructions": {
                "target_duration": 30.0,
                "transitions": ["fade"],
                "audio_sync": True,
                "color_correction": True,
                "stabilization": False
            },
            "callback_url": "http://ai-backend:8001/internal/v1/processing-complete"
        }

        response = client.post("/internal/v1/process-clips", json=request_data)
        assert response.status_code == 202  # Accepted

        data = response.json()
        assert "processing_id" in data
        assert data["processing_id"].startswith("proc_gen_abc123xyz_")
        assert data["status"] == "accepted"
        assert "estimated_completion" in data
        assert isinstance(data["estimated_completion"], int)

    def test_process_clips_minimal_request(self, client):
        """Test process clips endpoint with minimal valid request"""
        request_data = {
            "job_id": "gen_minimal123",
            "clips": [],
            "instructions": {
                "target_duration": 30.0
            },
            "callback_url": "http://ai-backend:8001/internal/v1/processing-complete"
        }

        response = client.post("/internal/v1/process-clips", json=request_data)
        assert response.status_code == 202

        data = response.json()
        assert data["processing_id"].startswith("proc_gen_minimal123_")

    def test_process_clips_invalid_request(self, client):
        """Test process clips endpoint with invalid request (missing required fields)"""
        request_data = {
            "job_id": "gen_invalid123",
            "clips": []
            # Missing instructions and callback_url
        }

        response = client.post("/internal/v1/process-clips", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_processing_complete_success(self, client):
        """Test processing complete endpoint with successful completion"""
        request_data = {
            "job_id": "gen_abc123xyz",
            "processing_id": "proc_123",
            "status": "completed",
            "output": {
                "video_url": "s3://bucket/processed/gen_abc123xyz.mp4",
                "thumbnail_url": "s3://bucket/thumbnails/gen_abc123xyz.jpg",
                "metadata": {"duration": 30.0}
            }
        }

        response = client.post("/internal/v1/processing-complete", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["acknowledged"] is True
        assert data["job_id"] == "gen_abc123xyz"
        assert data["processing_id"] == "proc_123"

    def test_processing_complete_failure(self, client):
        """Test processing complete endpoint with failure status"""
        request_data = {
            "job_id": "gen_failed123",
            "processing_id": "proc_456",
            "status": "failed",
            "output": {
                "error": "FFmpeg processing failed",
                "error_code": "PROCESSING_ERROR"
            }
        }

        response = client.post("/internal/v1/processing-complete", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["acknowledged"] is True
        assert data["job_id"] == "gen_failed123"
        assert data["processing_id"] == "proc_456"

    def test_processing_complete_invalid_request(self, client):
        """Test processing complete endpoint with invalid request"""
        request_data = {
            "job_id": "gen_invalid123",
            "processing_id": "proc_789"
            # Missing status field
        }

        response = client.post("/internal/v1/processing-complete", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_schema_validation_audio_analysis(self, client):
        """Test that audio analysis response matches expected schema"""
        request_data = {
            "job_id": "gen_schema123",
            "audio": {"url": "s3://bucket/audio.mp3"},
            "options": {"analysis_types": ["beat"]}
        }

        response = client.post("/internal/v1/audio-analysis", json=request_data)
        assert response.status_code == 200

        data = response.json()
        # Validate response structure
        required_fields = ["job_id", "beat_analysis", "sections", "energy_curve"]
        for field in required_fields:
            assert field in data

        # Validate beat_analysis structure
        assert "bpm" in data["beat_analysis"]
        assert "beats" in data["beat_analysis"]
        assert isinstance(data["beat_analysis"]["beats"], list)

    def test_schema_validation_process_clips(self, client):
        """Test that process clips response matches expected schema"""
        request_data = {
            "job_id": "gen_schema123",
            "clips": [],
            "instructions": {"target_duration": 30.0},
            "callback_url": "http://ai-backend:8001/internal/v1/processing-complete"
        }

        response = client.post("/internal/v1/process-clips", json=request_data)
        assert response.status_code == 202

        data = response.json()
        # Validate response structure
        required_fields = ["processing_id", "status", "estimated_completion"]
        for field in required_fields:
            assert field in data

        assert data["status"] == "accepted"
        assert isinstance(data["estimated_completion"], int)
