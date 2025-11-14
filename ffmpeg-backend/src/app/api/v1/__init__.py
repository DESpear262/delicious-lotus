"""API v1 routes."""

from fastapi import APIRouter

from .compositions import router as compositions_router
from .health import router as health_router
from .jobs import router as jobs_router

# Create main v1 router
router = APIRouter()

# Include sub-routers
router.include_router(health_router, tags=["health"])
router.include_router(compositions_router, prefix="/compositions", tags=["compositions"])
router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])

__all__ = ["router"]
