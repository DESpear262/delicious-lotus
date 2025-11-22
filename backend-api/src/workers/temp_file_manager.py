"""Temporary file management with automatic cleanup and disk space monitoring."""

import logging
import os
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TempFileManager:
    """Manages temporary files with automatic cleanup and disk space monitoring.

    Usage:
        with TempFileManager(job_id="job123") as temp_mgr:
            temp_file = temp_mgr.create_file("video.mp4")
            # Work with temp_file
        # Files are automatically cleaned up when exiting context
    """

    def __init__(
        self,
        job_id: str,
        base_dir: str | Path | None = None,
        ttl_seconds: int = 3600,
        min_free_space_gb: float = 1.0,
    ) -> None:
        """Initialize temporary file manager.

        Args:
            job_id: Unique job identifier for namespace isolation
            base_dir: Base directory for temporary files (defaults to system temp)
            ttl_seconds: Time-to-live for temporary files in seconds (default: 1 hour)
            min_free_space_gb: Minimum free disk space required in GB (default: 1.0)
        """
        self.job_id = job_id
        self.ttl_seconds = ttl_seconds
        self.min_free_space_bytes = int(min_free_space_gb * 1024**3)

        # Create job-specific temporary directory
        if base_dir:
            self.base_dir = Path(base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir = self.base_dir / f"job_{job_id}"
        else:
            # Use system temp directory with job namespace
            self.temp_dir = Path(tempfile.mkdtemp(prefix=f"ffmpeg_job_{job_id}_"))

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.created_files: list[Path] = []

        logger.info(
            f"Initialized TempFileManager for job {job_id}",
            extra={
                "job_id": job_id,
                "temp_dir": str(self.temp_dir),
                "ttl_seconds": ttl_seconds,
            },
        )

    def __enter__(self) -> "TempFileManager":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and cleanup temporary files."""
        self.cleanup()

    def check_disk_space(self) -> tuple[bool, int]:
        """Check available disk space.

        Returns:
            tuple: (has_enough_space, free_space_bytes)

        Raises:
            OSError: If disk space check fails
        """
        try:
            stat = os.statvfs(self.temp_dir)
            free_space = stat.f_bavail * stat.f_frsize

            has_enough = free_space >= self.min_free_space_bytes

            if not has_enough:
                logger.warning(
                    "Low disk space detected",
                    extra={
                        "free_space_gb": free_space / 1024**3,
                        "required_gb": self.min_free_space_bytes / 1024**3,
                        "temp_dir": str(self.temp_dir),
                    },
                )

            return has_enough, free_space

        except Exception as e:
            logger.exception(
                "Failed to check disk space",
                extra={"error": str(e), "temp_dir": str(self.temp_dir)},
            )
            raise

    def create_file(self, filename: str, check_space: bool = True) -> Path:
        """Create a new temporary file.

        Args:
            filename: Name of the file to create
            check_space: Whether to check disk space before creating (default: True)

        Returns:
            Path: Path to the created temporary file

        Raises:
            OSError: If insufficient disk space or file creation fails
        """
        if check_space:
            has_space, free_space = self.check_disk_space()
            if not has_space:
                raise OSError(
                    f"Insufficient disk space: {free_space / 1024**3:.2f}GB free, "
                    f"{self.min_free_space_bytes / 1024**3:.2f}GB required"
                )

        file_path = self.temp_dir / filename
        file_path.touch()
        self.created_files.append(file_path)

        logger.debug(
            f"Created temporary file: {filename}",
            extra={"file_path": str(file_path), "job_id": self.job_id},
        )

        return file_path

    def create_dir(self, dirname: str) -> Path:
        """Create a new temporary directory.

        Args:
            dirname: Name of the directory to create

        Returns:
            Path: Path to the created temporary directory
        """
        dir_path = self.temp_dir / dirname
        dir_path.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"Created temporary directory: {dirname}",
            extra={"dir_path": str(dir_path), "job_id": self.job_id},
        )

        return dir_path

    def get_temp_path(self, filename: str) -> Path:
        """Get path for a temporary file without creating it.

        Args:
            filename: Name of the file

        Returns:
            Path: Path where the file would be located
        """
        return self.temp_dir / filename

    def list_files(self) -> list[Path]:
        """List all files in the temporary directory.

        Returns:
            list[Path]: List of file paths
        """
        if not self.temp_dir.exists():
            return []

        return [f for f in self.temp_dir.rglob("*") if f.is_file()]

    def get_total_size(self) -> int:
        """Get total size of all temporary files in bytes.

        Returns:
            int: Total size in bytes
        """
        total_size = 0
        for file_path in self.list_files():
            try:
                total_size += file_path.stat().st_size
            except OSError:
                continue

        return total_size

    def cleanup(self, force: bool = False) -> None:
        """Clean up temporary files and directory.

        Args:
            force: Force cleanup even if TTL not expired (default: False)
        """
        if not self.temp_dir.exists():
            logger.debug(
                f"Temporary directory already removed: {self.temp_dir}",
                extra={"job_id": self.job_id},
            )
            return

        # Calculate directory age
        try:
            dir_created_time = self.temp_dir.stat().st_ctime
            age_seconds = time.time() - dir_created_time
        except OSError:
            age_seconds = 0

        # Check if cleanup should proceed
        if not force and age_seconds < self.ttl_seconds:
            logger.debug(
                "Skipping cleanup, TTL not expired",
                extra={
                    "job_id": self.job_id,
                    "age_seconds": age_seconds,
                    "ttl_seconds": self.ttl_seconds,
                },
            )
            return

        # Get total size before cleanup for logging
        total_size = self.get_total_size()
        file_count = len(self.list_files())

        try:
            # Remove the entire temporary directory
            shutil.rmtree(self.temp_dir, ignore_errors=True)

            logger.info(
                f"Cleaned up temporary directory for job {self.job_id}",
                extra={
                    "job_id": self.job_id,
                    "temp_dir": str(self.temp_dir),
                    "freed_bytes": total_size,
                    "freed_mb": total_size / 1024**2,
                    "file_count": file_count,
                },
            )

        except Exception as e:
            logger.exception(
                "Failed to cleanup temporary directory",
                extra={"job_id": self.job_id, "temp_dir": str(self.temp_dir), "error": str(e)},
            )
            raise

    @staticmethod
    def cleanup_orphaned_files(
        base_dir: str | Path | None = None,
        max_age_hours: int = 24,
    ) -> int:
        """Clean up orphaned temporary files from crashed jobs.

        Args:
            base_dir: Base directory to search for orphaned files
            max_age_hours: Maximum age of files to keep (default: 24 hours)

        Returns:
            int: Number of files cleaned up
        """
        search_dir = Path(base_dir) if base_dir else Path(tempfile.gettempdir())

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0

        logger.info(
            f"Scanning for orphaned files older than {max_age_hours} hours",
            extra={"search_dir": str(search_dir), "cutoff_time": cutoff_time.isoformat()},
        )

        try:
            # Find all job directories with the ffmpeg_job_ prefix
            for job_dir in search_dir.glob("ffmpeg_job_*"):
                if not job_dir.is_dir():
                    continue

                try:
                    # Check directory modification time
                    dir_mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)

                    if dir_mtime < cutoff_time:
                        # Directory is old enough to be considered orphaned
                        total_size = sum(
                            f.stat().st_size for f in job_dir.rglob("*") if f.is_file()
                        )

                        shutil.rmtree(job_dir, ignore_errors=True)
                        cleaned_count += 1

                        logger.info(
                            f"Removed orphaned directory: {job_dir.name}",
                            extra={
                                "dir_path": str(job_dir),
                                "age_hours": (datetime.now() - dir_mtime).total_seconds() / 3600,
                                "freed_mb": total_size / 1024**2,
                            },
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to cleanup orphaned directory: {job_dir}",
                        extra={"error": str(e)},
                    )
                    continue

            logger.info(
                "Orphaned file cleanup complete",
                extra={"cleaned_count": cleaned_count},
            )

            return cleaned_count

        except Exception as e:
            logger.exception(
                "Failed to scan for orphaned files",
                extra={"error": str(e), "search_dir": str(search_dir)},
            )
            return cleaned_count
