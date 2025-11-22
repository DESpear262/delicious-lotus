"""
WebSocket Broadcast Helper - Convenience functions for broadcasting generation updates
"""

import logging
import json
from datetime import datetime
from typing import Optional, Any, Dict
from fastapi_app.services.websocket_manager import get_websocket_manager
from workers.redis_pool import get_redis_connection

logger = logging.getLogger(__name__)


def _publish_legacy_update(generation_id: str, payload: Dict[str, Any]) -> None:
    """
    Publish update to Redis for legacy Raw WebSocket clients (frontend compatibility)
    
    The frontend connects to /api/v1/ws/jobs which listens to Redis 'job:progress:*'
    channels. We publish to these channels to support the existing frontend implementation
    without requiring immediate changes to switch to Socket.IO.
    """
    try:
        redis_conn = get_redis_connection()
        channel = f"job:progress:{generation_id}"
        redis_conn.publish(channel, json.dumps(payload))
        logger.debug(f"Published legacy update to {channel}")
    except Exception as e:
        logger.error(f"Failed to publish legacy update for {generation_id}: {str(e)}")


async def broadcast_progress(
    generation_id: str,
    step: str,
    clip_number: int,
    total_clips: int,
    percentage: float,
    message: str
):
    """
    Broadcast a progress update for a generation
    
    Args:
        generation_id: Generation ID
        step: Current processing step
        clip_number: Current clip number (0-indexed)
        total_clips: Total number of clips
        percentage: Progress percentage (0-100)
        message: Human-readable status message
    """
    try:
        # 1. Emit to Socket.IO clients (new path)
        ws_manager = get_websocket_manager()
        await ws_manager.emit_progress(
            generation_id=generation_id,
            step=step,
            clip_number=clip_number,
            total_clips=total_clips,
            percentage=percentage,
            message=message
        )
        
        # 2. Publish to Redis for Raw WebSocket clients (legacy path)
        _publish_legacy_update(generation_id, {
            "event": "job.processing",
            "jobId": generation_id,
            "jobType": "ai_generation",
            "status": "running",  # Map 'processing' to 'running' for frontend
            "progress": percentage,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to broadcast progress for {generation_id}: {str(e)}", exc_info=True)


async def broadcast_clip_completed(
    generation_id: str,
    clip_id: str,
    thumbnail_url: str,
    duration: float
):
    """
    Broadcast a clip completed event for a generation
    
    Args:
        generation_id: Generation ID
        clip_id: Completed clip ID
        thumbnail_url: Thumbnail URL for the clip
        duration: Clip duration in seconds
    """
    try:
        # 1. Emit to Socket.IO clients
        ws_manager = get_websocket_manager()
        await ws_manager.emit_clip_completed(
            generation_id=generation_id,
            clip_id=clip_id,
            thumbnail_url=thumbnail_url,
            duration=duration
        )
        
        # 2. Publish to Redis (legacy)
        # Note: Frontend doesn't have specific handler for individual clips yet,
        # but we can send a progress update
        _publish_legacy_update(generation_id, {
            "event": "job.clip_completed",
            "jobId": generation_id,
            "jobType": "ai_generation",
            "status": "running",
            "message": f"Clip {clip_id} completed",
            "clip_id": clip_id,
            "thumbnail_url": thumbnail_url,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to broadcast clip_completed for {generation_id}: {str(e)}", exc_info=True)


async def broadcast_status_change(
    generation_id: str,
    old_status: str,
    new_status: str,
    message: str
):
    """
    Broadcast a status change event for a generation
    
    Args:
        generation_id: Generation ID
        old_status: Previous status
        new_status: New status
        message: Status change message
    """
    try:
        # 1. Emit to Socket.IO clients
        ws_manager = get_websocket_manager()
        await ws_manager.emit_status_change(
            generation_id=generation_id,
            old_status=old_status,
            new_status=new_status,
            message=message
        )
        
        # 2. Publish to Redis (legacy)
        # Map status to what frontend expects
        frontend_status = new_status
        if new_status == "processing":
            frontend_status = "running"
        elif new_status == "completed":
            frontend_status = "succeeded"
        elif new_status == "cancelled":
            frontend_status = "canceled"
            
        _publish_legacy_update(generation_id, {
            "event": f"job.{frontend_status}",
            "jobId": generation_id,
            "jobType": "ai_generation",
            "status": frontend_status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to broadcast status_change for {generation_id}: {str(e)}", exc_info=True)


async def broadcast_completed(
    generation_id: str,
    video_url: str,
    thumbnail_url: str,
    duration: float
):
    """
    Broadcast a completion event for a generation
    
    Args:
        generation_id: Generation ID
        video_url: URL of the completed video
        thumbnail_url: Thumbnail URL
        duration: Video duration in seconds
    """
    try:
        # 1. Emit to Socket.IO clients
        ws_manager = get_websocket_manager()
        await ws_manager.emit_completed(
            generation_id=generation_id,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration=duration
        )
        
        # 2. Publish to Redis (legacy)
        _publish_legacy_update(generation_id, {
            "event": "job.succeeded",
            "jobId": generation_id,
            "jobType": "ai_generation",
            "status": "succeeded",
            "progress": 100,
            "message": "Generation completed successfully",
            "result": {
                "url": video_url,
                "video": video_url,
                "thumbnail": thumbnail_url,
                "duration": duration
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to broadcast completed for {generation_id}: {str(e)}", exc_info=True)


async def broadcast_error(
    generation_id: str,
    code: str,
    message: str,
    recoverable: bool = False
):
    """
    Broadcast an error event for a generation
    
    Args:
        generation_id: Generation ID
        code: Error code
        message: Error message
        recoverable: Whether the error is recoverable
    """
    try:
        # 1. Emit to Socket.IO clients
        ws_manager = get_websocket_manager()
        await ws_manager.emit_error(
            generation_id=generation_id,
            code=code,
            message=message,
            recoverable=recoverable
        )
        
        # 2. Publish to Redis (legacy)
        _publish_legacy_update(generation_id, {
            "event": "job.failed",
            "jobId": generation_id,
            "jobType": "ai_generation",
            "status": "failed",
            "error": message,
            "code": code,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to broadcast error for {generation_id}: {str(e)}", exc_info=True)
