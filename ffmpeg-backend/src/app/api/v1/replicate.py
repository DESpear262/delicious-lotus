"""Replicate API endpoints for AI video generation."""

import logging
import os

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..schemas.replicate import (
    NanoBananaErrorResponse,
    NanoBananaRequest,
    NanoBananaResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/nano-banana",
    response_model=NanoBananaResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate image with Nano-Banana model",
    description="Generate stylized image using Google's Nano-Banana model via Replicate from image inputs",
    responses={
        200: {
            "description": "Successfully generated image",
            "model": NanoBananaResponse,
        },
        400: {
            "description": "Invalid request parameters",
            "model": NanoBananaErrorResponse,
        },
        500: {
            "description": "Internal server error or Replicate API error",
            "model": NanoBananaErrorResponse,
        },
        503: {
            "description": "Replicate API key not configured",
            "model": NanoBananaErrorResponse,
        },
    },
)
async def generate_nano_banana(request_body: NanoBananaRequest) -> JSONResponse:
    """Generate image using Nano-Banana model.

    This endpoint accepts a text prompt and optional image input URLs,
    then uses the Replicate API to generate a stylized image.

    Args:
        request_body: Request containing prompt and optional image input

    Returns:
        NanoBananaResponse: Response with generated image URL

    Raises:
        HTTPException: If API key is not configured or generation fails
    """
    try:
        # Check if Replicate API key is configured
        replicate_api_key = os.getenv("REPLICATE_API_TOKEN")
        if not replicate_api_key:
            logger.error("REPLICATE_API_TOKEN environment variable not set")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Replicate API key not configured. Please set REPLICATE_API_TOKEN environment variable.",
                    "status": "error",
                },
            )

        # Import Replicate here to avoid import errors if package not installed
        try:
            import replicate
        except ImportError as e:
            logger.error(f"Failed to import Replicate package: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Replicate package not installed. Please run: pip install replicate",
                    "status": "error",
                },
            )

        logger.info(
            "Processing Nano-Banana request",
            extra={
                "prompt": request_body.prompt,
                "has_image_input": request_body.image_input is not None,
                "image_count": len(request_body.image_input) if request_body.image_input else 0,
            },
        )

        # Set API token for replicate
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_key

        # Prepare input for the model
        model_input = {
            "prompt": request_body.prompt,
        }

        # Add image input if provided
        if request_body.image_input:
            # Convert HttpUrl objects to strings
            model_input["image_input"] = [str(url) for url in request_body.image_input]

        # Run the Nano-Banana model
        try:
            output = replicate.run(
                "google/nano-banana",
                input=model_input,
            )

            # Get the output URL
            # The output is typically a string URL or a FileOutput object
            if isinstance(output, str):
                output_url = output
            elif hasattr(output, "url"):
                # If it's a file object with url attribute (not method)
                output_url = output.url if isinstance(output.url, str) else str(output.url)
            else:
                # Convert to string as fallback
                output_url = str(output)

            logger.info(
                "Nano-Banana generation successful",
                extra={
                    "output_url": output_url,
                    "prompt": request_body.prompt,
                },
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "url": output_url,
                    "status": "success",
                },
            )

        except Exception as e:
            logger.exception(
                "Replicate API call failed",
                extra={
                    "error": str(e),
                    "prompt": request_body.prompt,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": f"Failed to generate image: {str(e)}",
                    "status": "error",
                },
            )

    except Exception as e:
        logger.exception(
            "Unexpected error in Nano-Banana endpoint",
            extra={"error": str(e)},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": f"Unexpected error: {str(e)}",
                "status": "error",
            },
        )
