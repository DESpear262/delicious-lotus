"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

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
    rotation_when=settings.log_rotation_when,
    rotation_interval=settings.log_rotation_interval,
    max_bytes=settings.log_max_bytes,
    backup_count=settings.log_backup_count,
    compress_rotated=settings.log_compress_rotated,
    retention_days=settings.log_retention_days,
    disk_usage_threshold=settings.log_disk_usage_threshold,
)
logger = get_logger(__name__)


def custom_openapi(app: FastAPI):
    """Customize OpenAPI schema to include security schemes.

    Args:
        app: FastAPI application instance

    Returns:
        Callable that generates custom OpenAPI schema
    """

    def openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add security schemes for Swagger UI
        openapi_schema["components"]["securitySchemes"] = {
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API Key for internal endpoints (e.g., dev_key_123)",
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for service-to-service authentication",
            },
        }

        # Apply security to all /internal endpoints
        for path, path_item in openapi_schema.get("paths", {}).items():
            if path.startswith("/internal/"):
                for operation in path_item.values():
                    if isinstance(operation, dict) and "operationId" in operation:
                        # Allow either API Key or Bearer token
                        operation["security"] = [
                            {"APIKeyHeader": []},
                            {"BearerAuth": []},
                        ]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return openapi


def create_app() -> FastAPI:  # noqa: C901
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

    # Customize OpenAPI schema for authentication
    app.openapi = custom_openapi(app)

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
    # Use higher rate limit in development (1000 requests/min), lower in production (10 requests/min)
    rate_limit = 1000 if settings.is_development else 10
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)
    app.add_middleware(InternalAuthMiddleware, rate_limit_per_key=100)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # Setup exception handlers (replaces ErrorHandlerMiddleware with more comprehensive handling)
    setup_exception_handlers(app)

    # Include API routers
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
    app.include_router(internal_router, prefix="/internal")

    # Include consolidated fastapi_app routers
    from fastapi_app.api.routes.v1 import api_v1_router as fastapi_api_v1_router
    from fastapi_app.api.routes.internal_v1 import internal_v1_router as fastapi_internal_v1_router
    from fastapi_app.api.routes.webhooks import webhook_router as fastapi_webhook_router
    from fastapi_app.api.routes.websocket import websocket_router as fastapi_websocket_router

    # Mount with appropriate prefixes (fastapi_app routers already have prefixes defined)
    app.include_router(fastapi_api_v1_router)
    app.include_router(fastapi_internal_v1_router)
    app.include_router(fastapi_webhook_router)
    app.include_router(fastapi_websocket_router)

    @app.on_event("startup")
    async def startup_event() -> None:
        """Run on application startup."""
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")

        # Log feature flags
        feature_flags = settings.get_feature_flags()
        enabled_flags = [k for k, v in feature_flags.items() if v]
        if enabled_flags:
            logger.info(f"Enabled features: {', '.join(enabled_flags)}")

        # Start configuration watcher in development/staging
        if settings.is_development or settings.is_staging:
            try:
                from .config_reloader import get_config_watcher

                watcher = get_config_watcher()
                await watcher.start()
                logger.info("Configuration hot-reloading enabled")
            except Exception as e:
                logger.warning(f"Failed to start config watcher: {e}")

        # WebSocket services use lazy initialization - they'll be created
        # when the first WebSocket connection is established
        logger.info("WebSocket services will initialize on first connection")

        # Debug: Log all registered routes
        logger.info("Registered Routes:")
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                logger.info(f"  {route.methods} {route.path}")
            elif hasattr(route, "path"):
                logger.info(f"  (No methods) {route.path}")
            else:
                logger.info(f"  {route}")

        logger.info("Application startup complete")

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        """Run on application shutdown."""
        logger.info(f"Shutting down {settings.app_name}")

        # Stop configuration watcher
        if settings.is_development or settings.is_staging:
            try:
                from .config_reloader import get_config_watcher

                watcher = get_config_watcher()
                await watcher.stop()
                logger.info("Configuration watcher shut down")
            except Exception as e:
                logger.error(f"Error shutting down config watcher: {e}")

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
import socketio
from fastapi_app.api.routes.websocket import sio as fastapi_sio

fastapi_app = create_app()
app = socketio.ASGIApp(fastapi_sio, other_asgi_app=fastapi_app)
