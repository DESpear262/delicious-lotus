"""
Recomposition Models - PR 403: Recomposition Trigger
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

from .edit_intent import EditPlan, FFmpegOperation


class RecompositionStatus(str, Enum):
    """Status of a recomposition job"""
    PENDING = "pending"
    TRIGGERED = "triggered"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ClipEditInstruction(BaseModel):
    """
    Instructions for editing a specific clip in the composition

    This represents the changes to be applied to a single clip based on timeline operations.
    """
    clip_index: int = Field(..., ge=0, description="Original index of the clip in the composition")
    new_index: Optional[int] = Field(None, description="New index after reordering (None = no change)")

    # Timing edits
    trim_start: Optional[float] = Field(None, ge=0.0, description="New start time after trimming (seconds)")
    trim_end: Optional[float] = Field(None, ge=0.0, description="New end time after trimming (seconds)")
    duration_override: Optional[float] = Field(None, gt=0.0, description="Override clip duration")

    # Content edits
    speed_multiplier: Optional[float] = Field(None, gt=0.0, description="Speed multiplier (1.0 = normal speed)")
    volume_multiplier: Optional[float] = Field(None, ge=0.0, le=2.0, description="Volume multiplier")

    # Effects
    fade_in_duration: Optional[float] = Field(None, ge=0.0, description="Fade in duration (seconds)")
    fade_out_duration: Optional[float] = Field(None, ge=0.0, description="Fade out duration (seconds)")

    @validator('trim_end')
    def validate_trim_end(cls, v, values):
        """Validate that trim_end is after trim_start"""
        if v is not None and values.get('trim_start') is not None:
            if v <= values['trim_start']:
                raise ValueError("trim_end must be greater than trim_start")
        return v


class TransitionEditInstruction(BaseModel):
    """
    Instructions for editing transitions between clips

    This represents changes to transition effects between clips.
    """
    between_clips: tuple[int, int] = Field(..., description="Indices of clips this transition is between")
    transition_type: Optional[str] = Field(None, description="New transition type (fade, crossfade, cut, etc.)")
    duration: Optional[float] = Field(None, gt=0.0, description="Transition duration in seconds")
    easing: Optional[str] = Field(None, description="Easing function for transition")


class OverlayEditInstruction(BaseModel):
    """
    Instructions for editing text/graphics overlays

    This represents changes to overlay elements.
    """
    overlay_id: str = Field(..., description="Unique ID of the overlay element")
    text_content: Optional[str] = Field(None, description="New text content")
    position: Optional[Dict[str, Union[str, int]]] = Field(None, description="New position coordinates")
    timing: Optional[Dict[str, float]] = Field(None, description="New timing (start_time, end_time)")
    style: Optional[Dict[str, Any]] = Field(None, description="New styling properties")


class UpdatedCompositionConfig(BaseModel):
    """
    Updated composition configuration after applying timeline edits

    This represents the complete configuration sent to FFmpeg for recomposition.
    """
    composition_id: str = Field(..., description="Original composition ID")
    generation_id: str = Field(..., description="Generation job this composition belongs to")

    # Basic composition settings
    target_duration: float = Field(..., gt=0.0, description="Target video duration in seconds")
    resolution: str = Field(default="1920x1080", description="Output resolution")
    frame_rate: int = Field(default=30, description="Output frame rate")

    # Clip edits
    clip_edits: List[ClipEditInstruction] = Field(default_factory=list, description="Edits to apply to individual clips")

    # Transition edits
    transition_edits: List[TransitionEditInstruction] = Field(default_factory=list, description="Edits to transitions")

    # Overlay edits
    overlay_edits: List[OverlayEditInstruction] = Field(default_factory=list, description="Edits to overlays")

    # Global settings
    audio_sync: bool = Field(default=True, description="Whether to sync audio")
    color_correction: bool = Field(default=True, description="Apply color correction")
    stabilization: bool = Field(default=False, description="Apply stabilization")

    # Original source data (for rollback)
    original_config: Dict[str, Any] = Field(..., description="Original composition config before edits")

    def get_clip_edit(self, clip_index: int) -> Optional[ClipEditInstruction]:
        """Get edit instructions for a specific clip"""
        return next((edit for edit in self.clip_edits if edit.clip_index == clip_index), None)

    def has_changes(self) -> bool:
        """Check if this config has any actual changes"""
        return bool(self.clip_edits or self.transition_edits or self.overlay_edits)


class RecompositionRecord(BaseModel):
    """
    Record of a recomposition operation

    Tracks the lifecycle of recomposition jobs for audit and rollback purposes.
    """
    recomposition_id: str = Field(..., description="Unique ID for this recomposition")
    composition_id: str = Field(..., description="Original composition being recomposed")
    generation_id: str = Field(..., description="Generation job this belongs to")

    # Edit source
    edit_plan: EditPlan = Field(..., description="The timeline edit plan that triggered this recomposition")

    # Configuration
    updated_config: UpdatedCompositionConfig = Field(..., description="Updated composition config")
    ffmpeg_job_id: Optional[str] = Field(None, description="FFmpeg backend job ID")

    # Status and timing
    status: RecompositionStatus = Field(default=RecompositionStatus.PENDING, description="Current status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When recomposition was initiated")
    triggered_at: Optional[datetime] = Field(None, description="When FFmpeg job was triggered")
    completed_at: Optional[datetime] = Field(None, description="When recomposition completed")

    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")

    # Rollback information
    can_rollback: bool = Field(default=True, description="Whether this recomposition can be rolled back")
    rollback_config: Optional[Dict[str, Any]] = Field(None, description="Config to restore original state")

    def mark_triggered(self, ffmpeg_job_id: str):
        """Mark recomposition as triggered with FFmpeg job ID"""
        self.status = RecompositionStatus.TRIGGERED
        self.ffmpeg_job_id = ffmpeg_job_id
        self.triggered_at = datetime.utcnow()

    def mark_completed(self):
        """Mark recomposition as completed"""
        self.status = RecompositionStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """Mark recomposition as failed"""
        self.status = RecompositionStatus.FAILED
        self.error_message = error_message
        self.error_details = error_details
        self.completed_at = datetime.utcnow()

    def is_successful(self) -> bool:
        """Check if recomposition was successful"""
        return self.status == RecompositionStatus.COMPLETED

    def get_duration(self) -> Optional[float]:
        """Get total duration of the recomposition operation"""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None


class RecompositionTriggerRequest(BaseModel):
    """
    Request to trigger a recomposition operation

    This is sent to the recomposition trigger service to initiate FFmpeg recomposition.
    """
    generation_id: str = Field(..., description="Generation job ID")
    composition_id: str = Field(..., description="Current composition ID")
    edit_plan: EditPlan = Field(..., description="Timeline edit plan from PR #402")

    # Optional parameters
    priority: str = Field(default="normal", description="Processing priority")
    webhook_url: Optional[str] = Field(None, description="Webhook for completion notifications")


class RecompositionTriggerResponse(BaseModel):
    """
    Response from recomposition trigger request

    Contains tracking information for the initiated recomposition.
    """
    recomposition_id: str = Field(..., description="Unique ID for tracking this recomposition")
    ffmpeg_job_id: str = Field(..., description="FFmpeg backend job ID")
    status: RecompositionStatus = Field(..., description="Initial status")
    estimated_duration_seconds: float = Field(..., description="Estimated time to complete")

    # URLs for monitoring
    status_url: str = Field(..., description="URL to check recomposition status")
    result_url: Optional[str] = Field(None, description="URL to get final result")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "recomposition_id": self.recomposition_id,
            "ffmpeg_job_id": self.ffmpeg_job_id,
            "status": self.status.value,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "status_url": self.status_url,
            "result_url": self.result_url
        }


class FFmpegJobTriggerRequest(BaseModel):
    """
    Request sent to FFmpeg backend to trigger composition

    This matches the expected API format for the FFmpeg backend service.
    """
    composition_id: str = Field(..., description="Composition ID")
    config: UpdatedCompositionConfig = Field(..., description="Composition configuration")
    priority: str = Field(default="normal", description="Job priority")
    webhook_url: Optional[str] = Field(None, description="Completion webhook URL")

    # Metadata for tracking
    generation_id: str = Field(..., description="Original generation ID")
    edit_summary: str = Field(..., description="Summary of edits applied")


class FFmpegJobTriggerResponse(BaseModel):
    """
    Response from FFmpeg backend job trigger

    Contains the job tracking information from FFmpeg service.
    """
    job_id: str = Field(..., description="FFmpeg job ID")
    status: str = Field(..., description="Job status")
    estimated_duration: float = Field(..., description="Estimated processing time")
    queue_position: Optional[int] = Field(None, description="Position in processing queue")
