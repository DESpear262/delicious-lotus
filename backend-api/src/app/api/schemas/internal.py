"""Pydantic schemas for internal API endpoints."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ProcessingOperation(str, Enum):
    """Supported clip processing operations."""

    NORMALIZE = "normalize"
    RESIZE = "resize"
    CONVERT_CODEC = "convert_codec"
    EXTRACT_THUMBNAIL = "extract_thumbnail"
    NORMALIZE_AUDIO = "normalize_audio"


class ResolutionPreset(str, Enum):
    """Standard resolution presets."""

    SD_480P = "480p"
    HD_720P = "720p"
    HD_1080P = "1080p"
    UHD_4K = "4k"


class ProcessingOptions(BaseModel):
    """Options for clip processing operations."""

    # Resolution settings
    target_resolution: ResolutionPreset | None = Field(
        default=ResolutionPreset.HD_720P,
        description="Target resolution for normalization (default: 720p)",
    )
    maintain_aspect_ratio: bool = Field(
        default=True,
        description="Maintain original aspect ratio when resizing",
    )

    # Codec settings
    video_codec: str = Field(
        default="libx264",
        description="Target video codec (default: libx264)",
    )
    audio_codec: str = Field(
        default="aac",
        description="Target audio codec (default: aac)",
    )

    # Quality settings
    video_bitrate: str | None = Field(
        default=None,
        description="Target video bitrate (e.g., '2M', '5M'). If not specified, uses CRF",
    )
    audio_bitrate: str = Field(
        default="128k",
        description="Target audio bitrate (default: 128k)",
    )
    crf: int = Field(
        default=23,
        ge=0,
        le=51,
        description="Constant Rate Factor for video quality (0-51, lower is better, default: 23)",
    )

    # Frame rate settings
    target_fps: int | None = Field(
        default=30,
        ge=1,
        le=120,
        description="Target frame rate (default: 30fps)",
    )

    # Thumbnail settings
    generate_thumbnails: bool = Field(
        default=True,
        description="Generate thumbnails from processed clips",
    )
    thumbnail_timestamp: float = Field(
        default=1.0,
        ge=0,
        description="Timestamp (in seconds) for thumbnail extraction (default: 1.0)",
    )
    thumbnail_sizes: list[str] = Field(
        default_factory=lambda: ["small", "medium", "large"],
        description="Thumbnail sizes to generate (small: 320x180, medium: 640x360, large: 1280x720)",
    )


class ClipToProcess(BaseModel):
    """Single clip to be processed."""

    url: Annotated[HttpUrl, Field(description="URL of the clip to process")]
    clip_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique identifier for this clip from AI Backend",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Optional metadata to associate with this clip",
    )


class ProcessClipsRequest(BaseModel):
    """Request body for processing clips."""

    clips: list[ClipToProcess] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of clips to process (1-100 clips per request)",
    )
    callback_url: Annotated[
        HttpUrl,
        Field(description="URL to call when processing completes"),
    ]
    processing_options: ProcessingOptions = Field(
        default_factory=ProcessingOptions,
        description="Options for processing operations",
    )
    operations: list[ProcessingOperation] = Field(
        default_factory=lambda: [ProcessingOperation.NORMALIZE],
        description="List of processing operations to perform",
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Processing priority (1=lowest, 10=highest, default=5)",
    )

    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, v: HttpUrl) -> HttpUrl:
        """Validate callback URL is properly formatted.

        Args:
            v: Callback URL to validate

        Returns:
            HttpUrl: Validated URL

        Raises:
            ValueError: If URL is invalid
        """
        # Convert to string for validation
        url_str = str(v)

        # Callback URL must use http or https
        if not url_str.startswith(("http://", "https://")):
            raise ValueError("Callback URL must use http or https protocol")

        # Don't allow localhost/127.0.0.1 in production (security concern)
        # This check can be disabled in development mode
        # if "localhost" in url_str or "127.0.0.1" in url_str:
        #     raise ValueError("Callback URL cannot use localhost")

        return v


class ProcessingJobStatus(str, Enum):
    """Status of a processing job."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingJobInfo(BaseModel):
    """Information about a processing job."""

    job_id: str = Field(..., description="Unique job ID")
    clip_id: str = Field(..., description="Clip ID from request")
    status: ProcessingJobStatus = Field(..., description="Current job status")
    queued_at: str = Field(..., description="ISO 8601 timestamp when job was queued")


class ProcessClipsResponse(BaseModel):
    """Response from process-clips endpoint."""

    request_id: str = Field(..., description="Unique request ID for tracking")
    jobs: list[ProcessingJobInfo] = Field(
        ...,
        description="List of created processing jobs",
    )
    total_clips: int = Field(..., description="Total number of clips submitted")
    message: str = Field(
        default="Clips queued for processing",
        description="Human-readable status message",
    )


class ProcessingResult(BaseModel):
    """Result of processing a single clip (sent in callback)."""

    clip_id: str = Field(..., description="Original clip ID")
    status: ProcessingJobStatus = Field(..., description="Processing status")
    processed_url: str | None = Field(
        default=None,
        description="URL of processed clip (if successful)",
    )
    thumbnails: dict[str, str] = Field(
        default_factory=dict,
        description="Map of thumbnail size to URL (e.g., {'small': 'url', 'medium': 'url'})",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Processing metadata (duration, resolution, etc.)",
    )
    error: str | None = Field(
        default=None,
        description="Error message if processing failed",
    )


class ProcessingCallback(BaseModel):
    """Callback payload sent to AI Backend when processing completes."""

    request_id: str = Field(..., description="Original request ID")
    completed_at: str = Field(..., description="ISO 8601 timestamp when processing completed")
    results: list[ProcessingResult] = Field(
        ...,
        description="Results for each processed clip",
    )
    total_successful: int = Field(
        ...,
        description="Number of successfully processed clips",
    )
    total_failed: int = Field(
        ...,
        description="Number of failed clips",
    )
