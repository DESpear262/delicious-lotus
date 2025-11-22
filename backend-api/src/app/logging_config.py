"""Structured JSON logging configuration using pythonjsonlogger.

This module configures application-wide logging with structured JSON output
including contextual metadata like request IDs, composition IDs, and user IDs.
"""

import gzip
import logging
import logging.handlers
import os
import shutil
import sys
import time
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger

# Context variables for storing request-scoped metadata
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
composition_id_ctx: ContextVar[str | None] = ContextVar("composition_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)
job_id_ctx: ContextVar[str | None] = ContextVar("job_id", default=None)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes context variables in every log entry."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to the log record.

        Args:
            log_record: Dictionary to be serialized to JSON
            record: Python logging LogRecord
            message_dict: Dictionary with message and extra fields
        """
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add process and thread info
        log_record["process_id"] = record.process
        log_record["thread_id"] = record.thread

        # Add context variables from contextvars
        request_id = request_id_ctx.get()
        if request_id:
            log_record["request_id"] = request_id

        composition_id = composition_id_ctx.get()
        if composition_id:
            log_record["composition_id"] = composition_id

        user_id = user_id_ctx.get()
        if user_id:
            log_record["user_id"] = user_id

        job_id = job_id_ctx.get()
        if job_id:
            log_record["job_id"] = job_id

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None,
            }


class CompressingTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """TimedRotatingFileHandler that compresses rotated logs with gzip."""

    def __init__(self, *args, compress: bool = True, **kwargs):
        """Initialize handler with compression option.

        Args:
            *args: Positional arguments for TimedRotatingFileHandler
            compress: Whether to compress rotated files
            **kwargs: Keyword arguments for TimedRotatingFileHandler
        """
        super().__init__(*args, **kwargs)
        self.compress = compress

    def doRollover(self) -> None:  # noqa: N802
        """Perform rollover and compress the rotated file."""
        super().doRollover()

        if self.compress and self.backupCount > 0:
            # Find the most recently rotated file
            # TimedRotatingFileHandler appends a suffix like .2025-01-14
            # Get all rotated files
            dir_name, base_name = os.path.split(self.baseFilename)
            file_names = os.listdir(dir_name)
            result = []
            prefix = base_name + "."
            plen = len(prefix)

            for file_name in file_names:
                if file_name[:plen] == prefix:
                    suffix = file_name[plen:]
                    if suffix.endswith(".gz"):
                        continue
                    result.append(os.path.join(dir_name, file_name))

            if result:
                result.sort()
                # Compress the most recent rotated file (last in sorted list)
                source_file = result[-1]
                if os.path.exists(source_file):
                    self._compress_file(source_file)

    def _compress_file(self, source_file: str) -> None:
        """Compress a log file with gzip.

        Args:
            source_file: Path to file to compress
        """
        dest_file = source_file + ".gz"
        try:
            with open(source_file, "rb") as f_in, gzip.open(dest_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(source_file)
        except Exception as e:
            # Don't fail if compression fails
            logging.error(f"Failed to compress log file {source_file}: {e}")


class CompressingRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """RotatingFileHandler that compresses rotated logs with gzip."""

    def __init__(self, *args, compress: bool = True, **kwargs):
        """Initialize handler with compression option.

        Args:
            *args: Positional arguments for RotatingFileHandler
            compress: Whether to compress rotated files
            **kwargs: Keyword arguments for RotatingFileHandler
        """
        super().__init__(*args, **kwargs)
        self.compress = compress

    def doRollover(self) -> None:  # noqa: N802
        """Perform rollover and compress the rotated file."""
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)

            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)

            # Compress the rotated file
            if self.compress and os.path.exists(dfn):
                self._compress_file(dfn)

        if not self.delay:
            self.stream = self._open()

    def _compress_file(self, source_file: str) -> None:
        """Compress a log file with gzip.

        Args:
            source_file: Path to file to compress
        """
        dest_file = source_file + ".gz"
        try:
            with open(source_file, "rb") as f_in, gzip.open(dest_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(source_file)
        except Exception as e:
            logging.error(f"Failed to compress log file {source_file}: {e}")


def cleanup_old_logs(log_dir: Path, retention_days: int) -> None:
    """Clean up log files older than retention period.

    Args:
        log_dir: Directory containing log files
        retention_days: Number of days to keep logs
    """
    if not log_dir.exists():
        return

    cutoff_time = time.time() - (retention_days * 86400)  # 86400 seconds in a day
    cleaned_count = 0

    try:
        for log_file in log_dir.glob("*.log*"):
            # Skip current log files (without numeric or date suffix)
            if log_file.suffix == ".log":
                continue

            # Check file modification time
            if os.path.getmtime(log_file) < cutoff_time:
                try:
                    os.remove(log_file)
                    cleaned_count += 1
                except Exception as e:
                    logging.error(f"Failed to remove old log file {log_file}: {e}")

        if cleaned_count > 0:
            logging.info(f"Cleaned up {cleaned_count} old log files")
    except Exception as e:
        logging.error(f"Error during log cleanup: {e}")


def check_disk_usage(log_dir: Path, threshold: float = 0.8) -> None:
    """Check disk usage for log directory and log warning if above threshold.

    Args:
        log_dir: Directory containing log files
        threshold: Usage threshold (0.0-1.0) to trigger warning
    """
    try:
        stat = os.statvfs(log_dir)
        # Calculate disk usage percentage
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        used = total - free
        usage_percent = used / total if total > 0 else 0

        if usage_percent >= threshold:
            logging.warning(
                "Log directory disk usage above threshold",
                extra={
                    "log_dir": str(log_dir),
                    "usage_percent": round(usage_percent * 100, 2),
                    "threshold_percent": round(threshold * 100, 2),
                    "used_bytes": used,
                    "total_bytes": total,
                },
            )
    except Exception as e:
        logging.error(f"Failed to check disk usage: {e}")


def setup_logging(
    environment: str = "development",
    log_level: str = "INFO",
    log_dir: str | None = None,
    enable_file_logging: bool = True,
    rotation_when: str = "midnight",
    rotation_interval: int = 1,
    max_bytes: int = 100 * 1024 * 1024,
    backup_count: int = 30,
    compress_rotated: bool = True,
    retention_days: int = 30,
    disk_usage_threshold: float = 0.8,
) -> None:
    """Configure structured JSON logging for the application.

    Args:
        environment: Environment name (development, staging, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        enable_file_logging: Whether to enable file logging (default: True)
        rotation_when: When to rotate logs (midnight, H, D, W0-W6)
        rotation_interval: Rotation interval (e.g., 1 for daily)
        max_bytes: Max log file size before rotation
        backup_count: Number of backup log files to keep
        compress_rotated: Whether to compress rotated files with gzip
        retention_days: Number of days to keep logs before deletion
        disk_usage_threshold: Disk usage threshold for warnings (0.0-1.0)
    """
    # Determine log level based on environment
    level_map = {
        "development": "DEBUG",
        "staging": "INFO",
        "production": "WARNING",
    }
    effective_level = log_level.upper() if log_level else level_map.get(environment, "INFO")

    # Create custom JSON formatter
    formatter = CustomJsonFormatter(
        fmt="%(timestamp)s %(level)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_level)
    root_logger.handlers.clear()  # Clear any existing handlers

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handlers (if enabled and log_dir provided)
    if enable_file_logging:
        log_path = Path(log_dir) if log_dir else Path("./logs")
        log_path.mkdir(parents=True, exist_ok=True)

        # Clean up old logs on startup
        cleanup_old_logs(log_path, retention_days)

        # Check disk usage
        check_disk_usage(log_path, disk_usage_threshold)

        # Application log file with time-based rotation
        app_log_file = log_path / "app.log"
        app_handler = CompressingTimedRotatingFileHandler(
            app_log_file,
            when=rotation_when,
            interval=rotation_interval,
            backupCount=backup_count,
            encoding="utf-8",
            compress=compress_rotated,
        )
        app_handler.setLevel(effective_level)
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)

        # Error log file with time-based rotation (WARNING and above)
        error_log_file = log_path / "error.log"
        error_handler = CompressingTimedRotatingFileHandler(
            error_log_file,
            when=rotation_when,
            interval=rotation_interval,
            backupCount=backup_count,
            encoding="utf-8",
            compress=compress_rotated,
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # Access log file with size-based rotation for high-volume logs
        access_log_file = log_path / "access.log"
        access_handler = CompressingRotatingFileHandler(
            access_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
            compress=compress_rotated,
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(formatter)
        # Only add to api logger, not root
        api_logger = logging.getLogger("api")
        api_logger.addHandler(access_handler)

    # Configure specific loggers with appropriate levels
    configure_logger("app", effective_level)
    configure_logger("workers", effective_level)
    configure_logger("ffmpeg", effective_level)
    configure_logger("api", effective_level)

    # Suppress noisy third-party loggers in production
    if environment == "production":
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("redis").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured",
        extra={
            "environment": environment,
            "log_level": effective_level,
            "file_logging": enable_file_logging,
            "log_dir": str(log_path) if enable_file_logging else None,
            "rotation_when": rotation_when,
            "backup_count": backup_count,
            "compress_rotated": compress_rotated,
            "retention_days": retention_days,
        },
    )


def configure_logger(logger_name: str, level: str) -> logging.Logger:
    """Configure a specific logger with the given level.

    Args:
        logger_name: Name of the logger
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    return logger


def set_request_id(request_id: str) -> None:
    """Set the request ID in context for all subsequent log entries.

    Args:
        request_id: Unique request identifier
    """
    request_id_ctx.set(request_id)


def set_composition_id(composition_id: str) -> None:
    """Set the composition ID in context for all subsequent log entries.

    Args:
        composition_id: Composition identifier
    """
    composition_id_ctx.set(composition_id)


def set_user_id(user_id: str) -> None:
    """Set the user ID in context for all subsequent log entries.

    Args:
        user_id: User identifier
    """
    user_id_ctx.set(user_id)


def set_job_id(job_id: str) -> None:
    """Set the job ID in context for all subsequent log entries.

    Args:
        job_id: Job identifier
    """
    job_id_ctx.set(job_id)


def clear_context() -> None:
    """Clear all context variables."""
    request_id_ctx.set(None)
    composition_id_ctx.set(None)
    user_id_ctx.set(None)
    job_id_ctx.set(None)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
