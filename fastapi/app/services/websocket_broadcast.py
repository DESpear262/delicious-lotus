"""
WebSocket Broadcast Helper - Convenience functions for broadcasting generation updates
"""

import logging
from typing import Optional
from app.services.websocket_manager import get_websocket_manager

logger = logging.getLogger(__name__)


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
        ws_manager = get_websocket_manager()
        await ws_manager.emit_progress(
            generation_id=generation_id,
            step=step,
            clip_number=clip_number,
            total_clips=total_clips,
            percentage=percentage,
            message=message
        )
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
        ws_manager = get_websocket_manager()
        await ws_manager.emit_clip_completed(
            generation_id=generation_id,
            clip_id=clip_id,
            thumbnail_url=thumbnail_url,
            duration=duration
        )
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
        ws_manager = get_websocket_manager()
        await ws_manager.emit_status_change(
            generation_id=generation_id,
            old_status=old_status,
            new_status=new_status,
            message=message
        )
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
        ws_manager = get_websocket_manager()
        await ws_manager.emit_completed(
            generation_id=generation_id,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration=duration
        )
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
        ws_manager = get_websocket_manager()
        await ws_manager.emit_error(
            generation_id=generation_id,
            code=code,
            message=message,
            recoverable=recoverable
        )
    except Exception as e:
        logger.error(f"Failed to broadcast error for {generation_id}: {str(e)}", exc_info=True)

