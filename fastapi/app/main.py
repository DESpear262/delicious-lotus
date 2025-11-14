"""
Main FastAPI application
Block 0: API Skeleton & Core Infrastructure
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import RequestIDMiddleware, setup_logging, get_request_logger
from app.core.errors import global_exception_handler
from app.models.schemas import DetailedHealthResponse
from app.api.routes.v1 import api_v1_router
from app.api.routes.internal_v1 import internal_v1_router


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown hooks"""

    # Startup
    logger = logging.getLogger("app")
    logger.info("Starting AI Video Generation Pipeline API")
    logger.info("API routers registered")

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


def create_application() -> FastAPI:
    """Factory function to create and configure the FastAPI application"""
    setup_logging()
    return app
