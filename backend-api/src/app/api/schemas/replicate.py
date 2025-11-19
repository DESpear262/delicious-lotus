"""Replicate API schemas for AI generation models."""

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Request Schemas
# ============================================================================


class NanoBananaRequest(BaseModel):
    """Request schema for Nano-Banana image generation model.

    The Nano-Banana model generates stylized images based on a prompt
    and optional image input.
    """

    prompt: str = Field(
        ...,
        description="Text prompt describing the desired style or modifications",
        min_length=1,
        max_length=1000,
        examples=["Make the sheets in the style of the logo. Make the scene natural."]
    )

    image_input: list[HttpUrl] | None = Field(
        default=None,
        description="Optional list of image URLs to use as input",
        max_length=10,
        examples=[["https://example.com/image1.png", "https://example.com/image2.png"]]
    )


class WanVideoI2VRequest(BaseModel):
    """Request schema for Wan Video I2V model.

    The Wan Video I2V model generates videos from text prompts and optional images.
    """

    prompt: str = Field(
        ...,
        description="Prompt for video generation",
        min_length=1,
        max_length=1000,
        examples=["A serene ocean wave crashing on the shore"]
    )

    image: HttpUrl | None = Field(
        default=None,
        description="Optional input image to generate video from",
        examples=["https://example.com/image.png"]
    )

    last_image: HttpUrl | None = Field(
        default=None,
        description="Optional last image to condition the video generation for smoother transitions",
        examples=["https://example.com/last_frame.png"]
    )

    resolution: str = Field(
        default="480p",
        description="Resolution of video: 480p or 720p",
        examples=["480p", "720p"]
    )


class WanVideoT2VRequest(BaseModel):
    """Request schema for Wan Video 2.5 T2V model.

    The Wan Video 2.5 T2V model generates videos from text prompts only (text-to-video).
    """

    prompt: str = Field(
        ...,
        description="Text prompt for video generation",
        min_length=1,
        max_length=2000,
        examples=["A majestic dragon flying through clouds at sunset"]
    )

    size: str = Field(
        default="1280*720",
        description="Video resolution and aspect ratio",
        examples=["832*480", "480*832", "1280*720", "720*1280", "1920*1080", "1080*1920"]
    )

    duration: int = Field(
        default=5,
        description="Duration of the generated video in seconds (5 or 10)",
        ge=5,
        le=10,
        examples=[5, 10]
    )


# ============================================================================
# Response Schemas (Async)
# ============================================================================


class AsyncJobResponse(BaseModel):
    """Async job response for Replicate predictions.

    Returns immediately with a job ID that can be used to track progress.
    """

    job_id: str = Field(
        ...,
        description="Unique job identifier for tracking",
        examples=["pred_abc123xyz"]
    )

    status: str = Field(
        default="queued",
        description="Initial status of the job",
        examples=["queued", "starting"]
    )

    message: str | None = Field(
        default=None,
        description="Optional status message",
        examples=["Job created successfully"]
    )


class NanoBananaResponse(BaseModel):
    """Response schema for Nano-Banana model."""

    url: str = Field(
        ...,
        description="URL of the generated output image",
        examples=["https://replicate.delivery/.../output.png"]
    )

    status: str = Field(
        default="success",
        description="Status of the generation",
        examples=["success"]
    )


class NanoBananaErrorResponse(BaseModel):
    """Error response schema for Nano-Banana model."""

    error: str = Field(
        ...,
        description="Error message describing what went wrong",
        examples=["Failed to generate image: API key not configured"]
    )

    status: str = Field(
        default="error",
        description="Status indicating an error occurred",
        examples=["error"]
    )


# ============================================================================
# Webhook Schemas
# ============================================================================


class ReplicateWebhookPayload(BaseModel):
    """Webhook payload from Replicate when a prediction completes."""

    id: str = Field(..., description="Prediction ID")
    status: str = Field(..., description="Status: succeeded, failed, canceled")
    output: list[str] | str | None = Field(None, description="Output URL(s)")
    error: str | None = Field(None, description="Error message if failed")
    logs: str | None = Field(None, description="Generation logs")
    metrics: dict | None = Field(None, description="Performance metrics")
