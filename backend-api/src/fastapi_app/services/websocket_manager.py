"""
WebSocket Manager - Manages Socket.io connections and broadcasts generation updates
"""

import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
import socketio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages Socket.io connections for generation progress updates.
    
    Handles connection lifecycle, room management, and event broadcasting.
    """
    
    def __init__(self):
        """Initialize the WebSocket manager with Socket.io server"""
        # Create Socket.io server with async support
        # Note: The frontend uses path: '/ws/generations/{generation_id}'
        # Socket.io's path option is the server mount point (default: '/socket.io/')
        # We'll use the default path and handle generation_id extraction in the connect handler
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",  # Configure via settings in production
            async_mode='asgi',
            logger=False,  # We'll use our own logging
            engineio_logger=False
        )
        
        # Track connections by generation_id: set of session IDs
        self._connections: Dict[str, Set[str]] = {}
        
        # Track session to generation mapping
        self._session_to_generation: Dict[str, str] = {}
        
        logger.info("WebSocketManager initialized")
    
    def get_sio(self) -> socketio.AsyncServer:
        """Get the Socket.io server instance"""
        return self.sio
    
    async def connect(self, sid: str, generation_id: str):
        """
        Register a new connection for a generation
        
        Args:
            sid: Socket.io session ID
            generation_id: Generation ID to subscribe to
        """
        if generation_id not in self._connections:
            self._connections[generation_id] = set()
        
        self._connections[generation_id].add(sid)
        self._session_to_generation[sid] = generation_id
        
        # Join the room for this generation
        room_name = f"generation:{generation_id}"
        await self.sio.enter_room(sid, room_name)
        
        logger.info(f"Client {sid} connected to generation {generation_id} (room: {room_name})")
    
    async def disconnect(self, sid: str):
        """
        Unregister a connection
        
        Args:
            sid: Socket.io session ID
        """
        generation_id = self._session_to_generation.get(sid)
        if generation_id:
            if generation_id in self._connections:
                self._connections[generation_id].discard(sid)
                if not self._connections[generation_id]:
                    del self._connections[generation_id]
            
            del self._session_to_generation[sid]
            await self.sio.leave_room(sid, f"generation:{generation_id}")
            
            logger.info(f"Client {sid} disconnected from generation {generation_id}")
    
    async def emit_progress(
        self,
        generation_id: str,
        step: str,
        clip_number: int,
        total_clips: int,
        percentage: float,
        message: str
    ):
        """
        Emit a progress update event
        
        Args:
            generation_id: Generation ID
            step: Current processing step
            clip_number: Current clip number (0-indexed)
            total_clips: Total number of clips
            percentage: Progress percentage (0-100)
            message: Human-readable status message
        """
        event_data = {
            "step": step,
            "clip_number": clip_number,
            "total_clips": total_clips,
            "percentage": percentage,
            "message": message
        }
        
        room_name = f"generation:{generation_id}"
        await self.sio.emit(
            "progress",
            event_data,
            room=room_name
        )
        
        logger.debug(f"Emitted progress event for {generation_id}: {percentage}%")
    
    async def emit_clip_completed(
        self,
        generation_id: str,
        clip_id: str,
        thumbnail_url: str,
        duration: float
    ):
        """
        Emit a clip completed event
        
        Args:
            generation_id: Generation ID
            clip_id: Completed clip ID
            thumbnail_url: Thumbnail URL for the clip
            duration: Clip duration in seconds
        """
        event_data = {
            "clip_id": clip_id,
            "thumbnail_url": thumbnail_url,
            "duration": duration
        }
        
        await self.sio.emit(
            "clip_completed",
            event_data,
            room=f"generation:{generation_id}"
        )
        
        logger.info(f"Emitted clip_completed event for {generation_id}: {clip_id}")
    
    async def emit_status_change(
        self,
        generation_id: str,
        old_status: str,
        new_status: str,
        message: str
    ):
        """
        Emit a status change event
        
        Args:
            generation_id: Generation ID
            old_status: Previous status
            new_status: New status
            message: Status change message
        """
        event_data = {
            "old_status": old_status,
            "new_status": new_status,
            "message": message
        }
        
        await self.sio.emit(
            "status_change",
            event_data,
            room=f"generation:{generation_id}"
        )
        
        logger.info(f"Emitted status_change event for {generation_id}: {old_status} -> {new_status}")
    
    async def emit_completed(
        self,
        generation_id: str,
        video_url: str,
        thumbnail_url: str,
        duration: float
    ):
        """
        Emit a completion event
        
        Args:
            generation_id: Generation ID
            video_url: URL of the completed video
            thumbnail_url: Thumbnail URL
            duration: Video duration in seconds
        """
        event_data = {
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "duration": duration
        }
        
        await self.sio.emit(
            "completed",
            event_data,
            room=f"generation:{generation_id}"
        )
        
        logger.info(f"Emitted completed event for {generation_id}")
    
    async def emit_error(
        self,
        generation_id: str,
        code: str,
        message: str,
        recoverable: bool = False
    ):
        """
        Emit an error event
        
        Args:
            generation_id: Generation ID
            code: Error code
            message: Error message
            recoverable: Whether the error is recoverable
        """
        event_data = {
            "code": code,
            "message": message,
            "recoverable": recoverable
        }
        
        await self.sio.emit(
            "error",
            event_data,
            room=f"generation:{generation_id}"
        )
        
        logger.warning(f"Emitted error event for {generation_id}: {code} - {message}")
    
    def get_connection_count(self, generation_id: str) -> int:
        """
        Get the number of active connections for a generation
        
        Args:
            generation_id: Generation ID
            
        Returns:
            Number of active connections
        """
        return len(self._connections.get(generation_id, set()))
    
    def has_connections(self, generation_id: str) -> bool:
        """
        Check if there are any active connections for a generation
        
        Args:
            generation_id: Generation ID
            
        Returns:
            True if there are active connections
        """
        return generation_id in self._connections and len(self._connections[generation_id]) > 0


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create the global WebSocket manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager

