"""Structured JSON logging configuration using pythonjsonlogger.

This module configures application-wide logging with structured JSON output
including contextual metadata like request IDs, composition IDs, and user IDs.
"""

import logging
import logging.handlers
import sys
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


def setup_logging(
    environment: str = "development",
    log_level: str = "INFO",
    log_dir: str | None = None,
    enable_file_logging: bool = True,
) -> None:
    """Configure structured JSON logging for the application.

    Args:
        environment: Environment name (development, staging, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        enable_file_logging: Whether to enable file logging (default: True)
    """
    # Determine log level based on environment
    level_map = {
        "development": "DEBUG",
        "staging": "INFO",
        "production": "WARNING",
    }
    effective_level = log_level if log_level else level_map.get(environment, "INFO")

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

        # Application log file with rotation
        app_log_file = log_path / "app.log"
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=10,
            encoding="utf-8",
        )
        app_handler.setLevel(effective_level)
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)

        # Error log file (WARNING and above)
        error_log_file = log_path / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=10,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

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
