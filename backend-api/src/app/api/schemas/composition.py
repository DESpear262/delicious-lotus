"""Pydantic schemas for composition API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class VideoFormat(str, Enum):
    """Supported video formats."""

    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"


class VideoResolution(str, Enum):
    """Supported video resolutions."""

    SD_480P = "480p"
    HD_720P = "720p"
    FULL_HD_1080P = "1080p"
    UHD_4K = "4k"


class OverlayPosition(str, Enum):
    """Supported overlay positions."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class ProcessingStage(str, Enum):
    """Processing stages for composition."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    RENDERING = "rendering"
    ENCODING = "encoding"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class ClipConfig(BaseModel):
    """Configuration for a single video clip in the composition."""

    video_url: HttpUrl = Field(..., description="URL of the video file to include")
    start_time: float = Field(
        ..., ge=0, description="Start time in the composition timeline (seconds)"
    )
    end_time: float = Field(..., gt=0, description="End time in the composition timeline (seconds)")
    trim_start: float = Field(
        default=0, ge=0, description="Trim from start of source video (seconds)"
    )
    trim_end: float | None = Field(
        default=None,
        ge=0,
        description="Trim from end of source video (seconds), None for full video",
    )

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, end_time: float, info) -> float:
        """Validate end_time is after start_time."""
        if "start_time" in info.data and end_time <= info.data["start_time"]:
            raise ValueError("end_time must be greater than start_time")
        return end_time

    @field_validator("trim_end")
    @classmethod
    def validate_trim_end(cls, trim_end: float | None, info) -> float | None:
        """Validate trim_end is after trim_start if provided."""
        if (
            trim_end is not None
            and "trim_start" in info.data
            and trim_end <= info.data["trim_start"]
        ):
            raise ValueError("trim_end must be greater than trim_start")
        return trim_end

    @property
    def duration(self) -> float:
        """Calculate clip duration in the composition."""
        return self.end_time - self.start_time


class AudioConfig(BaseModel):
    """Audio configuration for the composition."""

    music_url: HttpUrl | None = Field(default=None, description="URL of background music file")
    voiceover_url: HttpUrl | None = Field(default=None, description="URL of voiceover audio file")
    music_volume: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Background music volume (0.0 to 1.0)"
    )
    voiceover_volume: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Voiceover volume (0.0 to 1.0)"
    )
    original_audio_volume: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Original video audio volume (0.0 to 1.0)"
    )


class OverlayConfig(BaseModel):
    """Configuration for text/image overlays."""

    text: str = Field(..., min_length=1, max_length=500, description="Text to overlay on video")
    position: OverlayPosition = Field(
        default=OverlayPosition.BOTTOM_CENTER, description="Overlay position"
    )
    start_time: float = Field(default=0, ge=0, description="When overlay appears (seconds)")
    end_time: float | None = Field(
        default=None,
        ge=0,
        description="When overlay disappears (seconds), None for entire duration",
    )
    font_size: int = Field(default=24, ge=8, le=144, description="Font size in pixels")
    font_color: str = Field(
        default="#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$", description="Font color in hex format"
    )

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, end_time: float | None, info) -> float | None:
        """Validate end_time is after start_time if provided."""
        if (
            end_time is not None
            and "start_time" in info.data
            and end_time <= info.data["start_time"]
        ):
            raise ValueError("end_time must be greater than start_time")
        return end_time


class OutputSettings(BaseModel):
    """Output video settings."""

    resolution: VideoResolution = Field(
        default=VideoResolution.HD_720P, description="Output video resolution"
    )
    format: VideoFormat = Field(default=VideoFormat.MP4, description="Output video format")
    fps: int = Field(default=30, ge=24, le=60, description="Frames per second")
    bitrate: str | None = Field(
        default=None,
        pattern=r"^\d+[kKmM]$",
        description="Video bitrate (e.g., '2000k', '5M')",
    )


class CompositionCreateRequest(BaseModel):
    """Request model for creating a new video composition."""

    title: str = Field(..., min_length=1, max_length=255, description="Composition title")
    description: str | None = Field(
        default=None, max_length=2000, description="Optional composition description"
    )
    clips: list[ClipConfig] = Field(
        ..., min_items=1, max_items=20, description="Video clips to compose"
    )
    audio: AudioConfig = Field(default_factory=AudioConfig, description="Audio configuration")
    overlays: list[OverlayConfig] = Field(
        default_factory=list, max_items=10, description="Text overlays to apply"
    )
    output: OutputSettings = Field(
        default_factory=OutputSettings, description="Output video settings"
    )

    @model_validator(mode="after")
    def validate_timeline_consistency(self) -> "CompositionCreateRequest":
        """Validate that clips don't overlap and total duration doesn't exceed 3 minutes."""
        if not self.clips:
            return self

        # Sort clips by start time
        sorted_clips = sorted(self.clips, key=lambda c: c.start_time)

        # Check for overlaps
        for i in range(len(sorted_clips) - 1):
            current = sorted_clips[i]
            next_clip = sorted_clips[i + 1]
            if current.end_time > next_clip.start_time:
                raise ValueError(
                    f"Clips overlap: clip ending at {current.end_time}s "
                    f"overlaps with clip starting at {next_clip.start_time}s"
                )

        # Check total duration (3 minutes = 180 seconds)
        total_duration = max(clip.end_time for clip in self.clips)
        max_duration = 180.0  # 3 minutes in seconds

        if total_duration > max_duration:
            raise ValueError(
                f"Total composition duration ({total_duration}s) exceeds maximum allowed "
                f"duration ({max_duration}s / 3 minutes)"
            )

        # Validate overlays are within composition duration
        for overlay in self.overlays:
            if overlay.start_time > total_duration:
                raise ValueError(
                    f"Overlay start_time ({overlay.start_time}s) is beyond composition duration ({total_duration}s)"
                )
            if overlay.end_time and overlay.end_time > total_duration:
                raise ValueError(
                    f"Overlay end_time ({overlay.end_time}s) is beyond composition duration ({total_duration}s)"
                )

        return self


class CompositionResponse(BaseModel):
    """Response model for composition resource."""

    id: UUID = Field(..., description="Unique composition identifier")
    title: str = Field(..., description="Composition title")
    description: str | None = Field(None, description="Composition description")
    status: str = Field(..., description="Current processing status")
    created_at: datetime = Field(..., description="When composition was created")
    updated_at: datetime = Field(..., description="When composition was last updated")
    output_url: str | None = Field(None, description="URL to final output (when completed)")
    error_message: str | None = Field(None, description="Error message if processing failed")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProcessingStageInfo(BaseModel):
    """Information about a processing stage."""

    stage: ProcessingStage = Field(..., description="Processing stage name")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage for this stage")
    started_at: datetime | None = Field(None, description="When this stage started")
    completed_at: datetime | None = Field(None, description="When this stage completed")
    message: str | None = Field(None, description="Stage-specific status message")


class CompositionStatusResponse(BaseModel):
    """Response model for composition status endpoint."""

    id: UUID = Field(..., description="Unique composition identifier")
    status: str = Field(..., description="Current processing status")
    overall_progress: float = Field(
        ..., ge=0, le=100, description="Overall processing progress percentage"
    )
    current_stage: ProcessingStage = Field(..., description="Current processing stage")
    stages: list[ProcessingStageInfo] = Field(
        default_factory=list, description="Processing stage details"
    )
    created_at: datetime = Field(..., description="When composition was created")
    updated_at: datetime = Field(..., description="When composition was last updated")
    completed_at: datetime | None = Field(None, description="When processing completed")
    error_message: str | None = Field(None, description="Error message if processing failed")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ResourceMetrics(BaseModel):
    """Resource usage metrics for processing."""

    cpu_usage_percent: float | None = Field(None, ge=0, le=100, description="CPU usage percentage")
    memory_usage_mb: float | None = Field(None, ge=0, description="Memory usage in megabytes")
    processing_time_seconds: float | None = Field(None, ge=0, description="Total processing time")
    queue_wait_time_seconds: float | None = Field(None, ge=0, description="Time spent in queue")


class InputFileInfo(BaseModel):
    """Information about input files."""

    url: str = Field(..., description="File URL")
    format: str | None = Field(None, description="File format")
    size_bytes: int | None = Field(None, ge=0, description="File size in bytes")
    duration_seconds: float | None = Field(
        None, ge=0, description="Duration in seconds (for video/audio)"
    )


class OutputFileInfo(BaseModel):
    """Information about output file."""

    url: str = Field(..., description="Output file URL")
    format: str = Field(..., description="Output format")
    size_bytes: int | None = Field(None, ge=0, description="File size in bytes")
    duration_seconds: float | None = Field(None, ge=0, description="Duration in seconds")
    resolution: str | None = Field(None, description="Video resolution")
    bitrate: str | None = Field(None, description="Video bitrate")
    fps: int | None = Field(None, ge=0, description="Frames per second")


class CompositionMetadataResponse(BaseModel):
    """Response model for detailed composition metadata."""

    id: UUID = Field(..., description="Unique composition identifier")
    title: str = Field(..., description="Composition title")
    status: str = Field(..., description="Current processing status")

    # Original request data
    request_config: dict[str, Any] = Field(
        ..., description="Original composition request configuration"
    )

    # Processing timeline
    created_at: datetime = Field(..., description="When composition was created")
    started_processing_at: datetime | None = Field(None, description="When processing started")
    completed_at: datetime | None = Field(None, description="When processing completed")

    # Resource metrics
    resource_metrics: ResourceMetrics | None = Field(None, description="Resource usage metrics")

    # File information
    input_files: list[InputFileInfo] = Field(
        default_factory=list, description="Information about input files"
    )
    output_file: OutputFileInfo | None = Field(None, description="Information about output file")

    # Applied effects and warnings
    applied_effects: list[str] = Field(
        default_factory=list, description="List of effects and transitions applied"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Warning messages during processing"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class DownloadResponse(BaseModel):
    """Response model for composition download endpoint."""

    composition_id: UUID = Field(..., description="Composition identifier")
    download_url: str = Field(..., description="Presigned S3 URL for download")
    expires_at: datetime = Field(..., description="When the download URL expires")
    file_size_bytes: int | None = Field(None, ge=0, description="File size in bytes")
    format: str = Field(..., description="File format")
    filename: str = Field(..., description="Suggested filename for download")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CompositionListResponse(BaseModel):
    """Response model for composition list endpoint with pagination."""

    compositions: list[CompositionResponse] = Field(
        ..., description="List of compositions in current page"
    )
    total: int = Field(..., ge=0, description="Total number of compositions matching filters")
    offset: int = Field(..., ge=0, description="Pagination offset")
    limit: int = Field(..., ge=1, description="Pagination limit")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CompositionCancelResponse(BaseModel):
    """Response model for composition cancellation."""

    composition_id: UUID = Field(..., description="Cancelled composition ID")
    status: str = Field(..., description="New status (should be 'cancelled')")
    message: str = Field(..., description="Cancellation confirmation message")
    cancelled_at: datetime = Field(..., description="When composition was cancelled")


class BulkCancelResponse(BaseModel):
    """Response model for bulk composition cancellation."""

    cancelled_count: int = Field(..., ge=0, description="Number of compositions cancelled")
    failed_count: int = Field(..., ge=0, description="Number that failed to cancel")
    cancelled_ids: list[UUID] = Field(
        default_factory=list, description="IDs of successfully cancelled compositions"
    )
    failed_ids: list[UUID] = Field(
        default_factory=list, description="IDs of compositions that failed to cancel"
    )
    message: str = Field(..., description="Summary message")
