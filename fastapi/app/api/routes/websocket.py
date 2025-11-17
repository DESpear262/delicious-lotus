"""
WebSocket Routes - Socket.io endpoints for real-time generation updates
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.websocket_manager import get_websocket_manager
from app.api.routes.v1 import generation_storage_service
from app.core.errors import NotFoundError

logger = logging.getLogger(__name__)

# Create WebSocket router
websocket_router = APIRouter()

# Get WebSocket manager
ws_manager = get_websocket_manager()
sio = ws_manager.get_sio()


@sio.event
async def connect(sid, environ, auth):
    """
    Handle Socket.io connection
    
    Note: This is called for ALL connections. We'll validate the generation
    in the custom connect handler below.
    """
    logger.debug(f"Socket.io connection attempt from {sid}")


@sio.event
async def disconnect(sid):
    """Handle Socket.io disconnection"""
    await ws_manager.disconnect(sid)
    logger.debug(f"Socket.io disconnection from {sid}")


@sio.on("connect")
async def handle_connect(sid, environ, auth):
    """
    Handle Socket.io connection and extract generation_id
    
    The frontend connects with path: '/ws/generations/{generation_id}'
    We need to extract the generation_id from the connection request.
    Socket.io passes the path in the environ dict.
    """
    logger.info(f"[WEBSOCKET_CONNECT] New connection attempt from {sid}")
    try:
        # The frontend uses: io(url, { path: '/ws/generations/{generation_id}' })
        # This path is available in the connection request
        # We need to extract it from the HTTP request path
        
        # Get the full request path
        path_info = environ.get("PATH_INFO", "")
        query_string = environ.get("QUERY_STRING", "")
        
        # Try to extract generation_id from path
        # Path format: /ws/generations/{generation_id} or /socket.io/...
        generation_id = None
        
        # Check if path contains /generations/
        if "/generations/" in path_info:
            parts = path_info.split("/generations/")
            if len(parts) > 1:
                generation_id = parts[1].split("/")[0].split("?")[0]
        
        # Also check query string as fallback
        if not generation_id and query_string:
            params = dict(param.split("=") for param in query_string.split("&") if "=" in param)
            generation_id = params.get("generation_id")
        
        # If still not found, check the referer or other headers
        if not generation_id:
            # Try to get from custom header if frontend sends it
            referer = environ.get("HTTP_REFERER", "")
            if "/generations/" in referer:
                parts = referer.split("/generations/")
                if len(parts) > 1:
                    generation_id = parts[1].split("/")[0].split("?")[0]
        
        if not generation_id:
            logger.warning(f"Could not extract generation_id from connection. Path: {path_info}, Query: {query_string}")
            # Allow connection but log warning - frontend can send generation_id in a message
            return True
        
        # Validate generation exists
        if generation_storage_service:
            generation = generation_storage_service.get_generation(generation_id)
            if not generation:
                logger.warning(f"Generation not found: {generation_id}")
                # Still allow connection - let frontend handle 404s via polling
                # return False
        else:
            # If storage service not available, allow connection but log warning
            logger.warning("Generation storage service not available, allowing connection without validation")
        
        # Register connection
        logger.info(f"[WEBSOCKET_CONNECT] Registering connection {sid} for generation {generation_id}")
        await ws_manager.connect(sid, generation_id)
        
        # Send initial connection confirmation
        logger.info(f"[WEBSOCKET_CONNECT] Sending connection confirmation to {sid}")
        await sio.emit("connected", {"generation_id": generation_id, "status": "connected"}, room=sid)
        
        logger.info(f"[WEBSOCKET_CONNECT] WebSocket connected successfully: {sid} -> generation {generation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error handling WebSocket connection: {str(e)}", exc_info=True)
        # Allow connection even on error - let the client handle it
        return True


@sio.on("disconnect")
async def handle_disconnect(sid):
    """Handle disconnection"""
    logger.info(f"[WEBSOCKET_DISCONNECT] Disconnecting {sid}")
    await ws_manager.disconnect(sid)
    logger.info(f"[WEBSOCKET_DISCONNECT] Successfully disconnected {sid}")


@sio.on("ping")
async def handle_ping(sid, data=None):
    """Handle ping for heartbeat"""
    await sio.emit("pong", {"timestamp": None}, room=sid)


@sio.on("subscribe")
async def handle_subscribe(sid, data):
    """
    Handle subscription message from client
    
    Allows clients to subscribe to a generation after connecting.
    This is useful if generation_id couldn't be extracted from the connection.
    
    Expected data: {"generation_id": "gen_123"}
    """
    try:
        if not isinstance(data, dict):
            await sio.emit("error", {"message": "Invalid subscription data"}, room=sid)
            return
        
        generation_id = data.get("generation_id")
        if not generation_id:
            await sio.emit("error", {"message": "generation_id is required"}, room=sid)
            return
        
        # Validate generation exists
        if generation_storage_service:
            generation = generation_storage_service.get_generation(generation_id)
            if not generation:
                await sio.emit("error", {"message": f"Generation not found: {generation_id}"}, room=sid)
                return
        
        # Register connection
        await ws_manager.connect(sid, generation_id)
        
        # Send confirmation
        await sio.emit("subscribed", {"generation_id": generation_id, "status": "subscribed"}, room=sid)
        
        logger.info(f"Client {sid} subscribed to generation {generation_id}")
        
    except Exception as e:
        logger.error(f"Error handling subscription: {str(e)}", exc_info=True)
        await sio.emit("error", {"message": f"Subscription failed: {str(e)}"}, room=sid)


@websocket_router.get("/ws/generations/{generation_id}/status")
async def get_generation_websocket_status(generation_id: str):
    """
    Get WebSocket connection status for a generation
    
    Returns the number of active WebSocket connections for the generation.
    This is useful for debugging and monitoring.
    """
    connection_count = ws_manager.get_connection_count(generation_id)
    return {
        "generation_id": generation_id,
        "active_connections": connection_count,
        "has_connections": connection_count > 0
    }

