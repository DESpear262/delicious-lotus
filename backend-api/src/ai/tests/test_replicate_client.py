"""
Unit tests for Replicate Model Client - PR 302
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from freezegun import freeze_time

from core.replicate_client import ReplicateModelClient
from models.replicate_client import (
    ClientConfig,
    GenerateClipRequest,
    GenerateClipResponse,
    GenerationResult,
    ClipMetadata,
    GenerationStatus,
    VideoResolution,
    VideoFormat
)


@pytest.fixture
def client_config():
    """Create test client configuration"""
    return ClientConfig(
        api_token="test_token",
        default_model="google/veo-3.1-fast",
        max_retries=2,
        request_timeout=30.0,
        generation_timeout=60.0
    )


@pytest.fixture
def replicate_client(client_config):
    """Create ReplicateModelClient instance"""
    return ReplicateModelClient(client_config)


@pytest.fixture
def sample_request():
    """Create sample generation request"""
    return GenerateClipRequest(
        clip_id="clip_123",
        generation_id="gen_456",
        scene_id="scene_789",
        prompt="A beautiful sunset over mountains",
        duration_seconds=5.0,
        aspect_ratio="16:9",
        resolution=VideoResolution.RES_720P
    )


class TestReplicateModelClient:
    """Test cases for ReplicateModelClient"""

    def test_initialization(self, replicate_client, client_config):
        """Test client initializes correctly"""
        assert replicate_client.config == client_config
        assert replicate_client.client is not None

    def test_prepare_model_inputs_basic(self, replicate_client, sample_request):
        """Test basic model input preparation"""
        inputs = replicate_client._prepare_model_inputs(sample_request)

        expected = {
            "prompt": "A beautiful sunset over mountains",
            "duration": 5.0,
            "aspect_ratio": "16:9",
            "width": 1280,
            "height": 720
        }

        assert inputs == expected

    def test_prepare_model_inputs_with_optional(self, replicate_client):
        """Test model input preparation with optional parameters"""
        request = GenerateClipRequest(
            clip_id="clip_123",
            generation_id="gen_456",
            scene_id="scene_789",
            prompt="Test prompt",
            negative_prompt="blurry, low quality",
            duration_seconds=3.0,
            seed=42,
            guidance_scale=7.5,
            num_inference_steps=25
        )

        inputs = replicate_client._prepare_model_inputs(request)

        assert inputs["negative_prompt"] == "blurry, low quality"
        assert inputs["seed"] == 42
        assert inputs["guidance_scale"] == 7.5
        assert inputs["num_inference_steps"] == 25

    @pytest.mark.parametrize("resolution,width,height", [
        (VideoResolution.RES_480P, 854, 480),
        (VideoResolution.RES_720P, 1280, 720),
        (VideoResolution.RES_1080P, 1920, 1080),
        (VideoResolution.RES_4K, 3840, 2160),
    ])
    def test_prepare_model_inputs_resolution(self, replicate_client, sample_request, resolution, width, height):
        """Test resolution-specific input parameters"""
        sample_request.resolution = resolution
        inputs = replicate_client._prepare_model_inputs(sample_request)

        assert inputs["width"] == width
        assert inputs["height"] == height

    def test_estimate_generation_time(self, replicate_client, sample_request):
        """Test generation time estimation"""
        # 5 second video at 720p should be around base time
        estimated = replicate_client._estimate_generation_time(sample_request)
        assert estimated > 40  # Base time is 45 seconds
        assert estimated < 60

    def test_estimate_generation_time_longer_video(self, replicate_client, sample_request):
        """Test estimation for longer videos"""
        sample_request.duration_seconds = 10.0
        estimated = replicate_client._estimate_generation_time(sample_request)

        # Should be roughly double the 5-second estimate
        short_estimate = replicate_client._estimate_generation_time(
            GenerateClipRequest(**{**sample_request.dict(), "duration_seconds": 5.0})
        )
        assert estimated > short_estimate

    def test_estimate_generation_time_higher_resolution(self, replicate_client, sample_request):
        """Test estimation for higher resolutions"""
        sample_request.resolution = VideoResolution.RES_1080P
        estimated_1080p = replicate_client._estimate_generation_time(sample_request)

        sample_request.resolution = VideoResolution.RES_720P
        estimated_720p = replicate_client._estimate_generation_time(sample_request)

        assert estimated_1080p > estimated_720p

    @pytest.mark.asyncio
    @patch('asyncio.get_event_loop')
    async def test_generate_clip_success(self, mock_get_event_loop, replicate_client, sample_request):
        """Test successful clip generation"""
        # Mock the event loop and Replicate client
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop

        # Mock Replicate prediction
        mock_prediction = MagicMock()
        mock_prediction.id = "pred_12345"

        # Mock the client.predictions.create call
        mock_client = MagicMock()
        mock_client.predictions.create.return_value = mock_prediction
        replicate_client.client = mock_client

        # Mock the executor call
        mock_loop.run_in_executor.return_value = mock_prediction

        with freeze_time("2024-01-01 12:00:00"):
            response = await replicate_client.generate_clip(sample_request)

        assert response.clip_id == "clip_123"
        assert response.prediction_id == "pred_12345"
        assert response.status == GenerationStatus.QUEUED
        assert response.status_url == "https://replicate.com/p/pred_12345"
        assert response.started_at.year == 2024

        # Verify the prediction was created with correct parameters
        mock_client.predictions.create.assert_called_once()
        call_args = mock_client.predictions.create.call_args
        assert call_args[1]["version"] == "google/veo-3.1-fast"
        assert call_args[1]["input"]["prompt"] == "A beautiful sunset over mountains"

    @pytest.mark.asyncio
    async def test_get_generation_status(self, replicate_client):
        """Test getting generation status"""
        mock_prediction = MagicMock()
        mock_prediction.status = "processing"
        mock_prediction.output = None
        mock_prediction.error = None
        mock_prediction.logs = "Processing..."
        mock_prediction.created_at = "2024-01-01T12:00:00Z"
        mock_prediction.completed_at = None

        with patch('asyncio.get_event_loop') as mock_get_event_loop:
            mock_loop = MagicMock()
            mock_loop.run_in_executor.return_value = mock_prediction
            mock_get_event_loop.return_value = mock_loop

            status = await replicate_client.get_generation_status("pred_123")

            assert status["status"] == "processing"
            assert status["logs"] == "Processing..."
            assert status["created_at"] == "2024-01-01T12:00:00Z"

    def test_parse_resolution_from_output(self, replicate_client):
        """Test resolution parsing from Replicate output"""
        test_cases = [
            ({"width": 854, "height": 480}, VideoResolution.RES_480P),
            ({"width": 1280, "height": 720}, VideoResolution.RES_720P),
            ({"width": 1920, "height": 1080}, VideoResolution.RES_1080P),
            ({"width": 3840, "height": 2160}, VideoResolution.RES_4K),
            ({}, VideoResolution.RES_480P),  # Default case
        ]

        for output, expected in test_cases:
            result = replicate_client._parse_resolution_from_output(output)
            assert result == expected

    def test_calculate_generation_time(self, replicate_client):
        """Test generation time calculation"""
        status_info = {
            "created_at": "2024-01-01T12:00:00Z",
            "completed_at": "2024-01-01T12:01:30Z"
        }

        time_taken = replicate_client._calculate_generation_time(status_info)
        assert time_taken == 90.0  # 1.5 minutes

    def test_calculate_generation_time_fallback(self, replicate_client):
        """Test generation time calculation fallback"""
        status_info = {}  # Missing timestamps

        time_taken = replicate_client._calculate_generation_time(status_info)
        assert time_taken == 60.0  # Default fallback

    @pytest.mark.asyncio
    async def test_wait_for_completion_success(self, replicate_client):
        """Test waiting for successful completion"""
        prediction_id = "pred_123"

        # Mock successful status
        mock_status = {
            "status": "succeeded",
            "output": {
                "video": "https://example.com/video.mp4",
                "duration": 5.0,
                "width": 1280,
                "height": 720
            },
            "version": "google/veo-3.1-fast",
            "created_at": "2024-01-01T12:00:00Z",
            "completed_at": "2024-01-01T12:01:00Z"
        }

        with patch.object(replicate_client, 'get_generation_status', return_value=mock_status):
            result = await replicate_client.wait_for_completion(prediction_id, timeout_seconds=10.0)

            assert isinstance(result, GenerationResult)
            assert result.clip_metadata.video_url == "https://example.com/video.mp4"
            assert result.clip_metadata.duration_seconds == 5.0
            assert result.clip_metadata.generation_time_seconds == 60.0

    @pytest.mark.asyncio
    async def test_wait_for_completion_failure(self, replicate_client):
        """Test waiting for failed completion"""
        prediction_id = "pred_123"

        mock_status = {
            "status": "failed",
            "error": "Content policy violation"
        }

        with patch.object(replicate_client, 'get_generation_status', return_value=mock_status):
            with pytest.raises(Exception, match="Generation failed: Content policy violation"):
                await replicate_client.wait_for_completion(prediction_id)

    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self, replicate_client):
        """Test timeout during completion wait"""
        prediction_id = "pred_123"

        # Always return processing status
        mock_status = {"status": "processing"}

        with patch.object(replicate_client, 'get_generation_status', return_value=mock_status):
            with pytest.raises(TimeoutError, match="Generation timed out"):
                await replicate_client.wait_for_completion(prediction_id, timeout_seconds=0.1)

    @pytest.mark.asyncio
    async def test_cancel_generation(self, replicate_client):
        """Test generation cancellation"""
        with patch('asyncio.get_event_loop') as mock_get_event_loop:
            mock_loop = MagicMock()
            mock_loop.run_in_executor.return_value = None  # Success
            mock_get_event_loop.return_value = mock_loop

            result = await replicate_client.cancel_generation("pred_123")
            assert result is True

    @pytest.mark.asyncio
    async def test_cancel_generation_failure(self, replicate_client):
        """Test generation cancellation failure"""
        with patch('asyncio.get_event_loop') as mock_get_event_loop:
            mock_loop = MagicMock()
            mock_loop.run_in_executor.side_effect = Exception("Cancel failed")
            mock_get_event_loop.return_value = mock_loop

            result = await replicate_client.cancel_generation("pred_123")
            assert result is False


class TestClipMetadata:
    """Test cases for ClipMetadata model"""

    def test_clip_metadata_creation(self):
        """Test creating clip metadata"""
        metadata = ClipMetadata(
            clip_id="clip_123",
            generation_id="gen_456",
            scene_id="scene_789",
            video_url="https://example.com/video.mp4",
            duration_seconds=5.0,
            resolution=VideoResolution.RES_720P,
            format=VideoFormat.MP4,
            model_used="google/veo-3.1-fast",
            prompt_used="Test prompt",
            generation_time_seconds=45.0
        )

        assert metadata.clip_id == "clip_123"
        assert metadata.is_successful() is True
        assert metadata.get_summary().startswith("Clip clip_123: 5.0s")

    def test_clip_metadata_with_error(self):
        """Test clip metadata with error"""
        metadata = ClipMetadata(
            clip_id="clip_123",
            generation_id="gen_456",
            scene_id="scene_789",
            video_url="https://example.com/video.mp4",
            duration_seconds=5.0,
            error_message="Generation failed"
        )

        assert metadata.is_successful() is False
        assert "Failed:" in metadata.get_summary()


class TestGenerateClipRequest:
    """Test cases for GenerateClipRequest model"""

    def test_request_creation(self):
        """Test creating generation request"""
        request = GenerateClipRequest(
            clip_id="clip_123",
            generation_id="gen_456",
            scene_id="scene_789",
            prompt="Test prompt",
            duration_seconds=5.0
        )

        assert request.clip_id == "clip_123"
        assert request.model == "google/veo-3.1-fast"  # Default
        assert request.resolution == VideoResolution.RES_720P  # Default

    def test_request_validation(self):
        """Test request validation"""
        # Valid request
        request = GenerateClipRequest(
            clip_id="clip_123",
            generation_id="gen_456",
            scene_id="scene_789",
            prompt="Test",
            duration_seconds=5.0
        )
        assert request.prompt == "Test"

        # Invalid duration (too short)
        with pytest.raises(ValueError):
            GenerateClipRequest(
                clip_id="clip_123",
                generation_id="gen_456",
                scene_id="scene_789",
                prompt="Test",
                duration_seconds=0.5  # Below minimum
            )
