"""
Edit Intent Classifier Service - PR 401: Edit Intent Classifier (OpenAI)
"""

import json
import logging
from typing import Dict, List, Optional, Any
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
from ..core.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class EditIntentClassifierService:
    """
    Service for classifying natural language edit requests using OpenAI

    Converts user-described edits into structured FFmpeg operations via LLM tool calls.
    """

    def __init__(self, openai_api_key: str, use_mock: bool = False):
        """
        Initialize the edit intent classifier

        Args:
            openai_api_key: OpenAI API key
            use_mock: Whether to use mock responses for testing
        """
        self.use_mock = use_mock
        if not use_mock:
            self.openai_client = OpenAIClient(
                api_key=openai_api_key,
                model="gpt-4o-mini"  # Use same model as other services
            )
        else:
            self.openai_client = None

        logger.info("EditIntentClassifierService initialized")

    async def classify_edit_intent(self, request: EditRequest) -> EditResponse:
        """
        Classify a natural language edit request into structured operations

        Args:
            request: The edit request to classify

        Returns:
            Response with edit plan or error
        """
        try:
            logger.info(f"Classifying edit intent for generation {request.generation_id}")

            # Step 1: Call OpenAI to classify the intent
            classification_result = await self._classify_with_openai(request)

            # Step 2: Convert to EditPlan
            edit_plan = classification_result.to_edit_plan(request)

            # Step 3: Run minimal safety check
            safety_result = self._check_safety_guardrails(edit_plan, request)
            edit_plan.safety_check_passed = safety_result.passed

            if not safety_result.passed:
                logger.warning(f"Safety guardrails failed for edit request: {safety_result.issues}")

            # Step 4: Validate technical feasibility
            if not edit_plan.validate_technical_feasibility():
                return EditResponse(
                    request_id=edit_plan.request_id,
                    edit_plan=edit_plan,
                    success=False,
                    error_message="Edit plan contains technically conflicting operations",
                    can_apply_immediately=False
                )

            # Step 5: Return successful response
            return EditResponse(
                request_id=edit_plan.request_id,
                edit_plan=edit_plan,
                success=True,
                can_apply_immediately=True,
                estimated_processing_time_seconds=edit_plan.estimated_duration_seconds
            )

        except Exception as e:
            logger.error(f"Failed to classify edit intent: {str(e)}")
            return EditResponse(
                request_id=f"error_{int(datetime.utcnow().timestamp())}",
                edit_plan=EditPlan(
                    generation_id=request.generation_id,
                    request_id=f"error_{request.generation_id}",
                    natural_language_request=request.natural_language_edit,
                    interpreted_intent="Failed to interpret request",
                    operations=[],
                    confidence_score=0.0,
                    safety_check_passed=False
                ),
                success=False,
                error_message=str(e),
                can_apply_immediately=False
            )

    async def _classify_with_openai(self, request: EditRequest) -> EditClassificationResult:
        """
        Use OpenAI to classify the edit intent with tool calls

        Args:
            request: The edit request

        Returns:
            Classification result from LLM
        """
        if self.use_mock:
            # Return mock classification result
            return self._get_mock_classification_result(request)

        system_prompt = self._build_system_prompt(request)
        user_prompt = self._build_user_prompt(request)

        # Define the tool for structured output
        tools = [self._get_edit_classification_tool()]

        try:
            response = await self.openai_client.call_openai_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "classify_video_edit"}}
            )

            # Parse the tool call response
            return self._parse_tool_response(response)

        except Exception as e:
            logger.error(f"OpenAI classification failed: {str(e)}")
            raise

    def _build_system_prompt(self, request: EditRequest) -> str:
        """Build the system prompt for edit classification"""
        context_info = ""
        if request.current_clip_count:
            context_info += f"\n- Video has {request.current_clip_count} clips"
        if request.total_duration_seconds:
            context_info += f"\n- Total duration: {request.total_duration_seconds} seconds"

        return f"""You are an expert video editor that converts natural language edit requests into precise FFmpeg operations.

Your task is to analyze the user's edit request and output a structured classification using the provided tool.

IMPORTANT RULES:
1. Parse the natural language request STRICTLY through understanding - do not use any hardcoded patterns or regex
2. Output MUST be a valid tool call to the classify_video_edit function
3. Focus on the core editing intent, ignore irrelevant information, poor grammar, or filler text
4. Be robust against ambiguous or poorly worded requests - make reasonable assumptions
5. Output structured FFmpeg operations that can be executed by video processing software

CONTEXT INFORMATION:{context_info}

EDIT OPERATION TYPES:
- trim: Change duration of a clip
- crop: Crop spatial dimensions of a clip
- split: Divide a clip into multiple parts
- merge: Combine multiple clips
- reorder: Change the sequence of clips
- swap: Exchange positions of two clips
- overlay: Add text, graphics, or other elements
- timing: Adjust when things appear in the timeline
- transition: Add/modify transitions between clips
- speed: Change playback speed (slow motion, fast forward)
- volume: Adjust audio levels
- filter: Apply visual effects (blur, color correction, etc.)

TARGET TYPES:
- clip: Individual video segment
- timeline: Overall video timeline
- audio: Audio track
- visual: Visual elements
- transition: Transitions between clips"""

    def _build_user_prompt(self, request: EditRequest) -> str:
        """Build the user prompt for edit classification"""
        return f"""Please analyze this video edit request and classify it into structured FFmpeg operations:

"{request.natural_language_edit}"

Focus on the core editing intent and output the classification using the provided tool."""

    def _get_edit_classification_tool(self) -> Dict[str, Any]:
        """Get the tool definition for edit classification"""
        return {
            "type": "function",
            "function": {
                "name": "classify_video_edit",
                "description": "Classify a natural language video edit request into structured FFmpeg operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "intent_summary": {
                            "type": "string",
                            "description": "Brief summary of what the user wants to achieve"
                        },
                        "operations": {
                            "type": "array",
                            "description": "List of FFmpeg operations to perform",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "operation_type": {
                                        "type": "string",
                                        "enum": [op.value for op in EditOperation],
                                        "description": "Type of edit operation"
                                    },
                                    "target_type": {
                                        "type": "string",
                                        "enum": [target.value for target in EditTarget],
                                        "description": "What is being edited"
                                    },
                                    "target_clips": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "description": "Clip indices affected (0-based)",
                                        "default": []
                                    },
                                    "target_time_range": {
                                        "type": "object",
                                        "properties": {
                                            "start": {"type": "number"},
                                            "end": {"type": "number"}
                                        },
                                        "description": "Time range affected in seconds"
                                    },
                                    "parameters": {
                                        "type": "object",
                                        "description": "Operation-specific parameters",
                                        "additionalProperties": True
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Human-readable description of the operation"
                                    },
                                    "priority": {
                                        "type": "integer",
                                        "minimum": 0,
                                        "maximum": 10,
                                        "description": "Execution priority (higher = execute first)",
                                        "default": 1
                                    }
                                },
                                "required": ["operation_type", "target_type", "description"]
                            }
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence score in the classification"
                        },
                        "safety_concerns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Any safety concerns identified",
                            "default": []
                        }
                    },
                    "required": ["intent_summary", "operations", "confidence"]
                }
            }
        }

    def _parse_tool_response(self, openai_response: Dict[str, Any]) -> EditClassificationResult:
        """
        Parse the OpenAI tool call response into a classification result

        Args:
            openai_response: Raw OpenAI API response

        Returns:
            Parsed classification result
        """
        try:
            # Extract tool call from response
            if "choices" in openai_response and openai_response["choices"]:
                choice = openai_response["choices"][0]
                if "message" in choice and "tool_calls" in choice["message"]:
                    tool_call = choice["message"]["tool_calls"][0]
                    if tool_call["function"]["name"] == "classify_video_edit":
                        # Parse the function arguments
                        args_str = tool_call["function"]["arguments"]
                        args = json.loads(args_str)

                        return EditClassificationResult(**args)

            # Fallback for mock responses or direct responses
            if "classification" in openai_response:
                return EditClassificationResult(**openai_response["classification"])

            # Last resort - try to parse the whole response
            return EditClassificationResult(**openai_response)

        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {str(e)}")
            logger.error(f"Raw response: {openai_response}")
            raise ValueError(f"Could not parse OpenAI response: {str(e)}")

    def _check_safety_guardrails(self, edit_plan: EditPlan, request: EditRequest) -> SafetyGuardrailResult:
        """
        Perform minimal safety guardrail checks (technical feasibility only)

        Args:
            edit_plan: The edit plan to check
            request: Original edit request

        Returns:
            Safety check result
        """
        issues = []
        recommendations = []

        # Check 1: Empty operations
        if not edit_plan.operations:
            issues.append("No operations specified in edit plan")
            recommendations.append("Ensure the edit request contains valid editing instructions")

        # Check 2: Invalid clip indices (if we have clip count info)
        if request.current_clip_count is not None:
            max_valid_index = request.current_clip_count - 1
            for op in edit_plan.operations:
                for clip_idx in op.target_clips:
                    if clip_idx < 0 or clip_idx > max_valid_index:
                        issues.append(f"Operation targets invalid clip index: {clip_idx}")
                        recommendations.append(f"Clip indices must be between 0 and {max_valid_index}")

        # Check 3: Conflicting time ranges
        time_ranges = []
        for op in edit_plan.operations:
            if op.target_time_range:
                time_ranges.append((op.target_time_range.get("start", 0),
                                  op.target_time_range.get("end", float('inf'))))

        # Simple overlap check (can be made more sophisticated)
        for i, (start1, end1) in enumerate(time_ranges):
            for j, (start2, end2) in enumerate(time_ranges[i+1:], i+1):
                if max(start1, start2) < min(end1, end2):  # Overlap detected
                    issues.append("Multiple operations target overlapping time ranges")
                    recommendations.append("Consider sequencing operations or clarifying the edit request")

        return SafetyGuardrailResult(
            passed=len(issues) == 0,
            issues=issues,
            recommendations=recommendations
        )

    def _get_mock_classification_result(self, request: EditRequest) -> EditClassificationResult:
        """
        Generate a mock classification result for testing

        Args:
            request: The edit request

        Returns:
            Mock classification result
        """
        return EditClassificationResult(
            intent_summary=f"Mock classification for: {request.natural_language_edit}",
            operations=[],
            confidence=0.8,
            safety_concerns=[]
        )
