"""Configuration management endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.config_reloader import get_config_reloader
from app.feature_flags import get_feature_flags, require_feature

logger = logging.getLogger(__name__)

router = APIRouter()


class ConfigReloadRequest(BaseModel):
    """Request to reload configuration."""

    force: bool = Field(default=False, description="Force reload even if file unchanged")


class ConfigReloadResponse(BaseModel):
    """Response from configuration reload."""

    success: bool = Field(description="Whether reload was successful")
    changes: dict[str, tuple[Any, Any]] = Field(
        default_factory=dict, description="Configuration changes detected"
    )
    reload_count: int = Field(description="Total number of reloads")
    message: str = Field(description="Human-readable message")


class FeatureFlagsResponse(BaseModel):
    """Feature flags status."""

    flags: dict[str, bool] = Field(description="All feature flags and their status")


class ConfigStatsResponse(BaseModel):
    """Configuration statistics."""

    reload_stats: dict[str, Any] = Field(description="Reload statistics")
    current_environment: str = Field(description="Current environment")
    debug_mode: bool = Field(description="Debug mode status")
    feature_flags: dict[str, bool] = Field(description="Current feature flags")


@router.post("/reload", response_model=ConfigReloadResponse)
@require_feature("dev_api", "Configuration reload is only available in development mode")
async def reload_configuration(request: ConfigReloadRequest) -> ConfigReloadResponse:
    """Manually trigger configuration reload.

    This endpoint is only available when the dev_api feature flag is enabled.
    It allows hot-reloading of configuration without restarting the service.

    Only safe configuration fields can be reloaded:
    - Feature flags
    - Logging settings
    - Media processing settings
    - Job queue settings

    Critical fields (database, Redis, S3 credentials) require a service restart.

    Args:
        request: Reload request with optional force flag

    Returns:
        ConfigReloadResponse with reload results

    Raises:
        HTTPException: If reload fails
    """
    try:
        reloader = get_config_reloader()
        changes = reloader.reload_settings(force=request.force)

        if changes is None:
            return ConfigReloadResponse(
                success=False,
                changes={},
                reload_count=reloader._reload_count,
                message="No configuration changes detected",
            )

        return ConfigReloadResponse(
            success=True,
            changes=changes,
            reload_count=reloader._reload_count,
            message=f"Configuration reloaded successfully ({len(changes)} changes)",
        )

    except Exception as e:
        logger.error("Failed to reload configuration", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration reload failed: {str(e)}",
        ) from e


@router.get("/feature-flags", response_model=FeatureFlagsResponse)
async def get_feature_flags_status() -> FeatureFlagsResponse:
    """Get current feature flag status.

    Returns:
        FeatureFlagsResponse with all feature flags
    """
    flags = get_feature_flags()
    return FeatureFlagsResponse(flags=flags.get_all())


@router.get("/stats", response_model=ConfigStatsResponse)
@require_feature("dev_api", "Configuration stats are only available in development mode")
async def get_configuration_stats() -> ConfigStatsResponse:
    """Get configuration statistics and current settings.

    This endpoint is only available when the dev_api feature flag is enabled.

    Returns:
        ConfigStatsResponse with current configuration state
    """
    settings = get_settings()
    reloader = get_config_reloader()
    flags = get_feature_flags()

    return ConfigStatsResponse(
        reload_stats=reloader.get_stats(),
        current_environment=settings.environment,
        debug_mode=settings.debug,
        feature_flags=flags.get_all(),
    )
