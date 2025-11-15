"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.internal import router as internal_router
from .api.v1 import router as api_v1_router
from .config import get_settings
from .logging_config import get_logger, setup_logging
from .middleware import InternalAuthMiddleware, LoggingMiddleware, RequestIDMiddleware
from .middleware.exception_handlers import setup_exception_handlers
from .middleware.metrics import MetricsMiddleware
from .middleware.rate_limiting import RateLimitMiddleware

# Initialize structured logging
settings = get_settings()
setup_logging(
    environment=settings.environment,
    log_level=settings.log_level,
    log_dir="./logs",
    enable_file_logging=not settings.is_development,  # Only file logging in non-dev
)
logger = get_logger(__name__)


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
    app.add_middleware(RateLimitMiddleware, requests_per_minute=10)
    app.add_middleware(InternalAuthMiddleware, rate_limit_per_key=100)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Setup exception handlers (replaces ErrorHandlerMiddleware with more comprehensive handling)
    setup_exception_handlers(app)

    # Include API routers
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    app.include_router(internal_router, prefix="/internal")

    @app.on_event("startup")
    async def startup_event() -> None:
        """Run on application startup."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")

        # Initialize WebSocket services
        try:
            from .api.v1.websocket import get_heartbeat_manager, get_redis_subscriber

            await get_redis_subscriber()
            logger.info("WebSocket Redis subscriber initialized")

            await get_heartbeat_manager()
            logger.info("WebSocket heartbeat manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket services: {e}")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Run on application shutdown."""
        logger.info(f"Shutting down {settings.app_name}")

        # Cleanup WebSocket services
        try:
            from .api.v1.websocket import heartbeat_manager, redis_subscriber

            if heartbeat_manager:
                await heartbeat_manager.stop()
                logger.info("WebSocket heartbeat manager shut down")

            if redis_subscriber:
                await redis_subscriber.stop_listening()
                await redis_subscriber.disconnect()
                logger.info("WebSocket Redis subscriber shut down")
        except Exception as e:
            logger.error(f"Error shutting down WebSocket services: {e}")

    return app


# Create app instance
app = create_app()
