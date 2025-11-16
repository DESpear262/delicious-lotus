"""Replicate API schemas for Nano-Banana model."""

from pydantic import BaseModel, Field, HttpUrl


class NanoBananaRequest(BaseModel):
    """Request schema for Nano-Banana model.

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
