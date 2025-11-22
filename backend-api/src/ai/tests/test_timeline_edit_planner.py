"""
Unit tests for Timeline Edit Planner Service - PR #402
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from ..models.edit_intent import EditPlan, FFmpegOperation, EditOperation, EditTarget
from ..models.clip_assembly import DatabaseClipMetadata, ClipStorageStatus
from ..models.replicate_client import VideoResolution, VideoFormat
from ..services.timeline_edit_planner_service import TimelineEditPlannerService, TimelineEditResult


class TestTimelineEditPlannerService:
    """Test cases for TimelineEditPlannerService"""

    @pytest.fixture
    def service(self):
        """Create a TimelineEditPlannerService instance"""
        return TimelineEditPlannerService(use_mock=True)

    @pytest.fixture
    def sample_clips(self):
        """Create sample clip metadata for testing"""
        return [
            DatabaseClipMetadata(
                clip_id="clip_001",
                generation_id="gen_123",
                scene_id="scene_001",
                sequence_order=0,
                start_time_seconds=0.0,
                end_time_seconds=5.0,
                duration_seconds=5.0,
                storage_status=ClipStorageStatus.COMPLETED,
                video_url="https://example.com/clip1.mp4",
                resolution=VideoResolution.RES_720P,
                format=VideoFormat.MP4,
                created_at=datetime.utcnow()
            ),
            DatabaseClipMetadata(
                clip_id="clip_002",
                generation_id="gen_123",
                scene_id="scene_002",
                sequence_order=1,
                start_time_seconds=5.0,
                end_time_seconds=10.0,
                duration_seconds=5.0,
                storage_status=ClipStorageStatus.COMPLETED,
                video_url="https://example.com/clip2.mp4",
                resolution=VideoResolution.RES_720P,
                format=VideoFormat.MP4,
                created_at=datetime.utcnow()
            ),
            DatabaseClipMetadata(
                clip_id="clip_003",
                generation_id="gen_123",
                scene_id="scene_003",
                sequence_order=2,
                start_time_seconds=10.0,
                end_time_seconds=15.0,
                duration_seconds=5.0,
                storage_status=ClipStorageStatus.COMPLETED,
                video_url="https://example.com/clip3.mp4",
                resolution=VideoResolution.RES_720P,
                format=VideoFormat.MP4,
                created_at=datetime.utcnow()
            )
        ]

    @pytest.fixture
    def sample_edit_plan(self):
        """Create a sample edit plan"""
        return EditPlan(
            generation_id="gen_123",
            request_id="edit_123_1234567890",
            natural_language_request="Trim the first clip and swap clips 1 and 2",
            interpreted_intent="User wants to trim first clip to 3 seconds and reorder clips",
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    parameters={"duration": 3.0}
                ),
                FFmpegOperation(
                    operation_type=EditOperation.REORDER,
                    target_type=EditTarget.TIMELINE,
                    target_clips=[1, 2],
                    parameters={"new_order": [2, 1]}
                )
            ],
            created_at=datetime.utcnow()
        )

    def test_service_initialization(self):
        """Test service initialization"""
        service = TimelineEditPlannerService()
        assert service.redis_client is None
        assert service.use_mock is False
        assert service.cache_ttl == 7200

        service_with_redis = TimelineEditPlannerService(redis_client=MagicMock())
        assert service_with_redis.redis_client is not None

    @pytest.mark.asyncio
    async def test_plan_timeline_edits_success(self, service, sample_edit_plan, sample_clips):
        """Test successful timeline edit planning"""
        result = await service.plan_timeline_edits(sample_edit_plan, sample_clips)

        assert isinstance(result, TimelineEditResult)
        assert result.original_plan == sample_edit_plan
        assert result.is_successful
        assert len(result.applied_operations) == 2
        assert len(result.modified_clips) == 3
        assert result.timeline_preview is not None

    @pytest.mark.asyncio
    async def test_plan_timeline_edits_validation_failure(self, service, sample_clips):
        """Test timeline edit planning with validation failure"""
        # Create an invalid edit plan (references non-existent clip)
        invalid_plan = EditPlan(
            generation_id="gen_123",
            request_id="edit_invalid",
            natural_language_request="Invalid operation",
            interpreted_intent="Invalid",
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[99],  # Invalid clip index
                    parameters={"duration": 2.0}
                )
            ]
        )

        result = await service.plan_timeline_edits(invalid_plan, sample_clips)

        assert isinstance(result, TimelineEditResult)
        assert not result.is_successful
        assert result.error_message is not None
        assert "validation failed" in result.error_message.lower()

    def test_validate_operations_valid(self, service, sample_edit_plan, sample_clips):
        """Test validation of valid operations"""
        result = service._validate_operations(sample_edit_plan.operations, sample_clips)

        assert result['is_feasible'] is True
        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0

    def test_validate_operations_invalid_clip_index(self, service, sample_clips):
        """Test validation with invalid clip index"""
        operations = [
            FFmpegOperation(
                operation_type=EditOperation.TRIM,
                target_type=EditTarget.CLIP,
                target_clips=[99],  # Invalid index
                parameters={"duration": 2.0}
            )
        ]

        result = service._validate_operations(operations, sample_clips)

        assert result['is_feasible'] is False
        assert len(result['errors']) > 0
        assert "invalid clip index" in result['errors'][0].lower()

    def test_validate_trim_operation_valid(self, service, sample_clips):
        """Test validation of valid trim operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.TRIM,
            target_type=EditTarget.CLIP,
            target_clips=[0],
            parameters={"duration": 3.0}
        )

        result = service._validate_trim_operation(operation, sample_clips)

        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0

    def test_validate_trim_operation_invalid_duration(self, service, sample_clips):
        """Test validation of trim operation with invalid duration"""
        operation = FFmpegOperation(
            operation_type=EditOperation.TRIM,
            target_type=EditTarget.CLIP,
            target_clips=[0],
            parameters={"duration": 10.0}  # Longer than original clip
        )

        result = service._validate_trim_operation(operation, sample_clips)

        assert len(result['errors']) > 0
        assert "cannot trim" in result['errors'][0].lower()

    def test_validate_reorder_operation_valid(self, service, sample_clips):
        """Test validation of valid reorder operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.REORDER,
            target_type=EditTarget.TIMELINE,
            target_clips=[0, 1],
            parameters={"new_order": [1, 0]}
        )

        result = service._validate_reorder_operation(operation, sample_clips)

        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0

    def test_validate_reorder_operation_insufficient_clips(self, service, sample_clips):
        """Test validation of reorder operation with insufficient clips"""
        operation = FFmpegOperation(
            operation_type=EditOperation.REORDER,
            target_type=EditTarget.TIMELINE,
            target_clips=[0],  # Only one clip
            parameters={"new_order": [0]}
        )

        result = service._validate_reorder_operation(operation, sample_clips)

        assert len(result['errors']) > 0
        assert "requires at least 2 clips" in result['errors'][0]

    def test_detect_operation_conflicts_trim_split(self, service):
        """Test detection of trim/split conflicts"""
        operations = [
            FFmpegOperation(
                operation_type=EditOperation.TRIM,
                target_type=EditTarget.CLIP,
                target_clips=[0],
                parameters={"duration": 3.0}
            ),
            FFmpegOperation(
                operation_type=EditOperation.SPLIT,
                target_type=EditTarget.CLIP,
                target_clips=[0],  # Same clip
                parameters={"split_time": 2.0}
            )
        ]

        conflicts = service._detect_operation_conflicts(operations)

        assert len(conflicts) > 0
        assert "cannot both trim and split" in conflicts[0]

    def test_apply_trim_operation_valid(self, service, sample_clips):
        """Test applying valid trim operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.TRIM,
            target_type=EditTarget.CLIP,
            target_clips=[0],
            parameters={"duration": 3.0}
        )

        result = service._apply_operation(operation, sample_clips)

        assert result is True
        assert sample_clips[0].duration_seconds == 3.0
        assert sample_clips[0].end_time_seconds == 3.0

    def test_apply_reorder_operation_valid(self, service, sample_clips):
        """Test applying valid reorder operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.REORDER,
            target_type=EditTarget.TIMELINE,
            target_clips=[0, 1],
            parameters={"new_order": [1, 0]}
        )

        result = service._apply_operation(operation, sample_clips)

        assert result is True
        # Check that sequence orders were updated
        assert sample_clips[0].sequence_order == 1
        assert sample_clips[1].sequence_order == 0

    def test_apply_timing_operation_valid(self, service, sample_clips):
        """Test applying valid timing operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.TIMING,
            target_type=EditTarget.CLIP,
            target_clips=[0],
            parameters={"time_offset": 1.0}
        )

        result = service._apply_operation(operation, sample_clips)

        assert result is True
        assert sample_clips[0].start_time_seconds == 1.0
        assert sample_clips[0].end_time_seconds == 6.0

    def test_apply_overlay_operation_valid(self, service, sample_clips):
        """Test applying valid overlay operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.OVERLAY,
            target_type=EditTarget.CLIP,
            target_clips=[0],
            parameters={"start_time": 1.0, "duration": 2.0}
        )

        result = service._apply_operation(operation, sample_clips)

        assert result is True

    def test_apply_overlay_operation_invalid(self, service, sample_clips):
        """Test applying invalid overlay operation"""
        operation = FFmpegOperation(
            operation_type=EditOperation.OVERLAY,
            target_type=EditTarget.CLIP,
            target_clips=[0],
            parameters={"start_time": 2.0, "end_time": 1.0}  # Invalid: end before start
        )

        result = service._apply_operation(operation, sample_clips)

        assert result is False

    def test_recalculate_timeline_no_clips(self, service):
        """Test timeline recalculation with empty clip list"""
        clips = []
        service._recalculate_timeline(clips)

        assert len(clips) == 0

    def test_recalculate_timeline_single_clip(self, service, sample_clips):
        """Test timeline recalculation with single clip"""
        single_clip = [sample_clips[0]]
        service._recalculate_timeline(single_clip)

        assert single_clip[0].start_time_seconds == 0.0
        assert single_clip[0].end_time_seconds == 5.0
        assert single_clip[0].duration_seconds == 5.0

    def test_recalculate_timeline_multiple_clips(self, service, sample_clips):
        """Test timeline recalculation with multiple clips"""
        # Modify clips to have gaps and overlaps
        sample_clips[1].start_time_seconds = 6.0  # Gap after first clip
        sample_clips[1].end_time_seconds = 11.0
        sample_clips[2].start_time_seconds = 10.0  # Overlap with second clip
        sample_clips[2].end_time_seconds = 15.0

        service._recalculate_timeline(sample_clips)

        # Should maintain contiguous timeline
        assert sample_clips[0].start_time_seconds == 0.0
        assert sample_clips[0].end_time_seconds == 5.0
        assert sample_clips[1].start_time_seconds == 5.0
        assert sample_clips[1].end_time_seconds == 10.0
        assert sample_clips[2].start_time_seconds == 10.0
        assert sample_clips[2].end_time_seconds == 15.0

    def test_generate_timeline_preview(self, service, sample_clips):
        """Test timeline preview generation"""
        preview = service._generate_timeline_preview(sample_clips)

        assert isinstance(preview, dict)
        assert preview['total_duration'] == 15.0
        assert preview['clip_count'] == 3
        assert len(preview['clips']) == 3

        # Check first clip preview
        first_clip = preview['clips'][0]
        assert first_clip['clip_id'] == 'clip_001'
        assert first_clip['start_time'] == 0.0
        assert first_clip['end_time'] == 5.0
        assert first_clip['duration'] == 5.0

    def test_timeline_edit_result_creation(self, sample_edit_plan, sample_clips):
        """Test TimelineEditResult creation and methods"""
        result = TimelineEditResult(
            original_plan=sample_edit_plan,
            modified_clips=sample_clips,
            applied_operations=sample_edit_plan.operations,
            validation_result={'is_feasible': True, 'errors': [], 'warnings': []},
            is_successful=True
        )

        assert result.original_plan == sample_edit_plan
        assert len(result.modified_clips) == 3
        assert len(result.applied_operations) == 2
        assert result.is_successful is True

        # Test summary method
        summary = result.get_summary()
        assert summary['generation_id'] == 'gen_123'
        assert summary['total_operations'] == 2
        assert summary['successful_operations'] == 2
        assert summary['validation_errors'] == 0
        assert summary['is_successful'] is True

        # Test fully successful check
        assert result.is_fully_successful() is True

    def test_timeline_edit_result_with_failures(self, sample_edit_plan, sample_clips):
        """Test TimelineEditResult with operation failures"""
        result = TimelineEditResult(
            original_plan=sample_edit_plan,
            modified_clips=sample_clips,
            applied_operations=sample_edit_plan.operations,
            successful_operations=[sample_edit_plan.operations[0]],  # Only first succeeded
            validation_result={'is_feasible': True, 'errors': [], 'warnings': []},
            is_successful=False,
            error_message="Some operations failed"
        )

        assert result.is_successful is False
        assert len(result.successful_operations) == 1
        assert result.error_message == "Some operations failed"

        # Test summary
        summary = result.get_summary()
        assert summary['successful_operations'] == 1
        assert summary['is_successful'] is False

        # Test fully successful check
        assert result.is_fully_successful() is False

    @pytest.mark.asyncio
    async def test_redis_caching_integration(self, sample_edit_plan, sample_clips):
        """Test Redis caching integration"""
        mock_redis = MagicMock()
        service = TimelineEditPlannerService(redis_client=mock_redis, use_mock=False)

        # Mock cache miss
        mock_redis.get.return_value = None

        result = await service.plan_timeline_edits(sample_edit_plan, sample_clips)

        # Verify Redis interactions
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()

    def test_complex_edit_plan_validation(self, service, sample_clips):
        """Test validation of complex edit plan with multiple operations"""
        complex_plan = EditPlan(
            generation_id="gen_complex",
            request_id="edit_complex",
            natural_language_request="Complex edit plan",
            interpreted_intent="Multiple operations",
            operations=[
                # Valid trim
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    parameters={"duration": 3.0}
                ),
                # Valid reorder
                FFmpegOperation(
                    operation_type=EditOperation.REORDER,
                    target_type=EditTarget.TIMELINE,
                    target_clips=[1, 2],
                    parameters={"new_order": [2, 1]}
                ),
                # Invalid operation (conflicts with trim)
                FFmpegOperation(
                    operation_type=EditOperation.SPLIT,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],  # Same clip as trim
                    parameters={"split_time": 2.0}
                )
            ]
        )

        result = service._validate_operations(complex_plan.operations, sample_clips)

        assert result['is_feasible'] is False
        assert len(result['errors']) > 0

    def test_clip_index_mapping(self, service, sample_clips):
        """Test that clip index mapping works correctly"""
        # Clips should be sorted by sequence_order initially
        assert sample_clips[0].sequence_order == 0
        assert sample_clips[1].sequence_order == 1
        assert sample_clips[2].sequence_order == 2

        # After operations that might reorder, the service should handle index mapping
        operation = FFmpegOperation(
            operation_type=EditOperation.REORDER,
            target_type=EditTarget.TIMELINE,
            target_clips=[0, 1],  # Referring to clips by their current sequence_order
            parameters={"new_order": [1, 0]}
        )

        result = service._apply_operation(operation, sample_clips)

        assert result is True
        # Verify the reordering was applied
        assert sample_clips[0].sequence_order == 1
        assert sample_clips[1].sequence_order == 0
