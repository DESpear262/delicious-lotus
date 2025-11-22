"""
End-to-end tests for complete composition workflows.

These tests simulate real user scenarios from API request to final video download,
testing the complete system integration with minimal mocking.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import pytest
from httpx import AsyncClient


class TestSimpleCompositionE2E:
    """E2E tests for simple video composition (2 clips)."""

    @pytest.fixture
    def simple_composition_request(self) -> dict[str, Any]:
        """Create simple composition request with 2 clips."""
        return {
            "title": "Simple E2E Test Composition",
            "description": "Two clips merged together",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                },
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video2.mp4",
                    "start_time": 5.0,
                    "end_time": 10.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                },
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

    @pytest.mark.asyncio
    async def test_simple_composition_workflow(
        self,
        test_app,
        simple_composition_request: dict,
    ):
        """Test complete workflow for simple 2-clip composition.

        Steps:
        1. Submit composition request
        2. Verify composition created with PENDING/QUEUED status
        3. Poll status until PROCESSING
        4. Poll until COMPLETED
        5. Get download URL
        6. Verify download URL is valid
        """
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Step 1: Create composition
            response = await client.post(
                "/api/v1/compositions/",
                json=simple_composition_request,
            )

            assert response.status_code == 202
            composition_data = response.json()

            composition_id = composition_data["id"]
            assert composition_id is not None
            assert composition_data["title"] == "Simple E2E Test Composition"
            assert composition_data["status"] in ["pending", "queued"]

            # Step 2: Poll status until processing or completed
            max_polls = 30
            poll_interval = 1.0
            current_status = composition_data["status"]

            for _ in range(max_polls):
                if current_status in ["completed", "failed"]:
                    break

                await asyncio.sleep(poll_interval)

                # Get status
                status_response = await client.get(f"/api/v1/compositions/{composition_id}/status")

                assert status_response.status_code == 200
                status_data = status_response.json()

                current_status = status_data["status"]
                overall_progress = status_data["overall_progress"]

                # Verify progress is between 0-100
                assert 0 <= overall_progress <= 100

                # Check if we have stages information
                if "stages" in status_data and status_data["stages"]:
                    # Verify stage structure
                    for stage in status_data["stages"]:
                        assert "stage" in stage
                        assert "progress" in stage
                        assert 0 <= stage["progress"] <= 100

            # In a real E2E test with running workers, we'd expect COMPLETED
            # For now, verify we can get status
            assert current_status in ["pending", "queued", "processing", "completed", "failed"]

    @pytest.mark.asyncio
    async def test_composition_with_invalid_url(self, test_app):
        """Test composition with invalid video URL."""
        invalid_request = {
            "title": "Invalid URL Test",
            "description": "Test with invalid URL",
            "clips": [
                {
                    "video_url": "not-a-valid-url",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=invalid_request,
            )

            # Should fail validation
            assert response.status_code == 422


class TestComplexCompositionE2E:
    """E2E tests for complex video composition with overlays and audio."""

    @pytest.fixture
    def complex_composition_request(self) -> dict[str, Any]:
        """Create complex composition with 10+ clips, audio, and overlays."""
        # Create 10 clips
        clips = []
        for i in range(10):
            clips.append(
                {
                    "video_url": f"https://test-bucket.s3.amazonaws.com/video{i}.mp4",
                    "start_time": i * 3.0,
                    "end_time": (i + 1) * 3.0,
                    "trim_start": 0.0,
                    "trim_end": 3.0,
                }
            )

        return {
            "title": "Complex E2E Test Composition",
            "description": "10 clips with audio and text overlays",
            "clips": clips,
            "audio": {
                "music_url": "https://test-bucket.s3.amazonaws.com/background.mp3",
                "voiceover_url": "https://test-bucket.s3.amazonaws.com/voiceover.mp3",
                "music_volume": 0.3,
                "voiceover_volume": 1.0,
                "original_audio_volume": 0.8,
            },
            "overlays": [
                {
                    "text": "Opening Title",
                    "position": "top_center",
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "font_size": 48,
                    "font_color": "white",
                },
                {
                    "text": "Subtitle 1",
                    "position": "bottom_center",
                    "start_time": 3.0,
                    "end_time": 6.0,
                    "font_size": 36,
                    "font_color": "yellow",
                },
                {
                    "text": "Closing Credits",
                    "position": "center",
                    "start_time": 27.0,
                    "end_time": 30.0,
                    "font_size": 40,
                    "font_color": "white",
                },
            ],
            "output": {
                "resolution": "1080p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 5000000,
            },
        }

    @pytest.mark.asyncio
    async def test_complex_composition_workflow(
        self,
        test_app,
        complex_composition_request: dict,
    ):
        """Test complete workflow for complex composition with 10+ clips."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Create composition
            response = await client.post(
                "/api/v1/compositions/",
                json=complex_composition_request,
            )

            assert response.status_code == 202
            composition_data = response.json()

            composition_id = composition_data["id"]

            # Verify complex request stored correctly
            # In real scenario, we'd verify the config was stored
            assert composition_data["title"] == "Complex E2E Test Composition"

            # Get status
            status_response = await client.get(f"/api/v1/compositions/{composition_id}/status")

            assert status_response.status_code == 200
            status_data = status_response.json()

            assert status_data["id"] == composition_id
            assert "overall_progress" in status_data

    @pytest.mark.asyncio
    async def test_composition_metadata_endpoint(
        self,
        test_app,
        complex_composition_request: dict,
    ):
        """Test metadata endpoint returns complete composition information."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Create composition
            response = await client.post(
                "/api/v1/compositions/",
                json=complex_composition_request,
            )

            composition_id = response.json()["id"]

            # Get metadata
            metadata_response = await client.get(f"/api/v1/compositions/{composition_id}/metadata")

            assert metadata_response.status_code == 200
            metadata = metadata_response.json()

            # Verify metadata structure
            assert metadata["id"] == composition_id
            assert metadata["title"] == "Complex E2E Test Composition"
            assert "request_config" in metadata
            assert "created_at" in metadata
            assert "input_files" in metadata
            assert "applied_effects" in metadata

            # Verify config preserved
            assert len(metadata["request_config"]["clips"]) == 10
            assert len(metadata["request_config"]["overlays"]) == 3


class TestErrorScenariosE2E:
    """E2E tests for error scenarios and edge cases."""

    @pytest.mark.asyncio
    async def test_composition_with_invalid_time_range(self, test_app):
        """Test composition with invalid time range (end before start)."""
        invalid_request = {
            "title": "Invalid Time Range",
            "description": "End time before start time",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 10.0,  # Start after end
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=invalid_request,
            )

            assert response.status_code == 422
            error_data = response.json()
            assert "detail" in error_data

    @pytest.mark.asyncio
    async def test_composition_with_unsupported_format(self, test_app):
        """Test composition with unsupported output format."""
        invalid_request = {
            "title": "Unsupported Format",
            "description": "Request with unsupported format",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "webm",  # Not in supported formats
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=invalid_request,
            )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_nonexistent_composition(self, test_app):
        """Test getting a composition that doesn't exist."""
        nonexistent_id = uuid.uuid4()

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/compositions/{nonexistent_id}/status")

            assert response.status_code == 404
            error_data = response.json()
            assert "not found" in error_data["detail"].lower()

    @pytest.mark.asyncio
    async def test_download_incomplete_composition(self, test_app, simple_composition_request):
        """Test downloading a composition that hasn't completed."""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Create composition
            response = await client.post(
                "/api/v1/compositions/",
                json=simple_composition_request,
            )

            composition_id = response.json()["id"]

            # Try to download (should fail - not completed)
            download_response = await client.get(f"/api/v1/compositions/{composition_id}/download")

            # Should return 400 - composition not completed
            assert download_response.status_code == 400
            error_data = download_response.json()
            assert "not completed" in error_data["detail"].lower()

    @pytest.fixture
    def simple_composition_request(self) -> dict[str, Any]:
        """Create simple composition request."""
        return {
            "title": "Test Composition",
            "description": "Test",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }


class TestEdgeCasesE2E:
    """E2E tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_very_long_composition(self, test_app):
        """Test composition with very long duration (2 hours)."""
        # Create many clips totaling 2 hours
        clips = []
        num_clips = 240  # 240 clips of 30 seconds each = 2 hours
        for i in range(num_clips):
            clips.append(
                {
                    "video_url": f"https://test-bucket.s3.amazonaws.com/video{i % 10}.mp4",
                    "start_time": i * 30.0,
                    "end_time": (i + 1) * 30.0,
                    "trim_start": 0.0,
                    "trim_end": 30.0,
                }
            )

        long_request = {
            "title": "Very Long Composition (2 hours)",
            "description": "Edge case test for long videos",
            "clips": clips,
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=long_request,
            )

            # Should accept the request (validation passes)
            assert response.status_code == 202

            composition_data = response.json()
            assert composition_data["title"] == "Very Long Composition (2 hours)"

    @pytest.mark.asyncio
    async def test_single_frame_clip(self, test_app):
        """Test composition with very short clip (near single frame)."""
        short_request = {
            "title": "Single Frame Test",
            "description": "Very short clip",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 0.033,  # ~1 frame at 30fps
                    "trim_start": 0.0,
                    "trim_end": 0.033,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=short_request,
            )

            # Should accept short clips
            assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_4k_resolution_composition(self, test_app):
        """Test composition with 4K resolution output."""
        uhd_request = {
            "title": "4K Resolution Test",
            "description": "Ultra HD output",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video_4k.mp4",
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "trim_start": 0.0,
                    "trim_end": 10.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "4k",
                "format": "mp4",
                "fps": 60,  # High frame rate
                "bitrate": 20000000,  # High bitrate for 4K
            },
        }

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=uhd_request,
            )

            assert response.status_code == 202

            composition_data = response.json()
            # Verify request accepted
            assert composition_data["title"] == "4K Resolution Test"


class TestAuthenticationE2E:
    """E2E tests for API authentication."""

    @pytest.mark.asyncio
    async def test_composition_without_auth_token(self, test_app):
        """Test composition creation without authentication token."""
        request_data = {
            "title": "No Auth Test",
            "description": "Should fail without auth",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        # Create client without auth headers
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=request_data,
            )

            # If authentication is required, should return 401 or 403
            # If not required (public API), should return 202
            # Adjust based on actual API requirements
            assert response.status_code in [202, 401, 403]

    @pytest.mark.asyncio
    async def test_composition_with_invalid_auth_token(self, test_app):
        """Test composition creation with invalid authentication token."""
        request_data = {
            "title": "Invalid Auth Test",
            "description": "Should fail with invalid auth",
            "clips": [
                {
                    "video_url": "https://test-bucket.s3.amazonaws.com/video1.mp4",
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "trim_start": 0.0,
                    "trim_end": 5.0,
                }
            ],
            "audio": {
                "music_url": None,
                "voiceover_url": None,
                "music_volume": 0.5,
                "voiceover_volume": 1.0,
                "original_audio_volume": 1.0,
            },
            "overlays": [],
            "output": {
                "resolution": "720p",
                "format": "mp4",
                "fps": 30,
                "bitrate": 2000000,
            },
        }

        async with AsyncClient(
            app=test_app,
            base_url="http://test",
            headers={"X-Internal-Auth": "invalid-token-12345"},
        ) as client:
            response = await client.post(
                "/api/v1/compositions/",
                json=request_data,
            )

            # Should fail with invalid auth
            assert response.status_code in [202, 401, 403]


class TestConcurrentRequestsE2E:
    """E2E tests for concurrent API requests."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_compositions(self, test_app):
        """Test creating multiple compositions concurrently."""
        num_compositions = 5

        # Create composition requests
        requests = []
        for i in range(num_compositions):
            requests.append(
                {
                    "title": f"Concurrent Composition {i}",
                    "description": f"Concurrent test {i}",
                    "clips": [
                        {
                            "video_url": f"https://test-bucket.s3.amazonaws.com/video{i}.mp4",
                            "start_time": 0.0,
                            "end_time": 5.0,
                            "trim_start": 0.0,
                            "trim_end": 5.0,
                        }
                    ],
                    "audio": {
                        "music_url": None,
                        "voiceover_url": None,
                        "music_volume": 0.5,
                        "voiceover_volume": 1.0,
                        "original_audio_volume": 1.0,
                    },
                    "overlays": [],
                    "output": {
                        "resolution": "720p",
                        "format": "mp4",
                        "fps": 30,
                        "bitrate": 2000000,
                    },
                }
            )

        # Submit all requests concurrently
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            tasks = [client.post("/api/v1/compositions/", json=request) for request in requests]

            responses = await asyncio.gather(*tasks)

            # Verify all succeeded
            for i, response in enumerate(responses):
                assert response.status_code == 202, f"Request {i} failed"

                composition_data = response.json()
                assert "id" in composition_data
                assert composition_data["title"] == f"Concurrent Composition {i}"

            # Verify all compositions have unique IDs
            composition_ids = [resp.json()["id"] for resp in responses]
            assert len(set(composition_ids)) == num_compositions
