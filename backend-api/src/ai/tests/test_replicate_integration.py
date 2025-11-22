"""
Integration tests for Replicate Model Client - PR 302
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from freezegun import freeze_time

from core.replicate_client import ReplicateModelClient
from models.replicate_client import (
    ClientConfig,
    GenerateClipRequest,
    GenerationStatus,
    VideoResolution
)


class TestReplicateModelClientIntegration:
    """Integration tests for the complete Replicate client workflow"""

    @pytest.fixture
    def mock_replicate_client(self):
        """Create a mock Replicate client for testing"""
        mock_client = MagicMock()

        # Mock successful prediction creation
        mock_prediction = MagicMock()
        mock_prediction.id = "pred_integration_123"
        mock_client.predictions.create.return_value = mock_prediction

        # Mock successful prediction retrieval
        mock_client.predictions.get.return_value = MagicMock(
            status="succeeded",
            output={
                "video": "https://replicate.com/videos/integration_test.mp4",
                "duration": 5.0,
                "width": 1280,
                "height": 720,
                "quality_score": 0.85
            },
            error=None,
            logs="Generation completed successfully",
            created_at="2024-01-01T12:00:00Z",
            completed_at="2024-01-01T12:00:45Z",
            version="google/veo-3.1-fast"
        )

        return mock_client

    @pytest.fixture
    def client_config(self):
        """Create test client configuration"""
        return ClientConfig(
            api_token="integration_test_token",
            default_model="google/veo-3.1-fast"
        )

    @pytest.fixture
    def replicate_client(self, client_config, mock_replicate_client):
        """Create ReplicateModelClient with mocked dependencies"""
        client = ReplicateModelClient(client_config)
        client.client = mock_replicate_client
        return client

    @pytest.mark.asyncio
    async def test_full_generation_workflow(self, replicate_client, mock_replicate_client):
        """Test complete video generation workflow"""
        request = GenerateClipRequest(
            clip_id="integration_clip_001",
            generation_id="integration_gen_001",
            scene_id="integration_scene_001",
            prompt="A cinematic shot of a rocket launching into space",
            duration_seconds=5.0,
            aspect_ratio="16:9",
            resolution=VideoResolution.RES_720P,
            seed=12345,
            guidance_scale=7.5
        )

        # Step 1: Start generation
        with freeze_time("2024-01-01 12:00:00"):
            response = await replicate_client.generate_clip(request)

        assert response.clip_id == "integration_clip_001"
        assert response.prediction_id == "pred_integration_123"
        assert response.status == GenerationStatus.QUEUED

        # Verify prediction was created with correct parameters
        create_call = mock_replicate_client.predictions.create.call_args
        assert create_call[1]["version"] == "google/veo-3.1-fast"

        inputs = create_call[1]["input"]
        assert inputs["prompt"] == "A cinematic shot of a rocket launching into space"
        assert inputs["duration"] == 5.0
        assert inputs["aspect_ratio"] == "16:9"
        assert inputs["width"] == 1280
        assert inputs["height"] == 720
        assert inputs["seed"] == 12345
        assert inputs["guidance_scale"] == 7.5

        # Step 2: Wait for completion
        result = await replicate_client.wait_for_completion("pred_integration_123", timeout_seconds=10.0)

        # Verify result structure
        assert result.clip_metadata.clip_id == "clip_pred_integration_123"  # Auto-generated
        assert result.clip_metadata.video_url == "https://replicate.com/videos/integration_test.mp4"
        assert result.clip_metadata.duration_seconds == 5.0
        assert result.clip_metadata.resolution == VideoResolution.RES_720P
        assert result.clip_metadata.generation_time_seconds == 45.0
        assert result.clip_metadata.quality_score == 0.85
        assert result.clip_metadata.is_successful() is True

        # Verify prediction details are included
        assert "status" in result.prediction_details
        assert result.prediction_details["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_generation_with_negative_prompt(self, replicate_client, mock_replicate_client):
        """Test generation with negative prompt"""
        request = GenerateClipRequest(
            clip_id="neg_prompt_clip",
            generation_id="neg_prompt_gen",
            scene_id="neg_prompt_scene",
            prompt="A beautiful forest scene",
            negative_prompt="blurry, dark, scary, horror",
            duration_seconds=3.0
        )

        await replicate_client.generate_clip(request)

        # Verify negative prompt was included
        create_call = mock_replicate_client.predictions.create.call_args
        inputs = create_call[1]["input"]
        assert inputs["negative_prompt"] == "blurry, dark, scary, horror"

    @pytest.mark.asyncio
    async def test_different_resolutions(self, replicate_client, mock_replicate_client):
        """Test generation with different resolutions"""
        test_cases = [
            (VideoResolution.RES_480P, 854, 480),
            (VideoResolution.RES_720P, 1280, 720),
            (VideoResolution.RES_1080P, 1920, 1080),
            (VideoResolution.RES_4K, 3840, 2160),
        ]

        for resolution, expected_width, expected_height in test_cases:
            request = GenerateClipRequest(
                clip_id=f"res_test_{resolution.value}",
                generation_id="res_test_gen",
                scene_id="res_test_scene",
                prompt="Test prompt",
                duration_seconds=4.0,
                resolution=resolution
            )

            await replicate_client.generate_clip(request)

            create_call = mock_replicate_client.predictions.create.call_args
            inputs = create_call[1]["input"]
            assert inputs["width"] == expected_width
            assert inputs["height"] == expected_height

    @pytest.mark.asyncio
    async def test_webhook_integration(self, replicate_client, mock_replicate_client):
        """Test generation with webhook URL"""
        webhook_url = "https://api.example.com/webhooks/replicate"

        request = GenerateClipRequest(
            clip_id="webhook_clip",
            generation_id="webhook_gen",
            scene_id="webhook_scene",
            prompt="Test with webhook",
            duration_seconds=4.0,
            webhook_url=webhook_url
        )

        await replicate_client.generate_clip(request)

        # Verify webhook URL was passed to Replicate
        create_call = mock_replicate_client.predictions.create.call_args
        assert create_call[1]["webhook"] == webhook_url

    @pytest.mark.asyncio
    async def test_status_checking_workflow(self, replicate_client, mock_replicate_client):
        """Test the status checking workflow"""
        prediction_id = "status_test_pred"

        # Mock different status responses
        status_responses = [
            {"status": "starting", "output": None},
            {"status": "processing", "output": None},
            {
                "status": "succeeded",
                "output": {"video": "https://example.com/completed.mp4", "duration": 4.0},
                "created_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:00:30Z"
            }
        ]

        mock_replicate_client.predictions.get.side_effect = [
            MagicMock(**resp) for resp in status_responses
        ]

        # Get status updates
        status1 = await replicate_client.get_generation_status(prediction_id)
        assert status1["status"] == "starting"

        status2 = await replicate_client.get_generation_status(prediction_id)
        assert status2["status"] == "processing"

        status3 = await replicate_client.get_generation_status(prediction_id)
        assert status3["status"] == "succeeded"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, replicate_client, mock_replicate_client):
        """Test error handling in integration scenarios"""
        # Test API error during generation start
        mock_replicate_client.predictions.create.side_effect = Exception("API rate limited")

        request = GenerateClipRequest(
            clip_id="error_clip",
            generation_id="error_gen",
            scene_id="error_scene",
            prompt="Test prompt",
            duration_seconds=3.0
        )

        # Should retry and eventually fail
        with pytest.raises(Exception, match="Video generation failed"):
            await replicate_client.generate_clip(request)

    @pytest.mark.asyncio
    async def test_cancellation_workflow(self, replicate_client, mock_replicate_client):
        """Test generation cancellation workflow"""
        prediction_id = "cancel_test_pred"

        # Mock successful cancellation
        mock_replicate_client.predictions.cancel.return_value = None

        result = await replicate_client.cancel_generation(prediction_id)
        assert result is True

        # Verify cancel was called
        mock_replicate_client.predictions.cancel.assert_called_once_with(prediction_id)

    @pytest.mark.asyncio
    async def test_timeout_scenario(self, replicate_client, mock_replicate_client):
        """Test timeout handling during long generations"""
        prediction_id = "timeout_test_pred"

        # Always return processing status
        mock_replicate_client.predictions.get.return_value = MagicMock(
            status="processing",
            output=None
        )

        with pytest.raises(TimeoutError):
            await replicate_client.wait_for_completion(prediction_id, timeout_seconds=0.1)

    @pytest.mark.asyncio
    async def test_different_generation_durations(self, replicate_client, mock_replicate_client):
        """Test generation with different video durations"""
        durations = [2.0, 5.0, 8.0, 10.0]

        for duration in durations:
            request = GenerateClipRequest(
                clip_id=f"duration_test_{duration}",
                generation_id="duration_gen",
                scene_id="duration_scene",
                prompt="Test prompt",
                duration_seconds=duration
            )

            await replicate_client.generate_clip(request)

            create_call = mock_replicate_client.predictions.create.call_args
            inputs = create_call[1]["input"]
            assert inputs["duration"] == duration

    @pytest.mark.asyncio
    async def test_model_version_tracking(self, replicate_client, mock_replicate_client):
        """Test that model version is properly tracked"""
        request = GenerateClipRequest(
            clip_id="version_clip",
            generation_id="version_gen",
            scene_id="version_scene",
            prompt="Test prompt",
            duration_seconds=4.0,
            model="google/veo-3.1-fast"
        )

        await replicate_client.generate_clip(request)

        # Verify model version was passed
        create_call = mock_replicate_client.predictions.create.call_args
        assert create_call[1]["version"] == "google/veo-3.1-fast"

        # Test completion with version info
        result = await replicate_client.wait_for_completion("pred_integration_123")
        assert result.clip_metadata.model_used == "google/veo-3.1-fast"
