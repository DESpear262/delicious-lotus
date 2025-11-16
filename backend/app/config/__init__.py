"""
Configuration module for AI Video Generation Pipeline.

Exports the settings singleton for easy import throughout the application.
"""

from .settings import (
    settings,
    get_settings,
    get_database_config,
    get_redis_config,
    get_cors_config,
    get_celery_config,
)

__all__ = [
    "settings",
    "get_settings",
    "get_database_config",
    "get_redis_config",
    "get_cors_config",
    "get_celery_config",
]
