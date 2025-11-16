"""
Unit tests for API v1 routes
Block 0: API Skeleton & Core Infrastructure
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import create_application
from app.models.schemas import GenerationStatus


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    app = create_application()
    return TestClient(app)


class TestV1Routes:
    """Test cases for v1 API routes"""

    def test_api_v1_root(self, client):
        """Test API v1 root endpoint"""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AI Video Generation Pipeline API v1" in data["message"]
        assert data["status"] == "active"

    def test_create_generation_valid_request(self, client):
        """Test creating a generation with valid request"""
        request_data = {
            "prompt": "Create a 30-second ad for a luxury watch brand called ChronoLux with elegant gold and black colors",
            "parameters": {
                "duration_seconds": 30,
                "aspect_ratio": "16:9",
                "style": "professional",
                "brand": {
                    "name": "ChronoLux",
                    "colors": ["#1a1a1a", "#d4af37"]
                },
                "include_cta": True,
                "cta_text": "Shop Now",
                "music_style": "corporate"
            },
            "options": {
                "quality": "high",
                "fast_generation": False
            }
        }

        response = client.post("/api/v1/generations", json=request_data)
        assert response.status_code == 201

        data = response.json()
        assert "generation_id" in data
        assert data["generation_id"].startswith("gen_")
        assert data["status"] == "queued"
        assert "created_at" in data
        assert "estimated_completion" in data
        assert "websocket_url" in data
        assert data["websocket_url"] == f"/ws/generations/{data['generation_id']}"

    def test_create_generation_invalid_duration(self, client):
        """Test creating a generation with invalid duration"""
        request_data = {
            "prompt": "Create a 30-second ad for a luxury watch brand called ChronoLux",
            "parameters": {
                "duration_seconds": 25,  # Invalid duration
                "aspect_ratio": "16:9",
                "style": "professional",
                "include_cta": True,
                "cta_text": "Shop Now",
                "music_style": "corporate"
            }
        }

        response = client.post("/api/v1/generations", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_create_generation_short_prompt(self, client):
        """Test creating a generation with too short prompt"""
        request_data = {
            "prompt": "Short",  # Too short
            "parameters": {
                "duration_seconds": 30,
                "aspect_ratio": "16:9",
                "style": "professional",
                "include_cta": True,
                "cta_text": "Shop Now",
                "music_style": "corporate"
            }
        }

        response = client.post("/api/v1/generations", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_get_generation_existing(self, client):
        """Test getting an existing generation"""
        # First create a generation
        create_data = {
            "prompt": "Create a 30-second ad for a luxury watch brand called ChronoLux",
            "parameters": {
                "duration_seconds": 30,
                "aspect_ratio": "16:9",
                "style": "professional",
                "include_cta": True,
                "cta_text": "Shop Now",
                "music_style": "corporate"
            }
        }

        create_response = client.post("/api/v1/generations", json=create_data)
        assert create_response.status_code == 201
        generation_id = create_response.json()["generation_id"]

        # Now get the generation
        response = client.get(f"/api/v1/generations/{generation_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["generation_id"] == generation_id
        assert data["status"] == "queued"
        assert "metadata" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["metadata"]["prompt"] == create_data["prompt"]

    def test_get_generation_not_found(self, client):
        """Test getting a non-existent generation"""
        response = client.get("/api/v1/generations/gen_nonexistent123")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "NOT_FOUND" in data["error"]["code"]

    def test_create_generation_minimal_request(self, client):
        """Test creating a generation with minimal required fields"""
        request_data = {
            "prompt": "Create a 30-second ad for a luxury watch brand called ChronoLux with elegant gold and black colors",
            "parameters": {
                "duration_seconds": 30
            }
        }

        response = client.post("/api/v1/generations", json=request_data)
        assert response.status_code == 201

        data = response.json()
        assert "generation_id" in data
        assert data["status"] == "queued"
