"""
Tests for Edit Intent Classifier Service - PR 401
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from ..models.edit_intent import (
    EditRequest,
    EditResponse,
    EditPlan,
    EditClassificationResult,
    SafetyGuardrailResult,
    EditOperation,
    EditTarget,
    FFmpegOperation
)
from ..services.edit_intent_classifier_service import EditIntentClassifierService


class TestEditIntentClassifierService:
    """Test cases for the EditIntentClassifierService"""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client"""
        client = Mock()
        client.call_openai_api = AsyncMock()
        return client

    @pytest.fixture
    def service(self, mock_openai_client):
        """Create service with mocked OpenAI client"""
        with patch('ai.services.edit_intent_classifier_service.OpenAIClient', return_value=mock_openai_client):
            service = EditIntentClassifierService(openai_api_key="test_key", use_mock=True)
            service.openai_client = mock_openai_client
            return service

    @pytest.fixture
    def sample_edit_request(self):
        """Create a sample edit request"""
        return EditRequest(
            generation_id="gen_123",
            natural_language_edit="trim the first 5 seconds and make the middle part louder",
            current_clip_count=3,
            total_duration_seconds=30.0
        )

    @pytest.fixture
    def sample_classification_result(self):
        """Create a sample classification result"""
        return EditClassificationResult(
            intent_summary="Trim video start and increase volume in middle section",
            operations=[
                {
                    "operation_type": "trim",
                    "target_type": "clip",
                    "target_clips": [0],
                    "target_time_range": {"start": 0, "end": 5},
                    "parameters": {"duration": 25},
                    "description": "Trim first 5 seconds from clip 0",
                    "priority": 1
                },
                {
                    "operation_type": "volume",
                    "target_type": "audio",
                    "target_clips": [1],
                    "target_time_range": {"start": 10, "end": 20},
                    "parameters": {"gain": 1.5},
                    "description": "Increase volume by 50% in middle section",
                    "priority": 2
                }
            ],
            confidence=0.85,
            safety_concerns=[]
        )

    def test_service_initialization(self):
        """Test that service initializes correctly"""
        with patch('ai.services.edit_intent_classifier_service.OpenAIClient'):
            service = EditIntentClassifierService(openai_api_key="test_key", use_mock=True)
            assert service.openai_client is not None

    @pytest.mark.asyncio
    async def test_classify_edit_intent_success(self, service, mock_openai_client, sample_edit_request, sample_classification_result):
        """Test successful edit intent classification"""
        # Setup mock response
        mock_response = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "classify_video_edit",
                            "arguments": sample_classification_result.json()
                        }
                    }]
                }
            }]
        }
        mock_openai_client.call_openai_api.return_value = mock_response

        # Execute
        response = await service.classify_edit_intent(sample_edit_request)

        # Verify
        assert isinstance(response, EditResponse)
        assert response.success is True
        assert response.edit_plan.generation_id == "gen_123"
        assert len(response.edit_plan.operations) == 2
        assert response.edit_plan.confidence_score == 0.85
        assert response.can_apply_immediately is True

    @pytest.mark.asyncio
    async def test_classify_edit_intent_with_safety_failure(self, service, mock_openai_client, sample_edit_request):
        """Test classification with safety guardrail failure"""
        # Create request that will target invalid clip index
        bad_request = EditRequest(
            generation_id="gen_123",
            natural_language_edit="edit clip 10",  # Invalid index
            current_clip_count=3  # Only clips 0, 1, 2 exist
        )

        # Mock successful classification but with invalid clip index
        mock_response = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "classify_video_edit",
                            "arguments": """{
                                "intent_summary": "Edit invalid clip",
                                "operations": [{
                                    "operation_type": "trim",
                                    "target_type": "clip",
                                    "target_clips": [10],
                                    "description": "Trim invalid clip",
                                    "priority": 1
                                }],
                                "confidence": 0.9,
                                "safety_concerns": []
                            }"""
                        }
                    }]
                }
            }]
        }
        mock_openai_client.call_openai_api.return_value = mock_response

        # Execute
        response = await service.classify_edit_intent(bad_request)

        # Verify safety check failed
        assert response.success is False
        assert "invalid clip index" in response.error_message.lower()

    def test_build_system_prompt(self, service, sample_edit_request):
        """Test system prompt construction"""
        prompt = service._build_system_prompt(sample_edit_request)

        assert "expert video editor" in prompt
        assert "IMPORTANT RULES" in prompt
        assert "parse the natural language request STRICTLY" in prompt
        assert "Video has 3 clips" in prompt
        assert "Total duration: 30.0 seconds" in prompt
        assert "EDIT OPERATION TYPES" in prompt

    def test_build_user_prompt(self, service, sample_edit_request):
        """Test user prompt construction"""
        prompt = service._build_user_prompt(sample_edit_request)

        assert "analyze this video edit request" in prompt
        assert sample_edit_request.natural_language_edit in prompt
        assert "classify it into structured FFmpeg operations" in prompt

    def test_get_edit_classification_tool(self, service):
        """Test tool definition for OpenAI"""
        tool = service._get_edit_classification_tool()

        assert tool["type"] == "function"
        assert tool["function"]["name"] == "classify_video_edit"

        # Check required properties
        properties = tool["function"]["parameters"]["properties"]
        assert "intent_summary" in properties
        assert "operations" in properties
        assert "confidence" in properties

        # Check operation structure
        op_properties = properties["operations"]["items"]["properties"]
        assert "operation_type" in op_properties
        assert "target_type" in op_properties
        assert "description" in op_properties

    def test_parse_tool_response(self, service, sample_classification_result):
        """Test parsing of OpenAI tool response"""
        # Mock OpenAI response with tool call
        openai_response = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "classify_video_edit",
                            "arguments": sample_classification_result.json()
                        }
                    }]
                }
            }]
        }

        result = service._parse_tool_response(openai_response)

        assert isinstance(result, EditClassificationResult)
        assert result.intent_summary == sample_classification_result.intent_summary
        assert len(result.operations) == 2
        assert result.confidence == 0.85

    def test_parse_tool_response_mock_format(self, service, sample_classification_result):
        """Test parsing of mock response format"""
        # Mock response format
        openai_response = {
            "classification": sample_classification_result.dict()
        }

        result = service._parse_tool_response(openai_response)

        assert isinstance(result, EditClassificationResult)
        assert result.intent_summary == sample_classification_result.intent_summary

    def test_parse_tool_response_invalid(self, service):
        """Test parsing of invalid response"""
        openai_response = {"invalid": "response"}

        with pytest.raises(ValueError, match="Could not parse OpenAI response"):
            service._parse_tool_response(openai_response)

    def test_check_safety_guardrails_valid(self, service, sample_edit_request):
        """Test safety guardrail validation with valid operations"""
        edit_plan = EditPlan(
            generation_id="gen_123",
            request_id="req_456",
            natural_language_request="trim first clip",
            interpreted_intent="Trim first clip",
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    description="Trim first clip"
                )
            ],
            confidence_score=0.9
        )

        result = service._check_safety_guardrails(edit_plan, sample_edit_request)

        assert result.passed is True
        assert len(result.issues) == 0

    def test_check_safety_guardrails_invalid_clip_index(self, service, sample_edit_request):
        """Test safety guardrail validation with invalid clip index"""
        edit_plan = EditPlan(
            generation_id="gen_123",
            request_id="req_456",
            natural_language_request="edit invalid clip",
            interpreted_intent="Edit invalid clip",
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[5],  # Invalid index (only 0,1,2 exist)
                    description="Trim invalid clip"
                )
            ],
            confidence_score=0.9
        )

        result = service._check_safety_guardrails(edit_plan, sample_edit_request)

        assert result.passed is False
        assert len(result.issues) > 0
        assert "invalid clip index" in " ".join(result.issues).lower()

    def test_check_safety_guardrails_empty_operations(self, service, sample_edit_request):
        """Test safety guardrail validation with no operations"""
        edit_plan = EditPlan(
            generation_id="gen_123",
            request_id="req_456",
            natural_language_request="do nothing",
            interpreted_intent="Do nothing",
            operations=[],  # Empty operations
            confidence_score=0.9
        )

        result = service._check_safety_guardrails(edit_plan, sample_edit_request)

        assert result.passed is False
        assert len(result.issues) > 0
        assert "no operations specified" in " ".join(result.issues).lower()

    def test_check_safety_guardrails_time_overlap(self, service, sample_edit_request):
        """Test safety guardrail validation with overlapping time ranges"""
        edit_plan = EditPlan(
            generation_id="gen_123",
            request_id="req_456",
            natural_language_request="multiple overlapping edits",
            interpreted_intent="Multiple overlapping edits",
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    target_time_range={"start": 0, "end": 10},
                    description="First operation"
                ),
                FFmpegOperation(
                    operation_type=EditOperation.VOLUME,
                    target_type=EditTarget.AUDIO,
                    target_clips=[0],
                    target_time_range={"start": 5, "end": 15},  # Overlaps with first
                    description="Second operation"
                )
            ],
            confidence_score=0.9
        )

        result = service._check_safety_guardrails(edit_plan, sample_edit_request)

        assert result.passed is False
        assert len(result.issues) > 0
        assert "overlapping time ranges" in " ".join(result.issues).lower()

    @pytest.mark.asyncio
    async def test_classification_result_to_edit_plan(self, sample_classification_result, sample_edit_request):
        """Test conversion from classification result to edit plan"""
        edit_plan = sample_classification_result.to_edit_plan(sample_edit_request)

        assert isinstance(edit_plan, EditPlan)
        assert edit_plan.generation_id == sample_edit_request.generation_id
        assert edit_plan.natural_language_request == sample_edit_request.natural_language_edit
        assert edit_plan.interpreted_intent == sample_classification_result.intent_summary
        assert len(edit_plan.operations) == 2
        assert edit_plan.confidence_score == sample_classification_result.confidence

        # Check operations were converted correctly
        assert all(isinstance(op, FFmpegOperation) for op in edit_plan.operations)

    def test_edit_plan_validation(self):
        """Test edit plan validation methods"""
        # Valid plan
        valid_plan = EditPlan(
            generation_id="gen_123",
            request_id="req_456",
            natural_language_request="valid edit",
            interpreted_intent="Valid edit",
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    description="Trim clip"
                )
            ],
            confidence_score=0.9
        )

        assert valid_plan.validate_technical_feasibility() is True

        # Invalid plan with conflicting operations
        invalid_plan = EditPlan(
            generation_id="gen_123",
            request_id="req_456",
            natural_language_request="conflicting edits",
            interpreted_intent="Conflicting edits",
            operations=[
                FFmpegOperation(
                    operation_type=EditOperation.TRIM,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],
                    description="Trim clip"
                ),
                FFmpegOperation(
                    operation_type=EditOperation.SPLIT,
                    target_type=EditTarget.CLIP,
                    target_clips=[0],  # Same clip, conflicting operations
                    description="Split same clip"
                )
            ],
            confidence_score=0.9
        )

        assert invalid_plan.validate_technical_feasibility() is False

    def test_ffmpeg_operation_conversion(self):
        """Test FFmpeg operation to command conversion"""
        operation = FFmpegOperation(
            operation_type=EditOperation.TRIM,
            target_type=EditTarget.CLIP,
            target_clips=[0, 1],
            target_time_range={"start": 5.0, "end": 15.0},
            parameters={"duration": 10},
            description="Trim clips 0 and 1",
            priority=2
        )

        command = operation.to_ffmpeg_command()

        assert command["operation"] == "trim"
        assert command["target"] == "clip"
        assert command["clips"] == [0, 1]
        assert command["time_range"] == {"start": 5.0, "end": 15.0}
        assert command["parameters"] == {"duration": 10}
        assert command["description"] == "Trim clips 0 and 1"
        assert command["priority"] == 2


class TestEditIntentIntegration:
    """Integration tests for the complete edit intent classification workflow"""

    @pytest.mark.asyncio
    async def test_full_classification_workflow(self, service, mock_openai_client, sample_edit_request):
        """Test complete workflow from request to edit plan"""
        # Mock OpenAI response
        mock_response = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "classify_video_edit",
                            "arguments": """{
                                "intent_summary": "Trim video and adjust audio",
                                "operations": [
                                    {
                                        "operation_type": "trim",
                                        "target_type": "clip",
                                        "target_clips": [0],
                                        "parameters": {"start_time": 0, "end_time": 5},
                                        "description": "Remove first 5 seconds",
                                        "priority": 1
                                    },
                                    {
                                        "operation_type": "volume",
                                        "target_type": "audio",
                                        "target_clips": [1],
                                        "parameters": {"gain": 1.2},
                                        "description": "Increase volume by 20%",
                                        "priority": 2
                                    }
                                ],
                                "confidence": 0.88,
                                "safety_concerns": []
                            }"""
                        }
                    }]
                }
            }]
        }
        mock_openai_client.call_openai_api.return_value = mock_response

        # Execute full workflow
        response = await service.classify_edit_intent(sample_edit_request)

        # Verify complete response
        assert response.success is True
        assert response.edit_plan.generation_id == sample_edit_request.generation_id
        assert len(response.edit_plan.operations) == 2
        assert response.edit_plan.confidence_score == 0.88
        assert response.edit_plan.safety_check_passed is True
        assert response.can_apply_immediately is True

        # Verify operations are properly structured
        trim_op = response.edit_plan.operations[0]
        assert trim_op.operation_type == EditOperation.TRIM
        assert trim_op.target_clips == [0]

        volume_op = response.edit_plan.operations[1]
        assert volume_op.operation_type == EditOperation.VOLUME
        assert volume_op.target_type == EditTarget.AUDIO

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, service, mock_openai_client, sample_edit_request):
        """Test error handling in the classification workflow"""
        # Mock OpenAI failure
        mock_openai_client.call_openai_api.side_effect = Exception("OpenAI API error")

        response = await service.classify_edit_intent(sample_edit_request)

        assert response.success is False
        assert "OpenAI API error" in response.error_message
        assert response.can_apply_immediately is False

    def test_edge_case_requests(self, service):
        """Test handling of edge case edit requests"""
        # Very short request
        short_request = EditRequest(
            generation_id="gen_123",
            natural_language_edit="trim"
        )

        system_prompt = service._build_system_prompt(short_request)
        assert "robust against" in system_prompt  # Should handle poorly worded requests

        # Request with irrelevant information
        noisy_request = EditRequest(
            generation_id="gen_123",
            natural_language_edit="Hey there! Can you please trim the video by removing the first 10 seconds? Also, I like cats. Thanks!"
        )

        system_prompt = service._build_system_prompt(noisy_request)
        assert "do not use any hardcoded patterns" in system_prompt  # Should ignore irrelevant info

        # Empty request
        empty_request = EditRequest(
            generation_id="gen_123",
            natural_language_edit=""
        )

        user_prompt = service._build_user_prompt(empty_request)
        assert empty_request.natural_language_edit in user_prompt  # Still processes even if empty
