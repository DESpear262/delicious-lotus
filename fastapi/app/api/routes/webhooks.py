"""
Webhook endpoints for external service callbacks
Handles Replicate completion notifications
"""

import logging
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.core.logging import get_request_logger

logger = logging.getLogger(__name__)

# Create webhook router
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# Store prediction_id → generation_id/clip_id mapping
# In production, this should be Redis or database
_prediction_mapping: Dict[str, Dict[str, str]] = {}


class ReplicateWebhookPayload(BaseModel):
    """Replicate webhook payload structure"""
    id: str = Field(..., description="Replicate prediction ID")
    status: str = Field(..., description="Prediction status: succeeded, failed, cancelled")
    output: Optional[Any] = Field(None, description="Output data (video URL or dict)")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="When prediction was created")
    completed_at: Optional[str] = Field(None, description="When prediction completed")
    version: Optional[str] = Field(None, description="Model version used")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Generation metrics")
    logs: Optional[str] = Field(None, description="Generation logs")


def store_prediction_mapping(prediction_id: str, generation_id: str, clip_id: str, scene_id: str):
    """
    Store mapping from prediction_id to generation/clip info
    
    Args:
        prediction_id: Replicate prediction ID
        generation_id: Our generation ID
        clip_id: Our clip ID
        scene_id: Our scene ID
    """
    _prediction_mapping[prediction_id] = {
        "generation_id": generation_id,
        "clip_id": clip_id,
        "scene_id": scene_id
    }
    logger.info(f"Stored prediction mapping: {prediction_id} -> {generation_id}/{clip_id}")


def get_prediction_mapping(prediction_id: str) -> Optional[Dict[str, str]]:
    """Get mapping for a prediction_id"""
    return _prediction_mapping.get(prediction_id)


@webhook_router.post("/replicate", status_code=200)
async def replicate_webhook(
    payload: ReplicateWebhookPayload,
    request: Request
):
    """
    Handle Replicate webhook notifications for completed predictions
    
    Replicate calls this endpoint when a video generation completes (succeeds or fails).
    We process the result, download the video, upload to S3, and update the database.
    """
    logger = get_request_logger(request)
    logger.info(f"Received Replicate webhook for prediction {payload.id}, status: {payload.status}")
    
    # Get mapping for this prediction
    mapping = get_prediction_mapping(payload.id)
    if not mapping:
        logger.warning(f"No mapping found for prediction {payload.id}, ignoring webhook")
        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "reason": "unknown_prediction"}
        )
    
    generation_id = mapping["generation_id"]
    clip_id = mapping["clip_id"]
    scene_id = mapping["scene_id"]
    
    try:
        # Import services (lazy import to avoid circular dependencies)
        from app.services.storage import StorageService
        from app.services.generation_storage import GenerationStorageService
        from app.core.config import settings
        
        storage_service = None
        generation_storage_service = None
        
        # Initialize storage service if available
        try:
            storage_service = StorageService(
                use_local=settings.use_local_storage,
                local_storage_path=settings.local_storage_path,
                s3_bucket=settings.s3_bucket,
                aws_region=settings.aws_region
            )
        except Exception as e:
            logger.warning(f"StorageService not available: {e}")
        
        # Initialize generation storage service if available
        try:
            if settings.database_url:
                generation_storage_service = GenerationStorageService(database_url=settings.database_url)
        except Exception as e:
            logger.warning(f"GenerationStorageService not available: {e}")
        
        # Process based on status
        if payload.status == "succeeded":
            # Extract video URL from output
            video_url = None
            if isinstance(payload.output, str):
                video_url = payload.output
            elif isinstance(payload.output, dict):
                video_url = payload.output.get("video") or payload.output.get("url")
            
            if not video_url:
                logger.error(f"No video URL in successful webhook payload for {payload.id}")
                # Update generation status to failed
                if generation_storage_service:
                    try:
                        generation_storage_service.update_generation(
                            generation_id=generation_id,
                            status="failed",
                            metadata={"error": "No video URL in webhook payload"}
                        )
                    except Exception as e:
                        logger.error(f"Failed to update generation status: {e}")
                return JSONResponse(
                    status_code=200,
                    content={"status": "error", "reason": "no_video_url"}
                )
            
            # Upload video to storage
            final_url = video_url
            if storage_service:
                try:
                    object_key = f"generations/{generation_id}/clips/{clip_id}.mp4"
                    logger.info(f"Uploading video from {video_url} to storage: {object_key}")
                    final_url = storage_service.upload_from_url(
                        video_url,
                        object_key,
                        content_type="video/mp4"
                    )
                    logger.info(f"Successfully uploaded clip {clip_id} to storage: {final_url}")
                except Exception as e:
                    logger.error(f"Failed to upload video to storage: {e}")
                    # Continue with Replicate URL as fallback
            
            # Update generation metadata with completed clip
            if generation_storage_service:
                try:
                    # Get current metadata
                    generation = generation_storage_service.get_generation(generation_id)
                    if generation:
                        metadata = generation.get("metadata", {})
                        if isinstance(metadata, str):
                            import json
                            metadata = json.loads(metadata)
                        
                        # Add or update video_results
                        video_results = metadata.get("video_results", [])
                        
                        # Find existing clip result or create new one
                        clip_result = None
                        for result in video_results:
                            if result.get("clip_id") == clip_id:
                                clip_result = result
                                break
                        
                        if clip_result:
                            # Update existing
                            clip_result["video_url"] = final_url
                            clip_result["status"] = "completed"
                        else:
                            # Add new
                            video_results.append({
                                "clip_id": clip_id,
                                "scene_id": scene_id,
                                "video_url": final_url,
                                "status": "completed",
                                "prediction_id": payload.id
                            })
                        
                        metadata["video_results"] = video_results
                        
                        # Update generation
                        generation_storage_service.update_generation(
                            generation_id=generation_id,
                            metadata=metadata
                        )
                        logger.info(f"Updated generation {generation_id} with completed clip {clip_id}")
                except Exception as e:
                    logger.error(f"Failed to update generation metadata: {e}")
            
            logger.info(f"Successfully processed webhook for prediction {payload.id}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "processed",
                    "prediction_id": payload.id,
                    "generation_id": generation_id,
                    "clip_id": clip_id
                }
            )
        
        elif payload.status == "failed":
            # Handle failed generation
            error_msg = payload.error or "Unknown error"
            logger.error(f"Generation failed for prediction {payload.id}: {error_msg}")
            
            # Update generation metadata
            if generation_storage_service:
                try:
                    generation = generation_storage_service.get_generation(generation_id)
                    if generation:
                        metadata = generation.get("metadata", {})
                        if isinstance(metadata, str):
                            import json
                            metadata = json.loads(metadata)
                        
                        video_results = metadata.get("video_results", [])
                        
                        # Find and update clip result
                        clip_result = None
                        for result in video_results:
                            if result.get("clip_id") == clip_id:
                                clip_result = result
                                break
                        
                        if clip_result:
                            clip_result["status"] = "failed"
                            clip_result["error"] = error_msg
                        else:
                            video_results.append({
                                "clip_id": clip_id,
                                "scene_id": scene_id,
                                "video_url": None,
                                "status": "failed",
                                "error": error_msg,
                                "prediction_id": payload.id
                            })
                        
                        metadata["video_results"] = video_results
                        generation_storage_service.update_generation(
                            generation_id=generation_id,
                            metadata=metadata
                        )
                except Exception as e:
                    logger.error(f"Failed to update failed generation: {e}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "processed",
                    "prediction_id": payload.id,
                    "generation_id": generation_id,
                    "clip_id": clip_id,
                    "error": error_msg
                }
            )
        
        elif payload.status == "cancelled":
            logger.info(f"Generation cancelled for prediction {payload.id}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "processed",
                    "prediction_id": payload.id,
                    "generation_id": generation_id,
                    "clip_id": clip_id,
                    "status": "cancelled"
                }
            )
        
        else:
            # Unknown status
            logger.warning(f"Unknown status in webhook: {payload.status}")
            return JSONResponse(
                status_code=200,
                content={"status": "ignored", "reason": "unknown_status"}
            )
    
    except Exception as e:
        logger.exception(f"Error processing Replicate webhook: {e}")
        # Return 200 to prevent Replicate from retrying
        return JSONResponse(
            status_code=200,
            content={"status": "error", "error": str(e)}
        )

