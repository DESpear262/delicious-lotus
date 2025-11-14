"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Application health status
    """
    return HealthResponse(status="healthy", version="0.1.0")


@router.get("/ready", response_model=HealthResponse)
async def readiness_check() -> HealthResponse:
    """Readiness check endpoint.

    Returns:
        HealthResponse: Application readiness status
    """
    # TODO: Add checks for database, Redis, etc.
    return HealthResponse(status="ready", version="0.1.0")
