"""Replicate API endpoints for AI video generation."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..schemas.replicate import (
    NanoBananaErrorResponse,
    NanoBananaRequest,
    NanoBananaResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Add ai package to path for imports
_ai_package_path = Path(__file__).parent.parent.parent.parent.parent / "ai"
if str(_ai_package_path) not in sys.path:
    sys.path.insert(0, str(_ai_package_path))


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


# Video Generation Service Functions
async def generate_video_clips(
    scenes: List[Dict[str, Any]],
    micro_prompts: List[str],
    generation_id: str,
    aspect_ratio: str = "16:9",
    parallelize: bool = False,
    use_mock: bool = False,
    storage_service = None
) -> List[Dict[str, Any]]:
    """
    Generate video clips from micro-prompts using Replicate.
    
    This function extracts the working Replicate video generation logic
    from cli.py and makes it reusable for both CLI and FastAPI backend.
    
    Args:
        scenes: List of scene dictionaries with 'duration' and other metadata
        micro_prompts: List of micro-prompt strings, one per scene
        generation_id: Unique ID for the generation job
        aspect_ratio: Video aspect ratio (default: "16:9")
        parallelize: If True, generate clips concurrently; if False, sequentially
        use_mock: If True, create placeholder files instead of calling Replicate
        
    Returns:
        List of dictionaries with 'clip_id', 'video_url', 'scene_id', and 'status'
    """
    try:
        from ai.core.replicate_client import ReplicateModelClient, ClientConfig
        from ai.models.replicate_client import GenerateClipRequest, VideoResolution
    except ImportError as e:
        logger.error(f"Failed to import Replicate client: {e}")
        raise ImportError(f"Replicate client not available: {e}")
    
    # Initialize Replicate client
    replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_api_token and not use_mock:
        raise ValueError("REPLICATE_API_TOKEN not configured")
    
    replicate_client = None
    if not use_mock and replicate_api_token:
        replicate_config = ClientConfig(
            api_token=replicate_api_token,
            default_model=os.getenv("REPLICATE_DEFAULT_MODEL", "google/veo-3.1-fast"),
            generation_timeout=float(os.getenv("REPLICATE_TIMEOUT_SECONDS", "300.0"))
        )
        replicate_client = ReplicateModelClient(replicate_config)
    
    video_results = []
    
    async def generate_single_clip(i: int, scene: Dict[str, Any], micro_prompt: str) -> Dict[str, Any]:
        """Generate a single video clip and upload to storage"""
        clip_id = f"clip_{i:03d}_{hash(micro_prompt) % 10000}"
        scene_id = f"scene_{i}"
        
        if use_mock or not replicate_client:
            # Create placeholder file
            mock_url = f"mock://{clip_id}.mp4"
            if storage_service:
                # For mock, create a temporary placeholder file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                    tmp_file.write(b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41mp42iso5dash')
                    tmp_file.write(f"MOCK_CLIP:{clip_id}".encode())
                    tmp_path = tmp_file.name
                
                try:
                    object_key = f"generations/{generation_id}/clips/{clip_id}.mp4"
                    storage_url = storage_service.upload_file(tmp_path, object_key, content_type="video/mp4")
                    os.unlink(tmp_path)  # Clean up temp file
                    mock_url = storage_url
                except Exception as e:
                    logger.warning(f"Failed to upload mock clip to storage: {e}")
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            return {
                "clip_id": clip_id,
                "scene_id": scene_id,
                "video_url": mock_url,
                "status": "completed",
                "prediction_id": None
            }
        
        try:
            # Map duration to valid values for wan-video model (4, 6, or 8 seconds)
            duration = min(float(scene.get("duration", 5.0)), 10.0)
            if duration <= 5:
                valid_duration = 4
            elif duration <= 7:
                valid_duration = 6
            else:
                valid_duration = 8
            
            clip_request = GenerateClipRequest(
                clip_id=clip_id,
                generation_id=generation_id,
                scene_id=scene_id,
                prompt=micro_prompt,
                duration_seconds=valid_duration,
                aspect_ratio=aspect_ratio,
                resolution=VideoResolution.RES_720P
            )
            
            # Start generation
            response = await replicate_client.generate_clip(clip_request)
            
            # Wait for completion
            generation_result = await replicate_client.wait_for_completion(
                response.prediction_id,
                timeout_seconds=300.0
            )
            
            replicate_url = generation_result.clip_metadata.video_url
            
            # Upload to storage if storage_service is provided
            final_url = replicate_url
            if storage_service and replicate_url:
                try:
                    object_key = f"generations/{generation_id}/clips/{clip_id}.mp4"
                    # Download from Replicate and upload to storage
                    final_url = storage_service.upload_from_url(
                        replicate_url,
                        object_key,
                        content_type="video/mp4"
                    )
                    logger.info(f"Uploaded clip {clip_id} to storage: {final_url}")
                except Exception as e:
                    logger.error(f"Failed to upload clip {clip_id} to storage: {str(e)}")
                    # Fallback to Replicate URL if storage upload fails
                    final_url = replicate_url
            
            return {
                "clip_id": clip_id,
                "scene_id": scene_id,
                "video_url": final_url,
                "status": "completed",
                "prediction_id": response.prediction_id
            }
            
        except Exception as e:
            logger.error(f"Failed to generate clip {clip_id}: {str(e)}")
            return {
                "clip_id": clip_id,
                "scene_id": scene_id,
                "video_url": None,
                "status": "failed",
                "error": str(e),
                "prediction_id": None
            }
    
    # Generate clips either in parallel or sequentially
    if parallelize:
        # Generate all clips concurrently
        logger.info(f"Generating {len(micro_prompts)} clips in parallel")
        tasks = [
            generate_single_clip(i + 1, scene, micro_prompt)
            for i, (scene, micro_prompt) in enumerate(zip(scenes, micro_prompts))
        ]
        video_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(video_results):
            if isinstance(result, Exception):
                logger.error(f"Clip {i+1} generation raised exception: {result}")
                processed_results.append({
                    "clip_id": f"clip_{i+1}_error",
                    "scene_id": f"scene_{i+1}",
                    "video_url": None,
                    "status": "failed",
                    "error": str(result),
                    "prediction_id": None
                })
            else:
                processed_results.append(result)
        video_results = processed_results
    else:
        # Generate clips sequentially
        logger.info(f"Generating {len(micro_prompts)} clips sequentially")
        for i, (scene, micro_prompt) in enumerate(zip(scenes, micro_prompts), 1):
            result = await generate_single_clip(i, scene, micro_prompt)
            video_results.append(result)
    
    return video_results
