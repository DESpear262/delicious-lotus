"""
Replicate Model Client - PR 302: Replicate Model Client
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import replicate
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models.replicate_client import (
    ClientConfig,
    GenerateClipRequest,
    GenerateClipResponse,
    GenerationResult,
    ClipMetadata,
    GenerationStatus,
    VideoResolution,
    VideoFormat
)

logger = logging.getLogger(__name__)


class ReplicateModelClient:
    """
    Async client wrapper for Replicate video generation models

    Handles video clip generation with retry logic, progress tracking,
    and comprehensive error handling.
    """

    def __init__(self, config: ClientConfig):
        """
        Initialize the Replicate client

        Args:
            config: Client configuration with API credentials and settings
        """
        self.config = config

        # Initialize Replicate client
        self.client = replicate.Client(api_token=config.api_token)

        logger.info(f"ReplicateModelClient initialized with model: {config.default_model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((replicate.exceptions.ReplicateError, Exception))
    )
    async def generate_clip(self, request: GenerateClipRequest) -> GenerateClipResponse:
        """
        Generate a video clip using Replicate

        Args:
            request: Generation request with prompt and parameters

        Returns:
            Response with generation tracking information

        Raises:
            Exception: If generation fails after retries
        """
        try:
            logger.info(f"Starting video generation for clip {request.clip_id}")

            # Prepare model inputs
            model_inputs = self._prepare_model_inputs(request)

            # Start prediction asynchronously
            prediction = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.predictions.create(
                    version=request.model,
                    input=model_inputs,
                    webhook=request.webhook_url
                )
            )

            # Calculate estimated duration based on typical generation times
            estimated_duration = self._estimate_generation_time(request)

            # Create response
            response = GenerateClipResponse(
                clip_id=request.clip_id,
                status=GenerationStatus.QUEUED,
                prediction_id=prediction.id,
                estimated_duration_seconds=estimated_duration,
                status_url=f"https://replicate.com/p/{prediction.id}",
                logs_url=f"https://replicate.com/p/{prediction.id}/logs" if hasattr(prediction, 'logs_url') else None,
                started_at=datetime.utcnow()
            )

            logger.info(f"Video generation started for clip {request.clip_id}, prediction ID: {prediction.id}")
            return response

        except replicate.exceptions.ReplicateError as e:
            logger.error(f"Replicate API error for clip {request.clip_id}: {e}")
            raise Exception(f"Replicate API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating clip {request.clip_id}: {e}")
            raise Exception(f"Video generation failed: {str(e)}")

    async def get_generation_status(self, prediction_id: str) -> Dict[str, Any]:
        """
        Get the status of a running generation

        Args:
            prediction_id: Replicate prediction ID

        Returns:
            Status information from Replicate
        """
        try:
            prediction = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.predictions.get(prediction_id)
            )

            return {
                "status": prediction.status,
                "output": prediction.output,
                "error": prediction.error,
                "logs": prediction.logs,
                "created_at": prediction.created_at,
                "completed_at": prediction.completed_at
            }

        except Exception as e:
            logger.error(f"Error checking status for prediction {prediction_id}: {e}")
            raise Exception(f"Failed to get generation status: {str(e)}")

    async def wait_for_completion(
        self,
        prediction_id: str,
        timeout_seconds: Optional[float] = None
    ) -> GenerationResult:
        """
        Wait for a generation to complete and return the result

        Args:
            prediction_id: Replicate prediction ID
            timeout_seconds: Maximum time to wait (defaults to config timeout)

        Returns:
            Complete generation result with metadata

        Raises:
            TimeoutError: If generation takes too long
            Exception: If generation fails
        """
        timeout = timeout_seconds or self.config.generation_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status_info = await self.get_generation_status(prediction_id)

                if status_info["status"] == "succeeded":
                    # Parse successful result
                    return await self._parse_successful_result(prediction_id, status_info)

                elif status_info["status"] == "failed":
                    # Handle failure
                    error_msg = status_info.get("error", "Unknown error")
                    raise Exception(f"Generation failed: {error_msg}")

                elif status_info["status"] == "cancelled":
                    raise Exception("Generation was cancelled")

                # Still processing, wait and check again
                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"Error during generation wait for {prediction_id}: {e}")
                raise

        # Timeout
        raise TimeoutError(f"Generation timed out after {timeout} seconds")

    def _prepare_model_inputs(self, request: GenerateClipRequest) -> Dict[str, Any]:
        """
        Prepare inputs for the Replicate model

        Args:
            request: Generation request

        Returns:
            Model input parameters
        """
        inputs = {
            "prompt": request.prompt,
            "duration": request.duration_seconds,
            "aspect_ratio": request.aspect_ratio,
        }

        # Add optional parameters
        if request.negative_prompt:
            inputs["negative_prompt"] = request.negative_prompt

        if request.seed is not None:
            inputs["seed"] = request.seed

        if request.guidance_scale is not None:
            inputs["guidance_scale"] = request.guidance_scale

        if request.num_inference_steps is not None:
            inputs["num_inference_steps"] = request.num_inference_steps

        # Add resolution-specific parameters
        if request.resolution == VideoResolution.RES_480P:
            inputs["width"] = 854
            inputs["height"] = 480
        elif request.resolution == VideoResolution.RES_720P:
            inputs["width"] = 1280
            inputs["height"] = 720
        elif request.resolution == VideoResolution.RES_1080P:
            inputs["width"] = 1920
            inputs["height"] = 1080
        elif request.resolution == VideoResolution.RES_4K:
            inputs["width"] = 3840
            inputs["height"] = 2160

        return inputs

    def _estimate_generation_time(self, request: GenerateClipRequest) -> float:
        """
        Estimate generation time based on request parameters

        Args:
            request: Generation request

        Returns:
            Estimated time in seconds
        """
        # Base time for google/veo-3.1-fast
        base_time = 45.0  # seconds

        # Adjust for duration (longer videos take more time)
        duration_multiplier = request.duration_seconds / 5.0  # normalized to 5 seconds

        # Adjust for resolution (higher resolution = more time)
        resolution_multiplier = 1.0
        if request.resolution == VideoResolution.RES_1080P:
            resolution_multiplier = 1.5
        elif request.resolution == VideoResolution.RES_4K:
            resolution_multiplier = 2.5

        return base_time * duration_multiplier * resolution_multiplier

    async def _parse_successful_result(
        self,
        prediction_id: str,
        status_info: Dict[str, Any]
    ) -> GenerationResult:
        """
        Parse a successful generation result into structured metadata

        Args:
            prediction_id: Replicate prediction ID
            status_info: Raw status information from Replicate

        Returns:
            Structured generation result
        """
        output = status_info.get("output", {})

        # Extract video URL
        video_url = output.get("video")
        if not video_url:
            raise Exception("No video URL in successful generation output")

        # Create clip metadata
        metadata = ClipMetadata(
            clip_id=f"clip_{prediction_id}",  # Will be overridden by caller
            generation_id="",  # Will be overridden by caller
            scene_id="",  # Will be overridden by caller
            video_url=video_url,
            duration_seconds=output.get("duration", 0.0),
            resolution=self._parse_resolution_from_output(output),
            format=VideoFormat.MP4,  # Default assumption
            model_used=status_info.get("version", self.config.default_model),
            prompt_used="",  # Will be overridden by caller
            generation_time_seconds=self._calculate_generation_time(status_info),
            completed_at=datetime.utcnow()
        )

        # Add quality score if available
        if "quality_score" in output:
            metadata.quality_score = output["quality_score"]

        return GenerationResult(
            clip_metadata=metadata,
            prediction_details=status_info
        )

    def _parse_resolution_from_output(self, output: Dict[str, Any]) -> VideoResolution:
        """Parse resolution from Replicate output"""
        width = output.get("width", 1280)
        height = output.get("height", 720)

        if width >= 3840 or height >= 2160:
            return VideoResolution.RES_4K
        elif width >= 1920 or height >= 1080:
            return VideoResolution.RES_1080P
        elif width >= 1280 or height >= 720:
            return VideoResolution.RES_720P
        else:
            return VideoResolution.RES_480P

    def _calculate_generation_time(self, status_info: Dict[str, Any]) -> float:
        """Calculate actual generation time from timestamps"""
        try:
            created = datetime.fromisoformat(status_info["created_at"].replace('Z', '+00:00'))
            completed = datetime.fromisoformat(status_info["completed_at"].replace('Z', '+00:00'))
            return (completed - created).total_seconds()
        except:
            # Fallback to default estimate
            return 60.0

    async def cancel_generation(self, prediction_id: str) -> bool:
        """
        Cancel a running generation

        Args:
            prediction_id: Replicate prediction ID

        Returns:
            True if cancelled successfully
        """
        try:
            prediction = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.predictions.cancel(prediction_id)
            )
            logger.info(f"Cancelled generation {prediction_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel generation {prediction_id}: {e}")
            return False
