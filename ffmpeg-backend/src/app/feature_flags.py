"""Feature flag management system."""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


class FeatureFlags:
    """Feature flag manager for runtime feature toggling."""

    def __init__(self) -> None:
        """Initialize feature flags from settings."""
        self._settings = get_settings()
        self._flags = self._settings.get_feature_flags()
        logger.info(
            "Feature flags initialized",
            extra={"flags": self._flags},
        )

    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag (without 'feature_' prefix)

        Returns:
            bool: True if enabled, False otherwise
        """
        return self._flags.get(flag_name, False)

    def get_all(self) -> dict[str, bool]:
        """Get all feature flags.

        Returns:
            Dictionary of feature flag names and their values
        """
        return self._flags.copy()

    def reload(self) -> None:
        """Reload feature flags from settings.

        Note: This requires configuration hot-reloading to be implemented.
        """
        self._settings = get_settings()
        self._flags = self._settings.get_feature_flags()
        logger.info(
            "Feature flags reloaded",
            extra={"flags": self._flags},
        )


# Global feature flags instance
_feature_flags: FeatureFlags | None = None


def get_feature_flags() -> FeatureFlags:
    """Get global feature flags instance.

    Returns:
        FeatureFlags: Global feature flags manager
    """
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def require_feature(
    flag_name: str,
    error_message: str | None = None,
    return_404: bool = False,
) -> Callable[[F], F]:
    """Decorator to require a feature flag to be enabled for endpoint access.

    Args:
        flag_name: Name of the feature flag (without 'feature_' prefix)
        error_message: Custom error message (optional)
        return_404: If True, return 404 instead of 503 when disabled

    Returns:
        Decorated function that checks feature flag

    Example:
        @router.get("/dev/debug")
        @require_feature("dev_api", "Debug endpoints are currently disabled")
        async def debug_endpoint():
            return {"debug": "info"}
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            flags = get_feature_flags()
            if not flags.is_enabled(flag_name):
                msg = error_message or f"Feature '{flag_name}' is currently disabled"
                if return_404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=msg,
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={
                            "error_code": "FEATURE_DISABLED",
                            "message": msg,
                            "feature": flag_name,
                        },
                    )
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            flags = get_feature_flags()
            if not flags.is_enabled(flag_name):
                msg = error_message or f"Feature '{flag_name}' is currently disabled"
                if return_404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=msg,
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={
                            "error_code": "FEATURE_DISABLED",
                            "message": msg,
                            "feature": flag_name,
                        },
                    )
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def feature_flag_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
    """Middleware to add feature flag information to response headers.

    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain

    Returns:
        Response with feature flag headers
    """

    async def _middleware() -> Any:
        response = await call_next(request)

        # Add feature flags to response headers (for debugging)
        if get_settings().is_development:
            flags = get_feature_flags()
            response.headers["X-Feature-Flags"] = ",".join(
                [f"{k}={v}" for k, v in flags.get_all().items() if v]
            )

        return response

    return _middleware()


async def get_feature_flags_endpoint() -> dict[str, bool]:
    """Get all feature flags (for admin/debug endpoints).

    Returns:
        Dictionary of all feature flags and their status
    """
    flags = get_feature_flags()
    return flags.get_all()


def check_feature_dependencies() -> list[str]:
    """Check feature flag dependencies and return warnings.

    Returns:
        List of warning messages
    """
    warnings: list[str] = []
    settings = get_settings()

    # Check dependencies
    if settings.feature_4k_output_enabled and not settings.feature_gpu_encoding_enabled:
        warnings.append(
            "4K output is enabled without GPU encoding. "
            "This may result in very slow processing. "
            "Consider enabling FEATURE_GPU_ENCODING_ENABLED."
        )

    if settings.feature_beat_detection_enabled and not settings.feature_advanced_filters_enabled:
        warnings.append(
            "Beat detection is enabled but advanced filters are not. "
            "Beat detection requires advanced filter support."
        )

    return warnings
