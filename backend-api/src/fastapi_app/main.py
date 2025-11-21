"""
Main FastAPI application
Block 0: API Skeleton & Core Infrastructure
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import socketio

from fastapi_app.core.config import settings
from fastapi_app.core.logging import RequestIDMiddleware, setup_logging, get_request_logger
from fastapi_app.core.errors import global_exception_handler
from fastapi_app.models.schemas import DetailedHealthResponse
from fastapi_app.api.routes.v1 import api_v1_router
from fastapi_app.api.routes.internal_v1 import internal_v1_router
from fastapi_app.api.routes.webhooks import webhook_router
from fastapi_app.api.routes.websocket import websocket_router, sio
from fastapi_app.services.websocket_manager import get_websocket_manager


# Create FastAPI application
app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version
)

# Register global exception handler immediately
app.add_exception_handler(Exception, global_exception_handler)

# Register API routers immediately (not in lifespan)
app.include_router(api_v1_router)
app.include_router(internal_v1_router)
app.include_router(webhook_router)
app.include_router(websocket_router)

# Mount Socket.io ASGI app for WebSocket support
# This wraps the FastAPI app to handle Socket.io connections
# The Socket.io server will handle /socket.io/* paths, and FastAPI handles everything else
socketio_app = socketio.ASGIApp(sio, app)

# Mount static files for frontend (Option B deployment)
# Check if frontend/dist directory exists before mounting
# In Docker container, frontend is at /app/frontend/dist
# For local dev, check parent.parent (repo root) / frontend-app / dist
FRONTEND_DIST_PATH = Path("/app/frontend/dist") if os.path.exists("/app/frontend/dist") else Path(__file__).parent.parent.parent.parent / "frontend-app" / "dist"
FRONTEND_ASSETS_PATH = FRONTEND_DIST_PATH / "assets"
FRONTEND_INDEX_PATH = FRONTEND_DIST_PATH / "index.html"

# Only set up frontend serving if index.html exists (frontend is built)
if FRONTEND_INDEX_PATH.exists() and FRONTEND_INDEX_PATH.is_file():
    # Mount assets directory if it exists
    if FRONTEND_ASSETS_PATH.exists() and FRONTEND_ASSETS_PATH.is_dir():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_PATH)), name="static-assets")

    # Serve index.html for SPA routing (catch-all for non-API routes)
    # NOTE: This catch-all route MUST be defined after all API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve frontend SPA, with fallback to index.html for client-side routing"""
        # Skip API routes and health checks (they're already handled)
        if full_path.startswith("api/") or full_path.startswith("health") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve the requested file
        file_path = FRONTEND_DIST_PATH / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        # Fallback to index.html for SPA routing
        return FileResponse(FRONTEND_INDEX_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown hooks"""

    # Startup
    logger = logging.getLogger("app")
    logger.info("Starting AI Video Generation Pipeline API")
    logger.info("API routers registered")

    # Initialize WebSocket manager
    ws_manager = get_websocket_manager()
    logger.info("WebSocket manager initialized")

    # Initialize core services (placeholders for future use)
    logger.info("Core services initialized")

    yield

    # Shutdown
    logger.info("Shutting down AI Video Generation Pipeline API")
    logger.info("Core services cleaned up")


# Add lifespan to the app
app.router.lifespan_context = lifespan

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_to_state(request: Request, call_next):
    """Middleware to add request ID to request state for logging"""
    request_id = getattr(request.scope, "request_id", "unknown")
    request.state.request_id = request_id
    return await call_next(request)


# Health endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "ai-video-generation-pipeline"}


@app.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(request: Request):
    """Detailed health check with system information"""
    logger = get_request_logger(request)

    try:
        # Basic system checks (expand as needed)
        health_response = DetailedHealthResponse(
            status="healthy",
            service="ai-video-generation-pipeline",
            version=settings.version,
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", None),
            checks={
                "application": "ok",
                "database": "not_configured",  # Placeholder
                "redis": "not_configured",     # Placeholder
                "external_services": "not_configured"  # Placeholder
            }
        )

        logger.info("Detailed health check completed successfully")
        return health_response

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Global exception handler registered above


def create_application():
    """Factory function to create and configure the FastAPI application with Socket.io"""
    setup_logging()
    # Return the Socket.io wrapped app for uvicorn
    return socketio_app
