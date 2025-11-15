"""
Edit Intent Models - PR 401: Edit Intent Classifier (OpenAI)
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class EditOperation(str, Enum):
    """Types of edit operations that can be performed on video clips"""
    TRIM = "trim"           # Trim clip duration
    CROP = "crop"           # Crop clip spatially
    SPLIT = "split"         # Split clip into multiple parts
    MERGE = "merge"         # Merge clips together
    REORDER = "reorder"     # Change clip order in timeline
    SWAP = "swap"           # Swap two clips
    OVERLAY = "overlay"     # Add overlay elements
    TIMING = "timing"       # Adjust timing/duration
    TRANSITION = "transition"  # Add/modify transitions
    SPEED = "speed"         # Change playback speed
    VOLUME = "volume"       # Adjust audio volume
    FILTER = "filter"       # Apply visual filters


class EditTarget(str, Enum):
    """What the edit operation targets"""
    CLIP = "clip"           # Individual clip
    TIMELINE = "timeline"   # Overall timeline
    AUDIO = "audio"         # Audio track
    VISUAL = "visual"       # Visual elements
    TRANSITION = "transition"  # Transitions between clips


class FFmpegOperation(BaseModel):
    """
    Structured FFmpeg operation that can be executed by the video processing backend

    This represents the actual command that will be sent to FFmpeg to perform the edit.
    """
    operation_type: EditOperation = Field(..., description="Type of edit operation")
    target_type: EditTarget = Field(..., description="What is being edited")

    # Target specification
    target_clips: List[int] = Field(default_factory=list, description="Clip indices affected (0-based)")
    target_time_range: Optional[Dict[str, float]] = Field(None, description="Time range affected (start/end in seconds)")

    # Operation parameters
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")

    # Metadata
    description: str = Field(..., description="Human-readable description of the operation")
    priority: int = Field(default=1, ge=0, le=10, description="Execution priority (higher = execute first)")

    def to_ffmpeg_command(self) -> Dict[str, Any]:
        """
        Convert to FFmpeg-compatible command format

        Returns:
            Dictionary that can be serialized and sent to FFmpeg backend
        """
        return {
            "operation": self.operation_type.value,
            "target": self.target_type.value,
            "clips": self.target_clips,
            "time_range": self.target_time_range,
            "parameters": self.parameters,
            "description": self.description,
            "priority": self.priority
        }


class EditPlan(BaseModel):
    """
    Complete plan for editing a video based on natural language input

    Contains all the FFmpeg operations needed to execute the requested edits.
    """
    generation_id: str = Field(..., description="ID of the original generation being edited")
    request_id: str = Field(..., description="ID of this edit request")

    # Original request
    natural_language_request: str = Field(..., description="The original natural language edit request")
    interpreted_intent: str = Field(..., description="LLM's interpretation of the intent")

    # Operations to execute
    operations: List[FFmpegOperation] = Field(default_factory=list, description="FFmpeg operations to perform")

    # Metadata
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the interpretation")
    safety_check_passed: bool = Field(default=True, description="Whether safety guardrails passed")
    estimated_duration_seconds: float = Field(..., description="Estimated time to execute all operations")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the edit plan was created")
    applied_at: Optional[datetime] = Field(None, description="When the edit was applied")

    def get_operations_by_priority(self) -> List[FFmpegOperation]:
        """Get operations sorted by priority (highest first)"""
        return sorted(self.operations, key=lambda op: op.priority, reverse=True)

    def validate_technical_feasibility(self) -> bool:
        """
        Basic technical feasibility check

        Returns:
            True if operations appear technically feasible
        """
        # Check for conflicting operations on same clips
        clip_usage = {}
        for op in self.operations:
            for clip_idx in op.target_clips:
                if clip_idx in clip_usage:
                    # Multiple operations on same clip - check for conflicts
                    existing_ops = clip_usage[clip_idx]
                    for existing_op in existing_ops:
                        if self._operations_conflict(op, existing_op):
                            return False
                else:
                    clip_usage[clip_idx] = []
                clip_usage[clip_idx].append(op)

        return True

    def _operations_conflict(self, op1: FFmpegOperation, op2: FFmpegOperation) -> bool:
        """Check if two operations conflict when applied to the same clip"""
        # Simple conflict detection - can be expanded
        conflicting_pairs = [
            (EditOperation.TRIM, EditOperation.SPLIT),
            (EditOperation.SPLIT, EditOperation.MERGE),
            (EditOperation.MERGE, EditOperation.SPLIT),
        ]

        op_pair = (op1.operation_type, op2.operation_type)
        reverse_pair = (op2.operation_type, op1.operation_type)

        return op_pair in conflicting_pairs or reverse_pair in conflicting_pairs


class EditRequest(BaseModel):
    """
    Request to classify and plan a natural language edit
    """
    generation_id: str = Field(..., description="ID of the generation to edit")
    natural_language_edit: str = Field(..., description="Natural language description of the desired edit")

    # Optional context
    current_clip_count: Optional[int] = Field(None, description="Current number of clips in the video")
    total_duration_seconds: Optional[float] = Field(None, description="Current total duration")

    # Execution options
    apply_immediately: bool = Field(default=False, description="Whether to apply the edit immediately")


class EditResponse(BaseModel):
    """
    Response from edit intent classification
    """
    request_id: str = Field(..., description="Unique ID for this edit request")
    edit_plan: EditPlan = Field(..., description="The generated edit plan")

    # Status
    success: bool = Field(default=True, description="Whether classification was successful")
    error_message: Optional[str] = Field(None, description="Error message if classification failed")

    # Execution info
    can_apply_immediately: bool = Field(default=True, description="Whether the edit can be applied immediately")
    estimated_processing_time_seconds: Optional[float] = Field(None, description="Estimated time to process")


class EditClassificationResult(BaseModel):
    """
    Internal result from LLM classification before conversion to EditPlan
    """
    intent_summary: str = Field(..., description="Summary of the user's intent")
    operations: List[Dict[str, Any]] = Field(..., description="Raw operations from LLM tool calls")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    safety_concerns: List[str] = Field(default_factory=list, description="Any safety concerns identified")

    def to_edit_plan(self, request: EditRequest) -> EditPlan:
        """Convert classification result to EditPlan"""
        operations = []
        for op_data in self.operations:
            try:
                operation = FFmpegOperation(**op_data)
                operations.append(operation)
            except Exception as e:
                # Log invalid operation but continue
                print(f"Invalid operation data: {op_data}, error: {e}")
                continue

        return EditPlan(
            generation_id=request.generation_id,
            request_id=f"edit_{request.generation_id}_{int(datetime.utcnow().timestamp())}",
            natural_language_request=request.natural_language_edit,
            interpreted_intent=self.intent_summary,
            operations=operations,
            confidence_score=self.confidence,
            safety_check_passed=len(self.safety_concerns) == 0,
            estimated_duration_seconds=len(operations) * 5.0  # Rough estimate: 5s per operation
        )


class SafetyGuardrailResult(BaseModel):
    """
    Result of safety guardrail checks
    """
    passed: bool = Field(default=True, description="Whether all guardrails passed")
    issues: List[str] = Field(default_factory=list, description="Specific issues found")
    recommendations: List[str] = Field(default_factory=list, description="Suggested fixes")

    def __bool__(self) -> bool:
        return self.passed
