"""Cleanup job handler for managing temporary files and disk space."""

import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings

from workers.redis_pool import get_redis_connection

logger = logging.getLogger(__name__)


@dataclass
class CleanupReport:
    """Report of cleanup operation results."""

    files_deleted: int = 0
    directories_deleted: int = 0
    space_freed_bytes: int = 0
    errors: list[str] | None = None
    duration_seconds: float = 0.0

    @property
    def space_freed_mb(self) -> float:
        """Get space freed in MB.

        Returns:
            float: Space freed in megabytes
        """
        return round(self.space_freed_bytes / (1024 * 1024), 2)

    @property
    def space_freed_gb(self) -> float:
        """Get space freed in GB.

        Returns:
            float: Space freed in gigabytes
        """
        return round(self.space_freed_bytes / (1024 * 1024 * 1024), 2)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            dict: Serialized cleanup report
        """
        return {
            "files_deleted": self.files_deleted,
            "directories_deleted": self.directories_deleted,
            "space_freed_bytes": self.space_freed_bytes,
            "space_freed_mb": self.space_freed_mb,
            "space_freed_gb": self.space_freed_gb,
            "errors": self.errors or [],
            "duration_seconds": round(self.duration_seconds, 2),
        }


class CleanupJobHandler:
    """Handler for cleanup jobs that remove old temporary files."""

    # Default retention periods per file type (in hours)
    DEFAULT_RETENTION_HOURS: dict[str, int] = {
        "temp": 24,  # Temporary processing files: 24 hours
        "output": 72,  # Output files: 72 hours (3 days)
        "cache": 48,  # Cache files: 48 hours
        "logs": 168,  # Log files: 168 hours (7 days)
    }

    def __init__(
        self,
        temp_dir: str | Path | None = None,
        retention_hours: dict[str, int] | None = None,
    ) -> None:
        """Initialize cleanup job handler.

        Args:
            temp_dir: Temporary directory to clean (defaults to settings.temp_dir)
            retention_hours: Custom retention periods per file type
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path(settings.temp_dir)
        self.retention_hours = retention_hours or self.DEFAULT_RETENTION_HOURS
        self.redis = get_redis_connection()

        logger.info(
            "Initialized CleanupJobHandler",
            extra={
                "temp_dir": str(self.temp_dir),
                "retention_hours": self.retention_hours,
            },
        )

    def get_active_job_dirs(self) -> set[str]:
        """Get list of directories for currently active jobs from Redis.

        Returns:
            set[str]: Set of active job directory names
        """
        try:
            # Get all job status keys from Redis
            status_keys = self.redis.keys("job:status:*")

            active_dirs = set()
            for key in status_keys:
                # Extract job ID from key
                if isinstance(key, bytes):
                    key = key.decode("utf-8")

                job_id = key.split(":")[-1]

                # Check if job is still in progress
                status_data = self.redis.get(f"job:status:{job_id}")
                if status_data:
                    import json

                    try:
                        data = json.loads(status_data)
                        if data.get("status") in {"pending", "in_progress"}:
                            # Add job ID to active dirs (jobs create dirs with their ID)
                            active_dirs.add(job_id)
                    except json.JSONDecodeError:
                        pass

            logger.debug(
                f"Found {len(active_dirs)} active job directories",
                extra={"active_count": len(active_dirs)},
            )

            return active_dirs

        except Exception as e:
            logger.exception(f"Error getting active job dirs: {e}")
            return set()

    def is_file_old(self, file_path: Path, retention_hours: int) -> bool:
        """Check if a file is older than retention period.

        Args:
            file_path: Path to file
            retention_hours: Retention period in hours

        Returns:
            bool: True if file is older than retention period
        """
        try:
            # Get file modification time
            mtime = file_path.stat().st_mtime
            file_age = time.time() - mtime

            # Convert retention hours to seconds
            retention_seconds = retention_hours * 3600

            return file_age > retention_seconds

        except Exception as e:
            logger.warning(f"Error checking file age for {file_path}: {e}")
            return False

    def get_disk_usage(self, path: Path | None = None) -> tuple[int, int, float]:
        """Get disk usage statistics.

        Args:
            path: Path to check (defaults to temp_dir)

        Returns:
            tuple: (total_bytes, used_bytes, percent_used)
        """
        path = path or self.temp_dir

        try:
            stat = shutil.disk_usage(path)
            percent_used = (stat.used / stat.total) * 100

            return stat.total, stat.used, percent_used

        except Exception as e:
            logger.exception(f"Error getting disk usage: {e}")
            return (0, 0, 0.0)

    def cleanup_old_files(
        self,
        max_age_hours: int = 24,
        dry_run: bool = False,
    ) -> CleanupReport:
        """Clean up files older than max_age_hours.

        Args:
            max_age_hours: Maximum age of files to keep (in hours)
            dry_run: If True, don't actually delete files, just report what would be deleted

        Returns:
            CleanupReport: Report of cleanup operation
        """
        start_time = time.time()
        report = CleanupReport(errors=[])

        logger.info(
            f"Starting cleanup of files older than {max_age_hours} hours",
            extra={
                "max_age_hours": max_age_hours,
                "temp_dir": str(self.temp_dir),
                "dry_run": dry_run,
            },
        )

        if not self.temp_dir.exists():
            logger.warning(f"Temp directory does not exist: {self.temp_dir}")
            return report

        # Get active job directories to avoid deleting files in use
        active_job_dirs = self.get_active_job_dirs()

        try:
            # Iterate through files in temp directory
            for item in self.temp_dir.rglob("*"):
                try:
                    # Skip if in active job directory
                    if item.is_dir():
                        if item.name in active_job_dirs:
                            logger.debug(f"Skipping active job directory: {item}")
                            continue
                    else:
                        # Check if file is in an active job directory
                        if any(active_dir in str(item) for active_dir in active_job_dirs):
                            logger.debug(f"Skipping file in active job dir: {item}")
                            continue

                    # Check if old enough to delete
                    if not self.is_file_old(item, max_age_hours):
                        continue

                    # Get file size before deletion
                    if item.is_file():
                        size = item.stat().st_size
                    else:
                        # Calculate directory size
                        size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())

                    # Delete file or directory
                    if not dry_run:
                        if item.is_file():
                            item.unlink()
                            report.files_deleted += 1
                            logger.debug(f"Deleted file: {item}")
                        elif item.is_dir():
                            shutil.rmtree(item)
                            report.directories_deleted += 1
                            logger.debug(f"Deleted directory: {item}")

                    report.space_freed_bytes += size

                except Exception as e:
                    error_msg = f"Error processing {item}: {e}"
                    logger.warning(error_msg)
                    if report.errors is not None:
                        report.errors.append(error_msg)

        except Exception as e:
            logger.exception(f"Error during cleanup: {e}")
            if report.errors is not None:
                report.errors.append(f"Cleanup error: {e}")

        report.duration_seconds = time.time() - start_time

        logger.info(
            "Cleanup completed",
            extra={
                "files_deleted": report.files_deleted,
                "directories_deleted": report.directories_deleted,
                "space_freed_mb": report.space_freed_mb,
                "duration_seconds": report.duration_seconds,
                "dry_run": dry_run,
            },
        )

        return report

    def cleanup_by_disk_threshold(
        self,
        threshold_percent: float = 80.0,
        target_percent: float = 60.0,
    ) -> CleanupReport:
        """Clean up files when disk usage exceeds threshold.

        Args:
            threshold_percent: Trigger cleanup when disk usage exceeds this percentage
            target_percent: Clean up until disk usage is below this percentage

        Returns:
            CleanupReport: Report of cleanup operation
        """
        total, used, percent_used = self.get_disk_usage()

        logger.info(
            f"Disk usage: {percent_used:.1f}% (threshold: {threshold_percent}%)",
            extra={
                "percent_used": percent_used,
                "threshold": threshold_percent,
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
            },
        )

        # Check if cleanup is needed
        if percent_used < threshold_percent:
            logger.info("Disk usage below threshold, no cleanup needed")
            return CleanupReport()

        logger.warning(
            f"Disk usage ({percent_used:.1f}%) exceeds threshold ({threshold_percent}%), starting aggressive cleanup"
        )

        # Start with oldest files first (highest retention)
        combined_report = CleanupReport(errors=[])

        # Clean in order of increasing importance
        for _file_type, retention_hours in sorted(
            self.retention_hours.items(), key=lambda x: -x[1]
        ):
            report = self.cleanup_old_files(max_age_hours=retention_hours // 2)

            # Combine reports
            combined_report.files_deleted += report.files_deleted
            combined_report.directories_deleted += report.directories_deleted
            combined_report.space_freed_bytes += report.space_freed_bytes
            if report.errors and combined_report.errors is not None:
                combined_report.errors.extend(report.errors)

            # Check if we've reached target
            _, _, current_percent = self.get_disk_usage()
            if current_percent < target_percent:
                logger.info(
                    f"Reached target disk usage: {current_percent:.1f}%",
                    extra={"current_percent": current_percent, "target": target_percent},
                )
                break

        return combined_report

    def execute(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute cleanup job.

        Args:
            params: Optional job parameters
                - max_age_hours: Maximum age of files to keep
                - dry_run: If True, don't actually delete files
                - disk_threshold: If set, trigger threshold-based cleanup

        Returns:
            dict: Cleanup job result
        """
        params = params or {}

        logger.info("Starting cleanup job", extra={"params": params})

        try:
            # Check if threshold-based cleanup
            if "disk_threshold" in params:
                report = self.cleanup_by_disk_threshold(
                    threshold_percent=params.get("disk_threshold", 80.0),
                    target_percent=params.get("target_percent", 60.0),
                )
            else:
                # Regular time-based cleanup
                report = self.cleanup_old_files(
                    max_age_hours=params.get("max_age_hours", 24),
                    dry_run=params.get("dry_run", False),
                )

            logger.info(
                "Cleanup job completed successfully",
                extra=report.to_dict(),
            )

            return {
                "success": True,
                "report": report.to_dict(),
            }

        except Exception as e:
            logger.exception(f"Cleanup job failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }


def run_cleanup_job(**params: Any) -> dict[str, Any]:
    """Run cleanup job (entry point for RQ worker).

    Args:
        **params: Job parameters

    Returns:
        dict: Cleanup job result
    """
    handler = CleanupJobHandler()
    return handler.execute(params)
