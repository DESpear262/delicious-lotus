"""Main FastAPI application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import router as api_v1_router
from .config import get_settings
from .middleware import ErrorHandlerMiddleware, LoggingMiddleware, RequestIDMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()

    # Create FastAPI app with metadata
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="FFmpeg-powered media composition backend service",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Add custom middleware (order matters - first added is outermost)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Include API routers
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    @app.on_event("startup")
    async def startup_event() -> None:
        """Run on application startup."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Run on application shutdown."""
        logger.info(f"Shutting down {settings.app_name}")

    return app


# Create app instance
app = create_app()
