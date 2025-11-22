"""
Replicate Client Models - PR 302: Replicate Model Client
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class GenerationStatus(str, Enum):
    """Status of video generation"""
    QUEUED = "queued"
    STARTING = "starting"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoResolution(str, Enum):
    """Supported video resolutions"""
    RES_480P = "480p"
    RES_720P = "720p"
    RES_1080P = "1080p"
    RES_4K = "4k"


class VideoFormat(str, Enum):
    """Supported video formats"""
    MP4 = "mp4"
    WEBM = "webm"


class ClipMetadata(BaseModel):
    """
    Metadata for a generated video clip from Replicate

    Contains all the information needed to track and use a generated video clip.
    """
    clip_id: str = Field(..., description="Unique ID for this clip")
    generation_id: str = Field(..., description="ID of the generation job this clip belongs to")
    scene_id: str = Field(..., description="ID of the scene this clip represents")

    # Video details
    video_url: str = Field(..., description="URL to the generated video file")
    duration_seconds: float = Field(..., ge=0.0, description="Actual duration of the generated video")
    resolution: VideoResolution = Field(default=VideoResolution.RES_720P, description="Video resolution")
    format: VideoFormat = Field(default=VideoFormat.MP4, description="Video format")

    # Generation metadata
    model_used: str = Field(default="google/veo-3.1-fast", description="Replicate model used for generation")
    prompt_used: str = Field(..., description="The prompt that was sent to the model")
    negative_prompt_used: Optional[str] = Field(None, description="Negative prompt used")

    # Quality and performance metrics
    generation_time_seconds: float = Field(..., ge=0.0, description="Time taken to generate the video")
    model_version: Optional[str] = Field(None, description="Specific model version used")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model-reported quality score")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When generation started")
    completed_at: Optional[datetime] = Field(None, description="When generation completed")

    # Error information (if failed)
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    error_code: Optional[str] = Field(None, description="Error code if generation failed")

    def is_successful(self) -> bool:
        """Check if the clip generation was successful"""
        return self.error_message is None and self.video_url is not None

    def get_summary(self) -> str:
        """Get a human-readable summary of the clip"""
        status = "✅ Success" if self.is_successful() else f"❌ Failed: {self.error_message or 'Unknown error'}"
        return f"Clip {self.clip_id}: {self.duration_seconds:.1f}s, {self.resolution}, {status}"


class GenerateClipRequest(BaseModel):
    """
    Request to generate a video clip using Replicate

    Contains all the parameters needed to generate a single video clip.
    """
    clip_id: str = Field(..., description="Unique ID for the clip to generate")
    generation_id: str = Field(..., description="ID of the overall generation job")
    scene_id: str = Field(..., description="ID of the scene being generated")

    # Core generation parameters
    prompt: str = Field(..., description="The prompt for video generation")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt to avoid unwanted content")

    # Video specifications
    duration_seconds: float = Field(..., ge=1.0, le=10.0, description="Target duration in seconds")
    aspect_ratio: str = Field(default="16:9", description="Video aspect ratio")
    resolution: VideoResolution = Field(default=VideoResolution.RES_720P, description="Target resolution")

    # Model configuration
    model: str = Field(default="google/veo-3.1-fast", description="Replicate model to use")
    model_version: Optional[str] = Field(None, description="Specific model version (optional)")

    # Advanced parameters
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    guidance_scale: Optional[float] = Field(None, ge=1.0, le=20.0, description="Guidance scale for prompt adherence")
    num_inference_steps: Optional[int] = Field(None, ge=1, le=100, description="Number of inference steps")

    # Webhook for async completion
    webhook_url: Optional[str] = Field(None, description="Webhook URL for completion notification")


class GenerateClipResponse(BaseModel):
    """
    Response from clip generation request

    Contains the initial response and tracking information.
    """
    clip_id: str = Field(..., description="ID of the clip being generated")
    status: GenerationStatus = Field(..., description="Current status of generation")

    # Replicate prediction ID for tracking
    prediction_id: str = Field(..., description="Replicate prediction ID for status tracking")

    # Estimated completion
    estimated_duration_seconds: float = Field(..., ge=0.0, description="Estimated time to completion")

    # URLs for status checking
    status_url: str = Field(..., description="URL to check generation status")
    logs_url: Optional[str] = Field(None, description="URL to view generation logs")

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When generation started")


class GenerationResult(BaseModel):
    """
    Final result of a video generation

    Contains the completed clip metadata and any additional information.
    """
    clip_metadata: ClipMetadata = Field(..., description="Complete metadata for the generated clip")
    prediction_details: Dict[str, Any] = Field(default_factory=dict, description="Raw prediction details from Replicate")


class ClientConfig(BaseModel):
    """Configuration for the Replicate client"""

    # Authentication
    api_token: str = Field(..., description="Replicate API token")

    # Default model settings
    default_model: str = Field(default="google/veo-3.1-fast", description="Default model to use")
    default_resolution: VideoResolution = Field(default=VideoResolution.RES_720P, description="Default resolution")

    # Retry configuration
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_backoff_factor: float = Field(default=2.0, description="Exponential backoff factor")
    retry_max_delay: float = Field(default=60.0, description="Maximum delay between retries")

    # Timeouts
    request_timeout: float = Field(default=300.0, description="Timeout for individual requests (seconds)")
    generation_timeout: float = Field(default=600.0, description="Timeout for generation completion (seconds)")

    # Webhook configuration
    webhook_base_url: Optional[str] = Field(None, description="Base URL for webhooks")
