"""Replicate API endpoints for AI video generation."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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


class GenerateClipsRequest(BaseModel):
    """Request model for video clip generation"""
    scenes: List[Dict[str, Any]]
    micro_prompts: List[str]
    generation_id: str
    aspect_ratio: str = "16:9"
    parallelize: bool = False
    webhook_base_url: Optional[str] = None

class GenerateClipsResponse(BaseModel):
    """Response model for video clip generation"""
    video_results: List[Dict[str, Any]]
    message: str


@router.post(
    "/generate-clips",
    response_model=GenerateClipsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate video clips",
    description="Generate video clips from micro-prompts using Replicate with webhook callbacks",
    responses={
        200: {
            "description": "Successfully started video generation",
            "model": GenerateClipsResponse,
        },
        400: {
            "description": "Invalid request parameters",
        },
        500: {
            "description": "Internal server error",
        },
    },
)
async def generate_clips_endpoint(request: GenerateClipsRequest):
    """Generate video clips endpoint that calls the generate_video_clips function"""
    # logger.warning(f"[FFMPEG_API] ===== RECEIVED GENERATE-CLIPS REQUEST =====")
    # logger.warning(f"[FFMPEG_API] Generation ID: {request.generation_id}")
    # logger.warning(f"[FFMPEG_API] Scenes count: {len(request.scenes)}")
    # logger.warning(f"[FFMPEG_API] Micro-prompts count: {len(request.micro_prompts)}")
    # logger.warning(f"[FFMPEG_API] Aspect ratio: {request.aspect_ratio}")
    # logger.warning(f"[FFMPEG_API] Parallelize: {request.parallelize}")
    # logger.warning(f"[FFMPEG_API] Webhook base URL: {request.webhook_base_url}")
    # logger.warning(f"[FFMPEG_API] REPLICATE_API_TOKEN configured: {bool(os.getenv('REPLICATE_API_TOKEN'))}")

    try:
        # logger.warning(f"[FFMPEG_API] Calling generate_video_clips function...")
        # For now, we'll call generate_video_clips without storage service
        # The storage will be handled by the webhook handler in the main FastAPI backend
        # Call the generate_video_clips function
        video_results = await generate_video_clips(
            scenes=request.scenes,
            micro_prompts=request.micro_prompts,
            generation_id=request.generation_id,
            aspect_ratio=request.aspect_ratio,
            parallelize=request.parallelize,
            use_mock=False,
            storage_service=None,  # Storage will be handled by webhook handler
            webhook_base_url=request.webhook_base_url
        )

        # logger.warning(f"[FFMPEG_API] generate_video_clips completed successfully")
        # logger.warning(f"[FFMPEG_API] Returned {len(video_results)} video results")

        response = GenerateClipsResponse(
            video_results=video_results,
            message=f"Started generation of {len(video_results)} clips"
        )
        # logger.warning(f"[FFMPEG_API] Sending response: {response.message}")
        return response

    except Exception as e:
        logger.exception(f"[FFMPEG_API] Error in generate_clips_endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video generation failed: {str(e)}"
        )


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
            if not replicate_client:
                raise RuntimeError("Replicate client not initialized")
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
    storage_service = None,
    webhook_base_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate video clips from micro-prompts using Replicate with webhook callbacks.

    This function extracts the working Replicate video generation logic
    from cli.py and makes it reusable for both CLI and FastAPI backend.

    Uses webhooks for async completion - starts generation and returns immediately.
    Replicate will call the webhook endpoint when generation completes.

    Args:
        scenes: List of scene dictionaries with 'duration' and other metadata
        micro_prompts: List of micro-prompt strings, one per scene
        generation_id: Unique ID for the generation job
        aspect_ratio: Video aspect ratio (default: "16:9")
        parallelize: If True, generate clips concurrently; if False, sequentially
        use_mock: If True, create placeholder files instead of calling Replicate
        storage_service: Storage service for uploading videos (optional)
        webhook_base_url: Base URL for webhook callbacks (e.g., https://api.example.com)

    Returns:
        List of dictionaries with 'clip_id', 'video_url', 'scene_id', 'status', and 'prediction_id'
    """
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] ===== STARTING VIDEO GENERATION =====")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Generation ID: {generation_id}")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Scenes count: {len(scenes)}")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Micro-prompts count: {len(micro_prompts)}")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Aspect ratio: {aspect_ratio}")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Parallelize: {parallelize}")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Use mock: {use_mock}")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Webhook base URL: {webhook_base_url}")

    # Simple replicate client implementation for ffmpeg-backend
    import replicate
    from pydantic import BaseModel
    from typing import Optional
    from enum import Enum

    class VideoResolution(str, Enum):
        RES_480P = "480p"
        RES_720P = "720p"
        RES_1080P = "1080p"
        RES_4K = "4k"

    class GenerateClipRequest(BaseModel):
        clip_id: str
        generation_id: str
        scene_id: str
        prompt: str
        duration_seconds: float = 5.0
        aspect_ratio: str = "16:9"
        resolution: VideoResolution = VideoResolution.RES_720P
        webhook_url: Optional[str] = None

    # Initialize Replicate client
    replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] REPLICATE_API_TOKEN configured: {bool(replicate_api_token)}")
    if not replicate_api_token and not use_mock:
        logger.error(f"[GENERATE_VIDEO_CLIPS] REPLICATE_API_TOKEN not configured and use_mock=False")
        raise ValueError("REPLICATE_API_TOKEN not configured")

    model_version = os.getenv("REPLICATE_MODEL_VERSION") or os.getenv("REPLICATE_DEFAULT_MODEL", "google/veo-3.1-fast")
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Using model: {model_version}")
    replicate_client = None
    if not use_mock and replicate_api_token:
        # logger.warning(f"[GENERATE_VIDEO_CLIPS] Initializing Replicate client...")
        replicate_client = replicate.Client(api_token=replicate_api_token)
        # logger.warning(f"[GENERATE_VIDEO_CLIPS] Replicate client initialized")

    video_results = []
    # logger.warning(f"[GENERATE_VIDEO_CLIPS] Starting clip generation loop...")
    
    async def generate_single_clip(i: int, scene: Dict[str, Any], micro_prompt: str) -> Dict[str, Any]:
        """Generate a single video clip using webhook-based async generation"""
        # logger.warning(f"[GENERATE_SINGLE_CLIP] Starting clip {i} generation")
        clip_id = f"clip_{i:03d}_{hash(micro_prompt) % 10000}"
        scene_id = f"scene_{i}"
        # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip ID: {clip_id}, Scene ID: {scene_id}")
        # logger.warning(f"[GENERATE_SINGLE_CLIP] Prompt: {micro_prompt[:100]}...")
        
        if use_mock:
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
                "status": "queued",
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
            
            print(f"[INFO] Clip {i}: prompt='{micro_prompt[:50]}...', duration={valid_duration}s, aspect_ratio={aspect_ratio}")
            
            # Build webhook URL if webhook_base_url is provided
            webhook_url = None
            if webhook_base_url:
                webhook_url = f"{webhook_base_url.rstrip('/')}/api/v1/webhooks/replicate"
                print(f"[INFO] Clip {i}: Webhook URL configured: {webhook_url}")
            else:
                print(f"[WARN] Clip {i}: No webhook URL provided - status updates may be delayed")
            
            clip_request = GenerateClipRequest(
                clip_id=clip_id,
                generation_id=generation_id,
                scene_id=scene_id,
                prompt=micro_prompt,
                duration_seconds=valid_duration,
                aspect_ratio=aspect_ratio,
                resolution=VideoResolution.RES_720P,
                webhook_url=webhook_url
            )
            
            # Start generation using Replicate predictions API (non-blocking)
            # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip {i}: Submitting to Replicate API...")
            print(f"[INFO] Clip {i}: Submitting to Replicate API...")

            replicate_input = {
                "prompt": micro_prompt,
                "duration": valid_duration,
                "aspect_ratio": aspect_ratio,
                "resolution": "720p"
            }
            logger.warning(f"[REPLICATE_INPUT] ===== SENDING TO REPLICATE =====")
            logger.warning(f"[REPLICATE_INPUT] Clip {i}: Prompt: {micro_prompt}")
            logger.warning(f"[REPLICATE_INPUT] Clip {i}: Duration: {valid_duration}")
            logger.warning(f"[REPLICATE_INPUT] Clip {i}: Aspect Ratio: {aspect_ratio}")
            logger.warning(f"[REPLICATE_INPUT] Clip {i}: Resolution: 720p")
            logger.warning(f"[REPLICATE_INPUT] Clip {i}: Model: {model_version}")
            logger.warning(f"[REPLICATE_INPUT] ===== END REPLICATE INPUT =====")

            kwargs = {}
            if webhook_url:
                kwargs["webhook"] = webhook_url
                kwargs["webhook_events_filter"] = ["completed"]
                # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip {i}: Webhook configured: {webhook_url}")
            else:
                # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip {i}: No webhook URL - generation will be synchronous!")
                pass

            # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip {i}: Calling replicate_client.predictions.create...")
            prediction = await asyncio.to_thread(
                replicate_client.predictions.create,
                version=model_version,
                input=replicate_input,
                **kwargs
            )
            # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip {i}: Replicate call completed")

            prediction_id = getattr(prediction, "id", None) or str(prediction)
            prediction_url = getattr(prediction, "urls", {}).get("get", f"https://replicate.com/p/{prediction_id}")
            # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip {i}: Prediction ID: {prediction_id}")
            # logger.warning(f"[GENERATE_SINGLE_CLIP] Clip {i}: Replicate Prediction URL: {prediction_url}")
            print(f"[INFO] Clip {i}: Started prediction with ID: {prediction_id}")
            print(f"[INFO] Clip {i}: Track progress at: {prediction_url}")

            # Return immediately with queued status
            # Webhook will update status when generation completes
            return {
                "clip_id": clip_id,
                "scene_id": scene_id,
                "video_url": None,  # Will be set by webhook handler
                "status": "queued",
                "prediction_id": prediction_id
            }
            
        except Exception as e:
            logger.error(f"Failed to start generation for clip {clip_id}: {str(e)}")
            print(f"[ERROR] Failed to start generation for clip {i} ({clip_id}): {str(e)}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
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
        print(f"[INFO] Generating {len(micro_prompts)} clips in parallel")
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
                print(f"[ERROR] Clip {i+1} generation raised exception: {result}")
                processed_results.append({
                    "clip_id": f"clip_{i+1}_error",
                    "scene_id": f"scene_{i+1}",
                    "video_url": None,
                    "status": "failed",
                    "error": str(result),
                    "prediction_id": None
                })
            else:
                status = result.get('status', 'unknown')
                clip_id = result.get('clip_id', f'clip_{i+1}')
                if status == 'queued':
                    print(f"[OK] Clip {i+1} ({clip_id}) queued for generation")
                elif status == 'failed':
                    print(f"[ERROR] Clip {i+1} ({clip_id}) failed: {result.get('error', 'Unknown error')}")
                processed_results.append(result)
        video_results = processed_results
    else:
        # Generate clips sequentially
        logger.info(f"Generating {len(micro_prompts)} clips sequentially")
        print(f"[INFO] Generating {len(micro_prompts)} clips sequentially")
        for i, (scene, micro_prompt) in enumerate(zip(scenes, micro_prompts), 1):
            print(f"[INFO] Starting generation for clip {i}/{len(micro_prompts)}")
            result = await generate_single_clip(i, scene, micro_prompt)
            status = result.get('status', 'unknown')
            clip_id = result.get('clip_id', f'clip_{i}')
            if status == 'queued':
                print(f"[OK] Clip {i} ({clip_id}) queued for generation")
            elif status == 'failed':
                print(f"[ERROR] Clip {i} ({clip_id}) failed: {result.get('error', 'Unknown error')}")
            video_results.append(result)
    
    return video_results


async def wait_for_video_completion(
    video_results: List[Dict[str, Any]],
    replicate_client: Optional[Any] = None,
    timeout_seconds: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Wait for queued video generations to complete.
    
    This function polls Replicate for completion of queued video generations
    and updates the results with completed status and video URLs.
    
    Args:
        video_results: List of result dicts from generate_video_clips with "queued" status
        replicate_client: Optional ReplicateModelClient instance (will create if not provided)
        timeout_seconds: Optional timeout per video (defaults to REPLICATE_TIMEOUT_SECONDS)
        
    Returns:
        Updated list of results with "completed" status and video_urls, or "failed" status with errors
    """
    from ai.core.replicate_client import ReplicateModelClient, ClientConfig
    
    # Create client if not provided
    if not replicate_client:
        replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
        if not replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            # Mark all as failed
            for result in video_results:
                if result.get("status") == "queued":
                    result["status"] = "failed"
                    result["error"] = "REPLICATE_API_TOKEN not configured"
            return video_results
        
        replicate_config = ClientConfig(
            api_token=replicate_api_token,
            default_model=os.getenv("REPLICATE_DEFAULT_MODEL", "google/veo-3.1-fast"),
            generation_timeout=float(os.getenv("REPLICATE_TIMEOUT_SECONDS", "300.0"))
        )
        replicate_client = ReplicateModelClient(replicate_config)
    
    # Wait for each queued result
    completed_results = []
    for i, result in enumerate(video_results, 1):
        if result.get("status") == "queued" and result.get("prediction_id"):
            prediction_id = result["prediction_id"]
            clip_id = result.get("clip_id", f"clip_{i}")
            
            logger.info(f"Waiting for {clip_id} to complete (prediction_id: {prediction_id})")
            print(f"[INFO] Waiting for scene {i} to complete (prediction_id: {prediction_id})...")
            
            try:
                # Wait for completion
                generation_result = await replicate_client.wait_for_completion(
                    prediction_id,
                    timeout_seconds=timeout_seconds
                )
                
                # Extract video URL from result (it's in clip_metadata)
                if generation_result.clip_metadata and generation_result.clip_metadata.video_url:
                    result["status"] = "completed"
                    result["video_url"] = generation_result.clip_metadata.video_url
                    logger.info(f"Scene {i} generation completed: {result['video_url']}")
                    print(f"[OK] Scene {i} generation completed")
                else:
                    result["status"] = "failed"
                    result["error"] = "No video URL in result"
                    logger.error(f"Scene {i} completed but no video URL")
                    print(f"[ERROR] Scene {i} completed but no video URL")
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
                logger.error(f"Failed to wait for scene {i} completion: {e}")
                print(f"[ERROR] Failed to wait for scene {i} completion: {e}")
        
        completed_results.append(result)
    
    return completed_results


async def generate_video_clips_with_completion(
    scenes: List[Dict[str, Any]],
    micro_prompts: List[str],
    generation_id: str,
    aspect_ratio: str = "16:9",
    parallelize: bool = False,
    use_mock: bool = False,
    storage_service = None,
    webhook_base_url: Optional[str] = None,
    wait_for_completion: bool = True,
    timeout_seconds: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Generate video clips and optionally wait for completion.
    
    This is a convenience wrapper around generate_video_clips that optionally
    waits for all generations to complete before returning.
    
    Args:
        scenes: List of scene dictionaries with 'duration' and other metadata
        micro_prompts: List of micro-prompt strings, one per scene
        generation_id: Unique ID for the generation job
        aspect_ratio: Video aspect ratio (default: "16:9")
        parallelize: If True, generate clips concurrently; if False, sequentially
        use_mock: If True, create placeholder files instead of calling Replicate
        storage_service: Storage service for uploading videos (optional)
        webhook_base_url: Base URL for webhook callbacks (e.g., https://api.example.com)
        wait_for_completion: If True, wait for all videos to complete before returning
        timeout_seconds: Optional timeout per video when waiting for completion
        
    Returns:
        List of dictionaries with 'clip_id', 'video_url', 'scene_id', 'status', and 'prediction_id'
    """
    # Generate clips (returns immediately with "queued" status)
    video_results = await generate_video_clips(
        scenes=scenes,
        micro_prompts=micro_prompts,
        generation_id=generation_id,
        aspect_ratio=aspect_ratio,
        parallelize=parallelize,
        use_mock=use_mock,
        storage_service=storage_service,
        webhook_base_url=webhook_base_url
    )
    
    # If waiting for completion, poll for results
    if wait_for_completion and not use_mock:
        video_results = await wait_for_video_completion(
            video_results,
            timeout_seconds=timeout_seconds
        )
    
    return video_results


async def build_micro_prompts_from_scenes(
    scenes: List[Dict[str, Any]],
    prompt_analysis: Dict[str, Any],
    generation_id: str,
    brand_config: Optional[Dict[str, Any]] = None,
    use_fallback: bool = True
) -> List[str]:
    """
    Build micro-prompts from scene decomposition results.
    
    This is a convenience wrapper around MicroPromptBuilderService that handles
    the service initialization and fallback logic.
    
    Args:
        scenes: List of scene dictionaries from scene decomposition
        prompt_analysis: Prompt analysis results (tone, style, etc.)
        generation_id: Unique ID for the generation job
        brand_config: Optional brand configuration
        use_fallback: If True, use simple fallback prompts if service fails
        
    Returns:
        List of micro-prompt strings, one per scene
    """
    try:
        from ai.services.micro_prompt_builder_service import MicroPromptBuilderService
        from ai.models.micro_prompt import MicroPromptRequest
        
        # Build micro-prompts using the service
        micro_prompt_request = MicroPromptRequest(
            generation_id=generation_id,
            scenes=scenes,
            prompt_analysis=prompt_analysis,
            brand_config=brand_config or {"name": "Default Brand", "colors": ["#0066CC", "#FFFFFF"]},
            enforce_brand_consistency=True,
            enforce_accessibility=True,
            harmony_threshold=0.7
        )
        
        micro_prompt_service = MicroPromptBuilderService()
        micro_prompt_response = await micro_prompt_service.build_micro_prompts(micro_prompt_request)
        micro_prompts = [mp.prompt_text for mp in micro_prompt_response.micro_prompts]
        
        logger.info(f"Generated {len(micro_prompts)} micro-prompts using MicroPromptBuilderService")
        return micro_prompts
        
    except Exception as e:
        logger.warning(f"MicroPromptBuilderService failed: {e}, using fallback")
        if not use_fallback:
            raise
        
        # Fallback to simple prompt creation
        micro_prompts = []
        for i, scene in enumerate(scenes, 1):
            scene_type = scene.get('type', scene.get('scene_type', 'development'))
            scene_desc = scene.get('description', scene.get('content_description', 'scene'))
            tone = prompt_analysis.get('tone', 'professional')
            style = prompt_analysis.get('style', 'modern')
            
            micro_prompt = (
                f"Professional {scene_type} scene: {scene_desc}. "
                f"High-quality production, {style} style, {tone} tone."
            )
            micro_prompts.append(micro_prompt)
        
        logger.info(f"Generated {len(micro_prompts)} micro-prompts using fallback method")
        return micro_prompts


async def download_and_save_videos(
    video_results: List[Dict[str, Any]],
    micro_prompts: List[str],
    output_directory: Path,
    create_error_files: bool = True
) -> List[str]:
    """
    Download completed videos and save them to disk.
    
    Args:
        video_results: List of result dicts from generate_video_clips_with_completion
        micro_prompts: List of micro-prompt strings (for error file content)
        output_directory: Directory to save videos to
        create_error_files: If True, create placeholder files for failed generations
        
    Returns:
        List of local file paths to the saved videos
    """
    import requests
    
    # Ensure output directory exists
    output_directory.mkdir(parents=True, exist_ok=True)
    
    video_paths = []
    
    for i, result in enumerate(video_results, 1):
        if result.get("status") == "completed" and result.get("video_url"):
            video_url = result["video_url"]
            
            # If it's a mock URL, create placeholder file
            if video_url.startswith("mock://"):
                scene_filename = f"scene_{i}_{hash(micro_prompts[i-1]) % 10000}.mp4"
                scene_path = output_directory / scene_filename
                
                with open(scene_path, 'wb') as f:
                    f.write(b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41mp42iso5dash')
                    content = f"GENERATED_MICRO_PROMPT: {micro_prompts[i-1]}".encode()[:500]
                    f.write(content)
                    f.write(b'\x00' * (100 - len(content) if len(content) < 100 else 0))
                
                video_paths.append(str(scene_path))
                logger.info(f"Created mock video file: {scene_path}")
                print(f"[MOCK] Scene {i} placeholder video created")
            else:
                # Download and save the video
                scene_filename = f"scene_{i}_{hash(micro_prompts[i-1]) % 10000}.mp4"
                scene_path = output_directory / scene_filename
                
                try:
                    logger.info(f"Downloading video from {video_url}...")
                    print(f"   Downloading video from {video_url}...")
                    video_response = requests.get(video_url, timeout=60)
                    video_response.raise_for_status()
                    
                    with open(scene_path, 'wb') as f:
                        f.write(video_response.content)
                    
                    video_paths.append(str(scene_path))
                    logger.info(f"Video downloaded and saved: {scene_path} ({len(video_response.content)} bytes)")
                    print(f"[OK] Scene {i} video downloaded and saved ({len(video_response.content)} bytes)")
                except Exception as e:
                    logger.error(f"Failed to download video for scene {i}: {e}")
                    if create_error_files:
                        # Create error placeholder
                        with open(scene_path, 'wb') as f:
                            f.write(b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41mp42iso5dash')
                            content = f"[ERROR] Download failed: {str(e)} | URL: {video_url}".encode()[:500]
                            f.write(content)
                        video_paths.append(str(scene_path))
                        print(f"[ERROR] Failed to download scene {i}, created error file")
                    else:
                        video_paths.append(None)
        else:
            # Handle error case
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Failed to generate scene {i}: {error_msg}")
            print(f"[ERROR] Failed to generate scene {i}: {error_msg}")
            
            if create_error_files:
                scene_filename = f"scene_{i}_{hash(micro_prompts[i-1]) % 10000}.mp4"
                scene_path = output_directory / scene_filename
                
                with open(scene_path, 'wb') as f:
                    f.write(b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41mp42iso5dash')
                    content = f"[ERROR] Generation failed: {error_msg} | MICRO_PROMPT: {micro_prompts[i-1][:200]}".encode()
                    f.write(content)
                
                video_paths.append(str(scene_path))
            else:
                video_paths.append(None)
    
    return video_paths