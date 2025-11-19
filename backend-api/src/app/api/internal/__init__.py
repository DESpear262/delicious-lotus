"""Internal API endpoints router."""

from fastapi import APIRouter

from .clips import router as clips_router

# Create internal API router
router = APIRouter()

# Include sub-routers
router.include_router(clips_router, prefix="/v1", tags=["internal"])

__all__ = ["router"]
