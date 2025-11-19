"""
Webhook endpoints for external service callbacks
Handles Replicate completion notifications
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi_app.core.logging import get_request_logger
from fastapi_app.models.schemas import GenerationStatus
from fastapi_app.services.websocket_broadcast import (
    broadcast_completed,
    broadcast_status_change,
)

logger = logging.getLogger(__name__)

# Create webhook router
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# Store prediction_id → generation_id/clip_id mapping
# In production, this should be Redis or database
_prediction_mapping: Dict[str, Dict[str, str]] = {}


def _update_in_memory_store(
    generation_id: str,
    *,
    status: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Best-effort update of the in-memory generation store that backs dev mode.
    """
    try:
        from fastapi_app.api.routes import v1  # Lazy import to avoid circular dependency
    except ImportError:
        return

    store = getattr(v1, "_generation_store", None)
    if not store or generation_id not in store:
        return

    generation = store[generation_id]
    if status is not None:
        generation["status"] = status
    if metadata is not None:
        generation["metadata"] = metadata
    generation["updated_at"] = datetime.utcnow()


async def _set_generation_status(
    generation_id: str,
    *,
    new_status: GenerationStatus,
    metadata: Optional[Dict[str, Any]],
    generation_storage_service: Optional["GenerationStorageService"],
    previous_status: str = GenerationStatus.PROCESSING.value,
    completion_payload: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Persist a terminal generation status and broadcast websocket events.
    """
    status_value = new_status.value if isinstance(new_status, GenerationStatus) else new_status

    if generation_storage_service:
        try:
            generation_storage_service.update_generation(
                generation_id=generation_id,
                status=status_value,
                metadata=metadata,
            )
        except Exception as exc:
            logger.error(f"Failed to update generation status in database: {exc}")

    _update_in_memory_store(generation_id, status=status_value, metadata=metadata)

    try:
        await broadcast_status_change(
            generation_id=generation_id,
            old_status=previous_status,
            new_status=status_value,
            message=f"Generation {new_status.value if isinstance(new_status, GenerationStatus) else new_status}",
        )
    except Exception as exc:
        logger.warning(f"Failed to broadcast status change for {generation_id}: {exc}")

    if new_status == GenerationStatus.COMPLETED:
        try:
            payload = completion_payload or {}
            await broadcast_completed(
                generation_id=generation_id,
                video_url=payload.get("video_url", ""),
                thumbnail_url=payload.get("thumbnail_url", ""),
                duration=payload.get("duration", 0.0),
            )
        except Exception as exc:
            logger.warning(f"Failed to broadcast completion event for {generation_id}: {exc}")


async def _check_and_finalize_generation(
    generation_id: str,
    *,
    metadata: Optional[Dict[str, Any]],
    generation_storage_service: Optional["GenerationStorageService"],
) -> None:
    """
    If every clip is complete, mark the generation as completed.
    """
    if not metadata:
        return

    video_results = metadata.get("video_results") if isinstance(metadata, dict) else None
    if not video_results:
        return

    total_clips = len(video_results)
    if not total_clips:
        return

    all_completed = all(result.get("status") == "completed" for result in video_results)
    if not all_completed:
        return

    # Use first completed clip to populate completion payload when possible.
    completed_clip = next((clip for clip in video_results if clip.get("status") == "completed"), None)
    completion_payload = {
        "video_url": completed_clip.get("video_url", "") if completed_clip else "",
        "thumbnail_url": completed_clip.get("thumbnail_url", "") if completed_clip else "",
        "duration": completed_clip.get("duration", 0.0) if completed_clip else 0.0,
    }

    await _set_generation_status(
        generation_id=generation_id,
        new_status=GenerationStatus.COMPLETED,
        metadata=metadata,
        generation_storage_service=generation_storage_service,
        completion_payload=completion_payload,
    )


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
    logger.warning(f"[WEBHOOK] ===== RECEIVED REPLICATE WEBHOOK =====")
    logger.warning(f"[WEBHOOK] Prediction ID: {payload.id}")
    logger.warning(f"[WEBHOOK] Status: {payload.status}")
    logger.warning(f"[WEBHOOK] Payload keys: {list(payload.dict().keys()) if hasattr(payload, 'dict') else 'N/A'}")

    # Get mapping for this prediction
    mapping = get_prediction_mapping(payload.id)
    if not mapping:
        logger.warning(f"[WEBHOOK] No mapping found for prediction {payload.id}, ignoring webhook")
        logger.warning(f"[WEBHOOK] Current mappings: {list(_prediction_mappings.keys())[:5]}...")
        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "reason": "unknown_prediction"}
        )

    generation_id = mapping["generation_id"]
    clip_id = mapping["clip_id"]
    scene_id = mapping["scene_id"]
    logger.warning(f"[WEBHOOK] Found mapping - Generation ID: {generation_id}, Clip ID: {clip_id}, Scene ID: {scene_id}")
    logger.warning(f"[WEBHOOK] ===== PROCESSING WEBHOOK PAYLOAD =====")
    logger.warning(f"[WEBHOOK] Prediction status: {payload.status}")
    if hasattr(payload, 'output') and payload.output:
        logger.warning(f"[WEBHOOK] Output available: {bool(payload.output)}")
    if hasattr(payload, 'urls') and payload.urls:
        logger.warning(f"[WEBHOOK] URLs available: {payload.urls}")

    metadata_snapshot: Optional[Dict[str, Any]] = None

    try:
        # Import services (lazy import to avoid circular dependencies)
        from fastapi_app.services.storage import StorageService
        from fastapi_app.services.generation_storage import GenerationStorageService
        from fastapi_app.core.config import settings
        
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

            logger.warning(f"[WEBHOOK] Extracted video URL: {video_url}")
            logger.warning(f"[WEBHOOK] Original Replicate URL: https://replicate.com/p/{payload.id}")

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
                    logger.warning(f"[WEBHOOK] Uploading video to storage...")
                    logger.warning(f"[WEBHOOK] Source URL: {video_url}")
                    logger.warning(f"[WEBHOOK] Storage path: {object_key}")
                    final_url = storage_service.upload_from_url(
                        video_url,
                        object_key,
                        content_type="video/mp4"
                    )
                    logger.warning(f"[WEBHOOK] Successfully uploaded clip {clip_id}")
                    logger.warning(f"[WEBHOOK] Final storage URL: {final_url}")
                except Exception as e:
                    logger.warning(f"[WEBHOOK] Failed to upload video to storage: {e}")
                    logger.warning(f"[WEBHOOK] Will use Replicate URL as fallback: {video_url}")
                    # Continue with Replicate URL as fallback
            else:
                logger.warning(f"[WEBHOOK] No storage service available, using Replicate URL: {video_url}")
            
            # Update generation metadata with completed clip
            if generation_storage_service:
                try:
                    # Get current metadata
                    generation = generation_storage_service.get_generation(generation_id)
                    if generation:
                        metadata = generation.get("metadata", {}) or {}
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
                        metadata_snapshot = metadata
                        logger.info(f"Updated generation {generation_id} with completed clip {clip_id}")
                except Exception as e:
                    logger.error(f"Failed to update generation metadata: {e}")

            if metadata_snapshot is None:
                metadata_snapshot = {"video_results": video_results}

            _update_in_memory_store(generation_id, metadata=metadata_snapshot)
            await _check_and_finalize_generation(
                generation_id=generation_id,
                metadata=metadata_snapshot,
                generation_storage_service=generation_storage_service,
            )
            
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
            metadata_snapshot = None
            if generation_storage_service:
                try:
                    generation = generation_storage_service.get_generation(generation_id)
                    if generation:
                        metadata = generation.get("metadata", {}) or {}
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
                        metadata_snapshot = metadata
                except Exception as e:
                    logger.error(f"Failed to update failed generation: {e}")

            if metadata_snapshot is None:
                metadata_snapshot = {
                    "video_results": video_results
                }

            _update_in_memory_store(generation_id, metadata=metadata_snapshot)
            await _set_generation_status(
                generation_id=generation_id,
                new_status=GenerationStatus.FAILED,
                metadata=metadata_snapshot,
                generation_storage_service=generation_storage_service,
            )
            
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
            await _set_generation_status(
                generation_id=generation_id,
                new_status=GenerationStatus.CANCELLED,
                metadata=None,
                generation_storage_service=generation_storage_service,
            )
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


@webhook_router.post("/training", status_code=200)
async def training_webhook(
    request: Request
):
    """
    Handle training webhook notifications (Placeholder)
    """
    logger = get_request_logger(request)
    logger.info("[WEBHOOK] Received training webhook (Not Implemented)")
    
    # Log payload for debugging
    try:
        payload = await request.json()
        logger.info(f"[WEBHOOK] Training payload: {payload}")
    except Exception:
        logger.warning("[WEBHOOK] Could not parse training webhook payload")

    return JSONResponse(
        status_code=200,
        content={"status": "received", "message": "Training webhook placeholder"}
    )

