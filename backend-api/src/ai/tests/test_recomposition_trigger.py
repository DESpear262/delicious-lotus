"""
Unit tests for Recomposition Trigger Service - PR 403
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from freezegun import freeze_time

from services.recomposition_trigger_service import RecompositionTriggerService
from models.recomposition import (
    RecompositionTriggerRequest,
    RecompositionTriggerResponse,
    UpdatedCompositionConfig,
    RecompositionRecord,
    RecompositionStatus,
    ClipEditInstruction,
    FFmpegJobTriggerRequest,
    FFmpegJobTriggerResponse
)
from models.edit_intent import EditPlan, FFmpegOperation, EditOperation, EditTarget


@pytest.fixture
def recomposition_service():
    """Create RecompositionTriggerService instance"""
    return RecompositionTriggerService(
        ffmpeg_backend_url="http://ffmpeg-backend:8000",
        request_timeout=30.0
    )


@pytest.fixture
def sample_edit_plan():
    """Create sample edit plan for testing"""
    return EditPlan(
        operations=[
            FFmpegOperation(
                operation_type=EditOperation.TRIM,
                target_type=EditTarget.CLIP,
                target_clips=[0],
                target_time_range={"start": 2.0, "end": 8.0},
                priority=1
            ),
            FFmpegOperation(
                operation_type=EditOperation.MERGE,
                target_type=EditTarget.TRANSITION,
                target_clips=[0, 1],
                parameters={
                    "transition_type": "crossfade",
                    "duration": 1.0,
                    "easing": "linear"
                },
                priority=2
            )
        ],
        confidence_score=0.85,
        safety_check_passed=True
    )


@pytest.fixture
def sample_trigger_request(sample_edit_plan):
    """Create sample trigger request"""
    return RecompositionTriggerRequest(
        generation_id="gen_123",
        composition_id="comp_456",
        edit_plan=sample_edit_plan,
        priority="normal"
    )


class TestRecompositionTriggerService:
    """Test cases for RecompositionTriggerService"""

    def test_initialization(self, recomposition_service):
        """Test service initializes correctly"""
        assert recomposition_service.ffmpeg_backend_url == "http://ffmpeg-backend:8000"
        assert recomposition_service.request_timeout == 30.0
        assert isinstance(recomposition_service._recomposition_records, dict)

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_trigger_recomposition_success(self, mock_client_class, recomposition_service, sample_trigger_request):
        """Test successful recomposition trigger"""
        # Mock HTTP client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock FFmpeg backend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_id": "ffmpeg_job_789",
            "status": "queued",
            "estimated_duration": 45.0,
            "queue_position": 2
        }
        mock_client.post.return_value = mock_response

        with freeze_time("2024-01-01 12:00:00"):
            response = await recomposition_service.trigger_recomposition(sample_trigger_request)

        # Verify response structure
        assert isinstance(response, RecompositionTriggerResponse)
        assert response.ffmpeg_job_id == "ffmpeg_job_789"
        assert response.status == RecompositionStatus.TRIGGERED
        assert response.estimated_duration_seconds == 45.0
        assert "recompositions" in response.status_url

        # Verify record was created and stored
        record = recomposition_service.get_recomposition_record(response.recomposition_id)
        assert record is not None
        assert record.status == RecompositionStatus.TRIGGERED
        assert record.ffmpeg_job_id == "ffmpeg_job_789"
        assert record.composition_id == "comp_456"
        assert record.generation_id == "gen_123"

        # Verify HTTP request was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://ffmpeg-backend:8000/api/v1/compositions"
        request_data = call_args[1]["json"]

        assert request_data["composition_id"] == "comp_456"
        assert request_data["generation_id"] == "gen_123"
        assert request_data["priority"] == "normal"
        assert "config" in request_data

    @pytest.mark.asyncio
    async def test_trigger_recomposition_http_failure(self, recomposition_service, sample_trigger_request):
        """Test recomposition trigger with HTTP failure"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock failed HTTP response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post.return_value = mock_response

            with pytest.raises(Exception, match="Recomposition trigger failed"):
                await recomposition_service.trigger_recomposition(sample_trigger_request)

    def test_build_updated_config(self, recomposition_service, sample_edit_plan):
        """Test building updated config from edit plan"""
        # This would normally be async, but we're testing the logic
        # In real usage, this is called from trigger_recomposition

        # Create a mock for the async _get_original_composition_config call
        original_config = {
            "target_duration": 30.0,
            "resolution": "1920x1080",
            "frame_rate": 30,
            "clips": [{"index": 0, "duration": 10.0}, {"index": 1, "duration": 10.0}],
            "transitions": [],
            "overlays": []
        }

        with patch.object(recomposition_service, '_get_original_composition_config', return_value=original_config):
            # Call the method directly (normally async)
            import asyncio
            config = asyncio.run(recomposition_service._build_updated_config(
                "gen_123", "comp_456", sample_edit_plan
            ))

            assert isinstance(config, UpdatedCompositionConfig)
            assert config.composition_id == "comp_456"
            assert config.generation_id == "gen_123"
            assert config.target_duration == 30.0
            assert len(config.clip_edits) == 1  # One trim operation
            assert len(config.transition_edits) == 1  # One merge operation

    def test_convert_clip_operation_trim(self, recomposition_service):
        """Test converting clip trim operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.TRIM,
            target_type=EditTarget.CLIP,
            target_clips=[1],
            target_time_range={"start": 3.0, "end": 7.0},
            priority=1
        )

        clip_edit = recomposition_service._convert_clip_operation(operation)

        assert clip_edit is not None
        assert clip_edit.clip_index == 1
        assert clip_edit.trim_start == 3.0
        assert clip_edit.trim_end == 7.0

    def test_convert_clip_operation_no_changes(self, recomposition_service):
        """Test converting clip operation with no actual changes"""
        operation = FFmpegOperation(
            operation_type=EditOperation.TRIM,
            target_type=EditTarget.CLIP,
            target_clips=[0],
            # No target_time_range
            priority=1
        )

        clip_edit = recomposition_service._convert_clip_operation(operation)

        # Should return None since no actual changes
        assert clip_edit is None

    def test_convert_transition_operation(self, recomposition_service):
        """Test converting transition operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.MERGE,
            target_type=EditTarget.TRANSITION,
            target_clips=[0, 1],
            parameters={
                "transition_type": "crossfade",
                "duration": 2.0,
                "easing": "ease_in_out"
            },
            priority=1
        )

        transition_edit = recomposition_service._convert_transition_operation(operation)

        assert transition_edit is not None
        assert transition_edit.between_clips == (0, 1)
        assert transition_edit.transition_type == "crossfade"
        assert transition_edit.duration == 2.0
        assert transition_edit.easing == "ease_in_out"

    def test_convert_overlay_operation(self, recomposition_service):
        """Test converting overlay operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.MERGE,  # Overlays often come from merge operations
            target_type=EditTarget.OVERLAY,
            target_clips=[0],
            parameters={
                "overlay_id": "text_001",
                "text_content": "New Product Name",
                "position": {"x": 100, "y": 200},
                "timing": {"start_time": 5.0, "end_time": 10.0}
            },
            priority=1
        )

        overlay_edit = recomposition_service._convert_overlay_operation(operation)

        assert overlay_edit is not None
        assert overlay_edit.overlay_id == "text_001"
        assert overlay_edit.text_content == "New Product Name"
        assert overlay_edit.position == {"x": 100, "y": 200}
        assert overlay_edit.timing == {"start_time": 5.0, "end_time": 10.0}

    def test_create_edit_summary(self, recomposition_service):
        """Test creating edit summary"""
        config = UpdatedCompositionConfig(
            composition_id="comp_123",
            generation_id="gen_456",
            target_duration=30.0,
            clip_edits=[ClipEditInstruction(clip_index=0)],
            transition_edits=[TransitionEditInstruction(between_clips=(0, 1))],
            overlay_edits=[]
        )

        summary = recomposition_service._create_edit_summary(config)
        assert "1 clip edit" in summary
        assert "1 transition change" in summary

    def test_create_edit_summary_no_changes(self, recomposition_service):
        """Test creating edit summary with no changes"""
        config = UpdatedCompositionConfig(
            composition_id="comp_123",
            generation_id="gen_456",
            target_duration=30.0,
            clip_edits=[],
            transition_edits=[],
            overlay_edits=[]
        )

        summary = recomposition_service._create_edit_summary(config)
        assert "no changes" in summary

    def test_get_recomposition_record(self, recomposition_service):
        """Test getting recomposition record"""
        # Create a mock record
        record = RecompositionRecord(
            recomposition_id="recomp_123",
            composition_id="comp_456",
            generation_id="gen_789",
            edit_plan=EditPlan(operations=[]),
            updated_config=UpdatedCompositionConfig(
                composition_id="comp_456",
                generation_id="gen_789",
                target_duration=30.0
            )
        )

        recomposition_service._recomposition_records["recomp_123"] = record

        retrieved = recomposition_service.get_recomposition_record("recomp_123")
        assert retrieved is not None
        assert retrieved.recomposition_id == "recomp_123"

        # Test non-existent record
        assert recomposition_service.get_recomposition_record("nonexistent") is None

    def test_update_recomposition_status(self, recomposition_service):
        """Test updating recomposition status"""
        # Create and store a record
        record = RecompositionRecord(
            recomposition_id="recomp_123",
            composition_id="comp_456",
            generation_id="gen_789",
            edit_plan=EditPlan(operations=[]),
            updated_config=UpdatedCompositionConfig(
                composition_id="comp_456",
                generation_id="gen_789",
                target_duration=30.0
            )
        )
        recomposition_service._recomposition_records["recomp_123"] = record

        # Test successful completion
        success = recomposition_service.update_recomposition_status("recomp_123", RecompositionStatus.COMPLETED)
        assert success is True
        assert record.status == RecompositionStatus.COMPLETED
        assert record.completed_at is not None

        # Test failure status
        success = recomposition_service.update_recomposition_status(
            "recomp_123",
            RecompositionStatus.FAILED,
            "Processing error",
            {"details": "FFmpeg failed"}
        )
        assert success is True
        assert record.status == RecompositionStatus.FAILED
        assert record.error_message == "Processing error"
        assert record.error_details == {"details": "FFmpeg failed"}

        # Test non-existent record
        success = recomposition_service.update_recomposition_status("nonexistent", RecompositionStatus.COMPLETED)
        assert success is False


class TestRecompositionRecord:
    """Test cases for RecompositionRecord model"""

    def test_record_creation(self):
        """Test creating recomposition record"""
        record = RecompositionRecord(
            recomposition_id="recomp_123",
            composition_id="comp_456",
            generation_id="gen_789",
            edit_plan=EditPlan(operations=[]),
            updated_config=UpdatedCompositionConfig(
                composition_id="comp_456",
                generation_id="gen_789",
                target_duration=30.0
            )
        )

        assert record.recomposition_id == "recomp_123"
        assert record.status == RecompositionStatus.PENDING
        assert record.can_rollback is True
        assert not record.is_successful()

    def test_record_mark_triggered(self):
        """Test marking record as triggered"""
        record = RecompositionRecord(
            recomposition_id="recomp_123",
            composition_id="comp_456",
            generation_id="gen_789",
            edit_plan=EditPlan(operations=[]),
            updated_config=UpdatedCompositionConfig(
                composition_id="comp_456",
                generation_id="gen_789",
                target_duration=30.0
            )
        )

        record.mark_triggered("ffmpeg_job_456")

        assert record.status == RecompositionStatus.TRIGGERED
        assert record.ffmpeg_job_id == "ffmpeg_job_456"
        assert record.triggered_at is not None

    def test_record_mark_completed(self):
        """Test marking record as completed"""
        record = RecompositionRecord(
            recomposition_id="recomp_123",
            composition_id="comp_456",
            generation_id="gen_789",
            edit_plan=EditPlan(operations=[]),
            updated_config=UpdatedCompositionConfig(
                composition_id="comp_456",
                generation_id="gen_789",
                target_duration=30.0
            )
        )

        record.mark_completed()

        assert record.status == RecompositionStatus.COMPLETED
        assert record.is_successful()
        assert record.completed_at is not None

    def test_record_mark_failed(self):
        """Test marking record as failed"""
        record = RecompositionRecord(
            recomposition_id="recomp_123",
            composition_id="comp_456",
            generation_id="gen_789",
            edit_plan=EditPlan(operations=[]),
            updated_config=UpdatedCompositionConfig(
                composition_id="comp_456",
                generation_id="gen_789",
                target_duration=30.0
            )
        )

        record.mark_failed("Processing failed", {"error_code": "FFMPEG_ERROR"})

        assert record.status == RecompositionStatus.FAILED
        assert not record.is_successful()
        assert record.error_message == "Processing failed"
        assert record.error_details == {"error_code": "FFMPEG_ERROR"}
        assert record.completed_at is not None

    def test_record_get_duration(self):
        """Test getting record duration"""
        record = RecompositionRecord(
            recomposition_id="recomp_123",
            composition_id="comp_456",
            generation_id="gen_789",
            edit_plan=EditPlan(operations=[]),
            updated_config=UpdatedCompositionConfig(
                composition_id="comp_456",
                generation_id="gen_789",
                target_duration=30.0
            )
        )

        # No timing data yet
        assert record.get_duration() is None

        # Set timing data
        record.created_at = datetime(2024, 1, 1, 12, 0, 0)
        record.completed_at = datetime(2024, 1, 1, 12, 1, 30)  # 90 seconds later

        duration = record.get_duration()
        assert duration == 90.0


class TestUpdatedCompositionConfig:
    """Test cases for UpdatedCompositionConfig model"""

    def test_config_creation(self):
        """Test creating updated composition config"""
        config = UpdatedCompositionConfig(
            composition_id="comp_123",
            generation_id="gen_456",
            target_duration=30.0,
            resolution="1920x1080",
            frame_rate=30,
            clip_edits=[ClipEditInstruction(clip_index=0, trim_start=2.0, trim_end=8.0)],
            transition_edits=[],
            overlay_edits=[],
            original_config={"original": "data"}
        )

        assert config.composition_id == "comp_123"
        assert config.generation_id == "gen_456"
        assert config.target_duration == 30.0
        assert config.has_changes() is True

    def test_config_has_changes_false(self):
        """Test config with no changes"""
        config = UpdatedCompositionConfig(
            composition_id="comp_123",
            generation_id="gen_456",
            target_duration=30.0,
            clip_edits=[],
            transition_edits=[],
            overlay_edits=[]
        )

        assert config.has_changes() is False

    def test_config_get_clip_edit(self):
        """Test getting clip edit by index"""
        edit1 = ClipEditInstruction(clip_index=0, trim_start=1.0)
        edit2 = ClipEditInstruction(clip_index=2, trim_end=5.0)

        config = UpdatedCompositionConfig(
            composition_id="comp_123",
            generation_id="gen_456",
            target_duration=30.0,
            clip_edits=[edit1, edit2]
        )

        assert config.get_clip_edit(0) == edit1
        assert config.get_clip_edit(2) == edit2
        assert config.get_clip_edit(1) is None  # No edit for index 1
