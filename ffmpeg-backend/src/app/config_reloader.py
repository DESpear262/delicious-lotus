"""Configuration hot-reloading system."""

import asyncio
import contextlib
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from app.config import Settings

logger = logging.getLogger(__name__)


class ConfigurationReloader:
    """Configuration hot-reloader for runtime config updates."""

    # Safe-to-reload configuration fields (non-critical settings)
    SAFE_RELOAD_FIELDS: ClassVar[set[str]] = {
        # Feature flags
        "feature_dev_api_enabled",
        "feature_beat_detection_enabled",
        "feature_gpu_encoding_enabled",
        "feature_4k_output_enabled",
        "feature_websocket_enabled",
        "feature_metrics_enabled",
        "feature_advanced_filters_enabled",
        # Logging settings
        "log_level",
        "log_sampling_rate",
        "log_request_body_size",
        "log_response_body_size",
        "log_request_headers",
        # Media processing
        "max_concurrent_jobs",
        "ffmpeg_threads",
        # RQ settings
        "rq_default_timeout",
        "rq_result_ttl",
        "rq_failure_ttl",
    }

    # Critical fields that require restart
    CRITICAL_FIELDS: ClassVar[set[str]] = {
        "database_url",
        "redis_url",
        "s3_bucket_name",
        "s3_access_key_id",
        "s3_secret_access_key",
        "environment",
    }

    def __init__(self, env_file: Path = Path(".env")) -> None:
        """Initialize configuration reloader.

        Args:
            env_file: Path to .env file to monitor
        """
        self.env_file = env_file
        self._lock = threading.RLock()
        self._last_modified: float | None = None
        self._current_settings: Settings | None = None
        self._reload_count = 0
        self._last_reload_time: datetime | None = None

    def _get_file_mtime(self) -> float | None:
        """Get modification time of .env file.

        Returns:
            Modification timestamp or None if file doesn't exist
        """
        try:
            return self.env_file.stat().st_mtime if self.env_file.exists() else None
        except OSError:
            return None

    def _file_changed(self) -> bool:
        """Check if .env file has been modified.

        Returns:
            True if file changed since last check
        """
        current_mtime = self._get_file_mtime()
        if current_mtime is None:
            return False

        if self._last_modified is None:
            self._last_modified = current_mtime
            return False

        changed = current_mtime > self._last_modified
        if changed:
            self._last_modified = current_mtime

        return changed

    def reload_settings(self, force: bool = False) -> dict[str, Any] | None:
        """Reload configuration from .env file.

        Args:
            force: Force reload even if file hasn't changed

        Returns:
            Dictionary of changed settings or None if no changes
        """
        with self._lock:
            # Check if reload needed
            if not force and not self._file_changed():
                return None

            logger.info("Configuration file changed, reloading settings")

            # Clear the lru_cache for get_settings
            from app.config import get_settings

            get_settings.cache_clear()

            try:
                # Load new settings
                new_settings = Settings()

                # Validate new settings
                errors = new_settings.validate_configuration()
                if errors:
                    logger.error(
                        "Configuration validation failed, keeping old settings",
                        extra={"errors": errors},
                    )
                    # Restore old cache
                    if self._current_settings:
                        get_settings.cache_clear()
                        get_settings()  # This will reload from env
                    return None

                # Detect changes
                changes = self._detect_changes(self._current_settings, new_settings)

                if not changes:
                    logger.info("No configuration changes detected")
                    return None

                # Check for critical field changes
                critical_changes = [field for field in changes if field in self.CRITICAL_FIELDS]

                if critical_changes:
                    logger.warning(
                        "Critical configuration fields changed - restart required",
                        extra={"critical_fields": critical_changes},
                    )
                    return None

                # Update current settings
                self._current_settings = new_settings
                self._reload_count += 1
                self._last_reload_time = datetime.utcnow()

                logger.info(
                    "Configuration reloaded successfully",
                    extra={
                        "changes": changes,
                        "reload_count": self._reload_count,
                    },
                )

                # Reload feature flags
                from app.feature_flags import get_feature_flags

                get_feature_flags().reload()

                return changes

            except Exception as e:
                logger.error(
                    "Failed to reload configuration",
                    exc_info=True,
                    extra={"error": str(e)},
                )
                return None

    def _detect_changes(
        self, old_settings: Settings | None, new_settings: Settings
    ) -> dict[str, tuple[Any, Any]]:
        """Detect changes between old and new settings.

        Args:
            old_settings: Previous settings (or None)
            new_settings: New settings

        Returns:
            Dictionary mapping field names to (old_value, new_value) tuples
        """
        if old_settings is None:
            return {}

        changes = {}

        # Check all safe-to-reload fields
        for field in self.SAFE_RELOAD_FIELDS:
            old_value = getattr(old_settings, field, None)
            new_value = getattr(new_settings, field, None)

            if old_value != new_value:
                changes[field] = (old_value, new_value)

        return changes

    def get_stats(self) -> dict[str, Any]:
        """Get reloader statistics.

        Returns:
            Dictionary with reload statistics
        """
        return {
            "reload_count": self._reload_count,
            "last_reload_time": (
                self._last_reload_time.isoformat() if self._last_reload_time else None
            ),
            "env_file": str(self.env_file),
            "file_exists": self.env_file.exists(),
            "last_modified": self._last_modified,
        }


# Global reloader instance
_reloader: ConfigurationReloader | None = None


def get_config_reloader() -> ConfigurationReloader:
    """Get global configuration reloader instance.

    Returns:
        ConfigurationReloader instance
    """
    global _reloader
    if _reloader is None:
        _reloader = ConfigurationReloader()
    return _reloader


class ConfigWatcherService:
    """Background service that watches for configuration changes."""

    def __init__(self, check_interval: int = 30) -> None:
        """Initialize config watcher service.

        Args:
            check_interval: Interval in seconds to check for changes
        """
        self.check_interval = check_interval
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self.reloader = get_config_reloader()

    async def start(self) -> None:
        """Start the configuration watcher service."""
        if self._running:
            logger.warning("Config watcher already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._watch_loop())
        logger.info(
            "Configuration watcher started",
            extra={"check_interval": self.check_interval},
        )

    async def stop(self) -> None:
        """Stop the configuration watcher service."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        logger.info("Configuration watcher stopped")

    async def _watch_loop(self) -> None:
        """Background loop that checks for configuration changes."""
        while self._running:
            try:
                # Run reload in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                changes = await loop.run_in_executor(None, self.reloader.reload_settings)

                if changes:
                    logger.info(
                        "Configuration auto-reloaded",
                        extra={"changes": list(changes.keys())},
                    )

            except Exception as e:
                logger.error(
                    "Error in config watcher loop",
                    exc_info=True,
                    extra={"error": str(e)},
                )

            # Wait before next check
            await asyncio.sleep(self.check_interval)


# Global watcher service
_watcher: ConfigWatcherService | None = None


def get_config_watcher() -> ConfigWatcherService:
    """Get global configuration watcher service.

    Returns:
        ConfigWatcherService instance
    """
    global _watcher
    if _watcher is None:
        _watcher = ConfigWatcherService()
    return _watcher
