"""
Integration tests for Recomposition Trigger - PR 403
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from freezegun import freeze_time

from services.recomposition_trigger_service import RecompositionTriggerService
from services.edit_intent_classifier_service import EditIntentClassifierService
from models.recomposition import RecompositionTriggerRequest, RecompositionStatus
from models.edit_intent import EditRequest, EditOperation, EditTarget


class TestRecompositionIntegration:
    """Integration tests for the complete recomposition workflow"""

    @pytest.fixture
    def ffmpeg_backend_url(self):
        """Mock FFmpeg backend URL"""
        return "http://mock-ffmpeg-backend:8000"

    @pytest.fixture
    def recomposition_service(self, ffmpeg_backend_url):
        """Create RecompositionTriggerService with mock backend"""
        return RecompositionTriggerService(
            ffmpeg_backend_url=ffmpeg_backend_url,
            request_timeout=30.0
        )

    @pytest.fixture
    def mock_edit_classifier(self):
        """Create mock edit intent classifier"""
        classifier = MagicMock(spec=EditIntentClassifierService)

        # Mock successful classification
        mock_response = MagicMock()
        mock_response.operations = [
            MagicMock(
                operation_type=EditOperation.TRIM,
                target_type=EditTarget.CLIP,
                target_clips=[0],
                target_time_range={"start": 2.0, "end": 8.0},
                priority=1
            ),
            MagicMock(
                operation_type=EditOperation.MERGE,
                target_type=EditTarget.TRANSITION,
                target_clips=[0, 1],
                parameters={
                    "transition_type": "crossfade",
                    "duration": 1.5,
                    "easing": "linear"
                },
                priority=2
            )
        ]
        mock_response.confidence_score = 0.87
        mock_response.safety_check_passed = True

        classifier.classify_edit_intent.return_value = mock_response
        return classifier

    @pytest.mark.asyncio
    async def test_full_recomposition_workflow(self, recomposition_service, mock_edit_classifier, ffmpeg_backend_url):
        """Test complete workflow from edit request to FFmpeg trigger"""
        # Step 1: Classify edit intent
        edit_request = EditRequest(
            generation_id="gen_integration_001",
            composition_id="comp_integration_001",
            natural_language_edit="Make the first clip 6 seconds shorter and add a smooth crossfade between clips"
        )

        edit_response = mock_edit_classifier.classify_edit_intent(edit_request)

        # Step 2: Create recomposition trigger request
        trigger_request = RecompositionTriggerRequest(
            generation_id=edit_request.generation_id,
            composition_id=edit_request.composition_id,
            edit_plan=edit_response,
            priority="high",
            webhook_url="http://api.example.com/webhooks/recomposition"
        )

        # Step 3: Mock FFmpeg backend response
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock successful FFmpeg job creation
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "job_id": "ffmpeg_integration_job_123",
                "status": "queued",
                "estimated_duration": 60.0,
                "queue_position": 1
            }
            mock_client.post.return_value = mock_response

            # Step 4: Trigger recomposition
            with freeze_time("2024-01-01 12:00:00"):
                trigger_response = await recomposition_service.trigger_recomposition(trigger_request)

            # Verify the complete workflow
            assert trigger_response.recomposition_id.startswith("recomp_")
            assert trigger_response.ffmpeg_job_id == "ffmpeg_integration_job_123"
            assert trigger_response.status == RecompositionStatus.TRIGGERED
            assert trigger_response.estimated_duration_seconds == 60.0

            # Verify FFmpeg API was called correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == f"{ffmpeg_backend_url}/api/v1/compositions"

            request_payload = call_args[1]["json"]
            assert request_payload["composition_id"] == "comp_integration_001"
            assert request_payload["generation_id"] == "gen_integration_001"
            assert request_payload["priority"] == "high"
            assert request_payload["webhook_url"] == "http://api.example.com/webhooks/recomposition"

            # Verify config contains the edits
            config = request_payload["config"]
            assert config["composition_id"] == "comp_integration_001"
            assert config["generation_id"] == "gen_integration_001"
            assert len(config["clip_edits"]) == 1  # One trim operation
            assert len(config["transition_edits"]) == 1  # One transition operation

            # Verify record persistence
            record = recomposition_service.get_recomposition_record(trigger_response.recomposition_id)
            assert record is not None
            assert record.status == RecompositionStatus.TRIGGERED
            assert record.ffmpeg_job_id == "ffmpeg_integration_job_123"
            assert record.edit_plan == edit_response

    @pytest.mark.asyncio
    async def test_recomposition_with_complex_edits(self, recomposition_service):
        """Test recomposition with multiple complex edit operations"""
        # Create complex edit plan with multiple operations
        from models.edit_intent import EditPlan, FFmpegOperation

        complex_edit_plan = EditPlan(
            operations=[
                # Trim first clip
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    target_time_range={"start": 1.0, "end": 7.0},
                    priority=1
                ),
                # Speed up second clip
                FFmpegOperation(
                    operation_type=EditOperation.MERGE,  # Using merge for speed adjustment
                    target_type=EditTarget.CLIP,
                    target_clips=[1],
                    parameters={"speed_multiplier": 1.2},
                    priority=2
                ),
                # Add transition between clips 1 and 2
                FFmpegOperation(
                    operation_type=EditOperation.MERGE,
                    target_type=EditTarget.TRANSITION,
                    target_clips=[1, 2],
                    parameters={
                        "transition_type": "fade",
                        "duration": 2.0,
                        "easing": "ease_in"
                    },
                    priority=3
                ),
                # Update overlay text
                FFmpegOperation(
                    operation_type=EditOperation.MERGE,
                    target_type=EditTarget.OVERLAY,
                    target_clips=[0],
                    parameters={
                        "overlay_id": "title_text",
                        "text_content": "Updated Product Name",
                        "position": {"x": "center", "y": 100}
                    },
                    priority=4
                )
            ],
            confidence_score=0.92,
            safety_check_passed=True
        )

        trigger_request = RecompositionTriggerRequest(
            generation_id="gen_complex_001",
            composition_id="comp_complex_001",
            edit_plan=complex_edit_plan
        )

        # Mock FFmpeg backend
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "job_id": "ffmpeg_complex_job_456",
                "status": "queued",
                "estimated_duration": 90.0,
                "queue_position": 3
            }
            mock_client.post.return_value = mock_response

            trigger_response = await recomposition_service.trigger_recomposition(trigger_request)

            # Verify all edit types were processed
            request_payload = mock_client.post.call_args[1]["json"]
            config = request_payload["config"]

            assert len(config["clip_edits"]) == 2  # Trim + speed adjustment
            assert len(config["transition_edits"]) == 1  # One transition
            assert len(config["overlay_edits"]) == 1  # One overlay update

            # Verify specific edits
            clip_edits = config["clip_edits"]
            trim_edit = next((edit for edit in clip_edits if edit["clip_index"] == 0), None)
            assert trim_edit is not None
            assert trim_edit["trim_start"] == 1.0
            assert trim_edit["trim_end"] == 7.0

            speed_edit = next((edit for edit in clip_edits if edit["clip_index"] == 1), None)
            assert speed_edit is not None
            assert speed_edit["speed_multiplier"] == 1.2

    @pytest.mark.asyncio
    async def test_recomposition_error_recovery(self, recomposition_service):
        """Test error recovery and rollback scenarios"""
        # Create a valid edit plan
        edit_plan = EditPlan(
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    target_time_range={"start": 1.0, "end": 5.0},
                    priority=1
                )
            ],
            confidence_score=0.8,
            safety_check_passed=True
        )

        trigger_request = RecompositionTriggerRequest(
            generation_id="gen_error_test",
            composition_id="comp_error_test",
            edit_plan=edit_plan
        )

        # Test FFmpeg backend failure
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock FFmpeg backend failure
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.text = "FFmpeg service temporarily unavailable"
            mock_client.post.return_value = mock_response

            # Verify exception is raised
            with pytest.raises(Exception, match="Recomposition trigger failed"):
                await recomposition_service.trigger_recomposition(trigger_request)

            # Verify no record was persisted (since it failed)
            all_records = recomposition_service.get_all_recomposition_records()
            assert len(all_records) == 0

    @pytest.mark.asyncio
    async def test_recomposition_status_updates(self, recomposition_service):
        """Test status update functionality"""
        # First create a successful recomposition
        edit_plan = EditPlan(operations=[], confidence_score=0.8, safety_check_passed=True)
        trigger_request = RecompositionTriggerRequest(
            generation_id="gen_status_test",
            composition_id="comp_status_test",
            edit_plan=edit_plan
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "job_id": "ffmpeg_status_job_789",
                "status": "queued",
                "estimated_duration": 30.0
            }
            mock_client.post.return_value = mock_response

            trigger_response = await recomposition_service.trigger_recomposition(trigger_request)

            recomposition_id = trigger_response.recomposition_id

            # Test status updates
            # Update to processing
            success = recomposition_service.update_recomposition_status(
                recomposition_id, RecompositionStatus.PROCESSING
            )
            assert success is True

            record = recomposition_service.get_recomposition_record(recomposition_id)
            assert record.status == RecompositionStatus.PROCESSING

            # Update to completed
            success = recomposition_service.update_recomposition_status(
                recomposition_id, RecompositionStatus.COMPLETED
            )
            assert success is True
            assert record.status == RecompositionStatus.COMPLETED
            assert record.completed_at is not None
            assert record.get_duration() is not None  # Should have duration now

            # Test update of non-existent record
            success = recomposition_service.update_recomposition_status(
                "nonexistent_id", RecompositionStatus.FAILED
            )
            assert success is False

    @pytest.mark.asyncio
    async def test_recomposition_with_different_priorities(self, recomposition_service):
        """Test recomposition with different priority levels"""
        priorities = ["low", "normal", "high", "urgent"]

        for priority in priorities:
            edit_plan = EditPlan(operations=[], confidence_score=0.8, safety_check_passed=True)
            trigger_request = RecompositionTriggerRequest(
                generation_id=f"gen_priority_{priority}",
                composition_id=f"comp_priority_{priority}",
                edit_plan=edit_plan,
                priority=priority
            )

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "job_id": f"ffmpeg_priority_job_{priority}",
                    "status": "queued",
                    "estimated_duration": 45.0
                }
                mock_client.post.return_value = mock_response

                trigger_response = await recomposition_service.trigger_recomposition(trigger_request)

                # Verify priority was passed to FFmpeg backend
                request_payload = mock_client.post.call_args[1]["json"]
                assert request_payload["priority"] == priority

    @pytest.mark.asyncio
    async def test_recomposition_config_preservation(self, recomposition_service):
        """Test that original config is preserved for rollback"""
        edit_plan = EditPlan(
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    target_time_range={"start": 0.5, "end": 4.5},
                    priority=1
                )
            ],
            confidence_score=0.85,
            safety_check_passed=True
        )

        trigger_request = RecompositionTriggerRequest(
            generation_id="gen_config_test",
            composition_id="comp_config_test",
            edit_plan=edit_plan
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "job_id": "ffmpeg_config_job_999",
                "status": "queued",
                "estimated_duration": 25.0
            }
            mock_client.post.return_value = mock_response

            await recomposition_service.trigger_recomposition(trigger_request)

            # Verify original config is preserved
            request_payload = mock_client.post.call_args[1]["json"]
            config = request_payload["config"]
            assert "original_config" in config
            assert config["original_config"]["target_duration"] == 30.0  # From mock
            assert config["original_config"]["resolution"] == "1920x1080"
