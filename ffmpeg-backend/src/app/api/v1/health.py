"""Health check endpoints with comprehensive component status checks."""

import asyncio
import os
import subprocess
import time
from typing import Any

import psutil
from db.session import get_db_session
from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, Field
from redis import Redis
from sqlalchemy import text

from app.config import get_settings
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


class ComponentStatus(BaseModel):
    """Individual component health status."""

    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float | None = None
    details: dict[str, Any] | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Basic health check response model."""

    status: str  # "healthy", "degraded", "unhealthy"
    version: str = "0.1.0"


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with component status."""

    status: str  # "healthy", "degraded", "unhealthy"
    version: str = "0.1.0"
    timestamp: float = Field(default_factory=time.time)
    components: list[ComponentStatus]
    system: dict[str, Any]


async def check_database() -> ComponentStatus:
    """Check PostgreSQL database connection and query execution.

    Returns:
        ComponentStatus: Database health status
    """
    start_time = time.time()
    try:
        async with get_db_session() as session:
            # Execute a simple query
            result = await session.execute(text("SELECT 1"))
            result.scalar()

            response_time = (time.time() - start_time) * 1000

            return ComponentStatus(
                name="database",
                status="healthy",
                response_time_ms=round(response_time, 2),
                details={
                    "type": "postgresql",
                    "pool_size": settings.db_pool_size,
                },
            )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return ComponentStatus(
            name="database",
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            error=str(e),
        )


async def check_redis() -> ComponentStatus:
    """Check Redis connectivity and SET/GET operations.

    Returns:
        ComponentStatus: Redis health status
    """
    start_time = time.time()
    try:
        # Create Redis client with timeout
        redis_client = Redis.from_url(
            str(settings.redis_url),
            socket_connect_timeout=5,
            socket_timeout=5,
            decode_responses=True,
        )

        # Test SET/GET operations
        test_key = "health_check_test"
        test_value = "ok"
        redis_client.set(test_key, test_value, ex=10)  # Expire in 10 seconds
        result = redis_client.get(test_key)

        if result != test_value:
            raise ValueError(f"Redis SET/GET test failed: expected {test_value}, got {result}")

        # Clean up
        redis_client.delete(test_key)
        redis_client.close()

        response_time = (time.time() - start_time) * 1000

        return ComponentStatus(
            name="redis",
            status="healthy",
            response_time_ms=round(response_time, 2),
            details={
                "max_connections": settings.redis_max_connections,
            },
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Redis health check failed: {e}", exc_info=True)
        return ComponentStatus(
            name="redis",
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            error=str(e),
        )


async def check_s3() -> ComponentStatus:
    """Check S3 bucket access and list permissions.

    Returns:
        ComponentStatus: S3 health status
    """
    start_time = time.time()
    try:
        import boto3

        # Create S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.s3_access_key_id or None,
            aws_secret_access_key=settings.s3_secret_access_key or None,
            region_name=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
        )

        # Try to list objects in the bucket (limit to 1)
        if settings.s3_bucket_name:
            s3_client.list_objects_v2(Bucket=settings.s3_bucket_name, MaxKeys=1)

            response_time = (time.time() - start_time) * 1000

            return ComponentStatus(
                name="s3",
                status="healthy",
                response_time_ms=round(response_time, 2),
                details={
                    "bucket": settings.s3_bucket_name,
                    "region": settings.s3_region,
                },
            )
        else:
            return ComponentStatus(
                name="s3",
                status="degraded",
                response_time_ms=0.0,
                details={"message": "S3 bucket not configured"},
            )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.warning(f"S3 health check failed: {e}")
        return ComponentStatus(
            name="s3",
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            error=str(e),
        )


async def check_ffmpeg() -> ComponentStatus:
    """Check FFmpeg binary availability and version.

    Returns:
        ComponentStatus: FFmpeg health status
    """
    start_time = time.time()
    try:
        # Check if FFmpeg binary exists
        if not os.path.exists(settings.ffmpeg_path):
            return ComponentStatus(
                name="ffmpeg",
                status="unhealthy",
                response_time_ms=0.0,
                error=f"FFmpeg binary not found at {settings.ffmpeg_path}",
            )

        # Get FFmpeg version
        result = subprocess.run(  # noqa: S603
            [settings.ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )

        # Extract version from first line
        version_line = result.stdout.split("\n")[0]

        response_time = (time.time() - start_time) * 1000

        return ComponentStatus(
            name="ffmpeg",
            status="healthy",
            response_time_ms=round(response_time, 2),
            details={
                "version": version_line,
                "path": settings.ffmpeg_path,
            },
        )
    except subprocess.TimeoutExpired:
        response_time = (time.time() - start_time) * 1000
        return ComponentStatus(
            name="ffmpeg",
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            error="FFmpeg version check timed out",
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"FFmpeg health check failed: {e}", exc_info=True)
        return ComponentStatus(
            name="ffmpeg",
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            error=str(e),
        )


def get_system_metrics() -> dict[str, Any]:
    """Get system resource usage metrics.

    Returns:
        dict: System metrics including CPU and memory usage
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_total_mb": round(memory.total / (1024 * 1024), 2),
            "memory_used_mb": round(memory.used / (1024 * 1024), 2),
            "memory_percent": round(memory.percent, 2),
            "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
            "disk_percent": round(disk.percent, 2),
        }
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {e}")
        return {"error": str(e)}


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response) -> HealthResponse:
    """Basic health check endpoint.

    Returns HTTP 200 if the service is running, HTTP 503 if unhealthy.

    Returns:
        HealthResponse: Application health status
    """
    try:
        # Quick check - just verify the service is running
        # For basic health, we don't check dependencies
        return HealthResponse(status="healthy", version="0.1.0")
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unhealthy", version="0.1.0")


@router.get("/healthz", response_model=DetailedHealthResponse)
async def detailed_health_check(response: Response) -> DetailedHealthResponse:
    """Detailed health check endpoint with component status.

    Checks:
    - PostgreSQL database connection and queries
    - Redis connectivity and operations
    - S3 bucket access
    - FFmpeg binary availability
    - System resource usage

    Returns HTTP 200 if all components are healthy,
    HTTP 503 if any critical component is unhealthy,
    HTTP 200 with degraded status if only non-critical components fail.

    Returns:
        DetailedHealthResponse: Detailed component health status
    """
    try:
        # Run all health checks concurrently with timeout
        check_tasks = [
            check_database(),
            check_redis(),
            check_s3(),
            check_ffmpeg(),
        ]

        # Execute checks with overall timeout of 10 seconds
        components = await asyncio.wait_for(
            asyncio.gather(*check_tasks, return_exceptions=True), timeout=10.0
        )

        # Handle any exceptions from gather
        component_statuses = []
        for comp in components:
            if isinstance(comp, Exception):
                logger.error(f"Component check raised exception: {comp}", exc_info=True)
                component_statuses.append(
                    ComponentStatus(
                        name="unknown",
                        status="unhealthy",
                        error=str(comp),
                    )
                )
            else:
                component_statuses.append(comp)

        # Get system metrics
        system_metrics = get_system_metrics()

        # Determine overall status
        statuses = [comp.status for comp in component_statuses]

        # Critical components: database, redis, ffmpeg
        critical_components = ["database", "redis", "ffmpeg"]
        critical_statuses = [
            comp.status for comp in component_statuses if comp.name in critical_components
        ]

        if "unhealthy" in critical_statuses:
            overall_status = "unhealthy"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif "unhealthy" in statuses or "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return DetailedHealthResponse(
            status=overall_status,
            components=component_statuses,
            system=system_metrics,
        )

    except asyncio.TimeoutError:
        logger.error("Health check timed out")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DetailedHealthResponse(
            status="unhealthy",
            components=[
                ComponentStatus(
                    name="health_check",
                    status="unhealthy",
                    error="Health check timed out after 10 seconds",
                )
            ],
            system={},
        )
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return DetailedHealthResponse(
            status="unhealthy",
            components=[
                ComponentStatus(
                    name="health_check",
                    status="unhealthy",
                    error=str(e),
                )
            ],
            system={},
        )


@router.get("/metrics")
async def get_metrics(request: Request) -> dict[str, Any]:
    """
    Get API performance metrics collected by MetricsMiddleware.

    Returns:
        dict: API metrics including request counts, response times, error rates
    """
    try:
        # Access metrics from middleware if available
        metrics_middleware = None
        for middleware in request.app.middleware_stack:
            if hasattr(middleware, "cls") and middleware.cls.__name__ == "MetricsMiddleware":
                metrics_middleware = middleware
                break

        if metrics_middleware and hasattr(metrics_middleware, "get_metrics"):
            return metrics_middleware.get_metrics()
        else:
            # Return empty metrics if middleware not configured
            return {
                "total_requests": 0,
                "total_errors": 0,
                "error_rate_percent": 0.0,
                "requests_by_endpoint": {},
                "requests_by_status": {},
                "response_times": {},
                "message": "Metrics middleware not configured",
            }
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {e}", exc_info=True)
        return {
            "error": str(e),
            "message": "Failed to retrieve metrics",
        }
