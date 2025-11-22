"""Unit tests for structured JSON logging configuration."""

import json
import logging
from io import StringIO

import pytest

try:
    from app.logging_config import (
        CustomJsonFormatter,
        clear_context,
        get_logger,
        set_composition_id,
        set_job_id,
        set_request_id,
        set_user_id,
        setup_logging,
    )
except ImportError:
    from src.app.logging_config import (
        CustomJsonFormatter,
        clear_context,
        get_logger,
        set_composition_id,
        set_job_id,
        set_request_id,
        set_user_id,
        setup_logging,
    )


@pytest.fixture
def json_log_handler() -> tuple[logging.Handler, StringIO]:
    """Create a log handler that captures JSON output.

    Returns:
        Tuple of (handler, output stream)
    """
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(CustomJsonFormatter())
    return handler, stream


def test_custom_json_formatter_basic_fields(
    json_log_handler: tuple[logging.Handler, StringIO]
) -> None:
    """Test that CustomJsonFormatter includes all basic fields."""
    handler, stream = json_log_handler

    logger = logging.getLogger("test_logger")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    logger.info("Test message")

    output = stream.getvalue()
    log_entry = json.loads(output)

    # Check standard fields are present
    assert "timestamp" in log_entry
    assert "level" in log_entry
    assert log_entry["level"] == "INFO"
    assert "logger" in log_entry
    assert log_entry["logger"] == "test_logger"
    assert "module" in log_entry
    assert "function" in log_entry
    assert "line" in log_entry
    assert "process_id" in log_entry
    assert "thread_id" in log_entry
    assert "message" in log_entry
    assert log_entry["message"] == "Test message"


def test_custom_json_formatter_with_request_id(
    json_log_handler: tuple[logging.Handler, StringIO]
) -> None:
    """Test that request_id is included when set in context."""
    handler, stream = json_log_handler

    logger = logging.getLogger("test_logger_request")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    # Set request ID in context
    test_request_id = "test-request-123"
    set_request_id(test_request_id)

    logger.info("Request message")

    output = stream.getvalue()
    log_entry = json.loads(output)

    assert "request_id" in log_entry
    assert log_entry["request_id"] == test_request_id

    # Clean up
    clear_context()


def test_custom_json_formatter_with_all_context_variables(
    json_log_handler: tuple[logging.Handler, StringIO],
) -> None:
    """Test that all context variables are included when set."""
    handler, stream = json_log_handler

    logger = logging.getLogger("test_logger_full_context")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    # Set all context variables
    set_request_id("req-123")
    set_composition_id("comp-456")
    set_user_id("user-789")
    set_job_id("job-abc")

    logger.info("Full context message")

    output = stream.getvalue()
    log_entry = json.loads(output)

    assert log_entry["request_id"] == "req-123"
    assert log_entry["composition_id"] == "comp-456"
    assert log_entry["user_id"] == "user-789"
    assert log_entry["job_id"] == "job-abc"

    # Clean up
    clear_context()


def test_custom_json_formatter_with_extra_fields(
    json_log_handler: tuple[logging.Handler, StringIO],
) -> None:
    """Test that extra fields passed via logging are included."""
    handler, stream = json_log_handler

    logger = logging.getLogger("test_logger_extra")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    logger.info("Message with extras", extra={"custom_field": "custom_value", "count": 42})

    output = stream.getvalue()
    log_entry = json.loads(output)

    assert "custom_field" in log_entry
    assert log_entry["custom_field"] == "custom_value"
    assert "count" in log_entry
    assert log_entry["count"] == 42


def test_custom_json_formatter_with_exception(
    json_log_handler: tuple[logging.Handler, StringIO],
) -> None:
    """Test that exception information is properly formatted."""
    handler, stream = json_log_handler

    logger = logging.getLogger("test_logger_exception")
    logger.handlers = [handler]
    logger.setLevel(logging.ERROR)

    try:
        raise ValueError("Test error")
    except ValueError:
        logger.exception("An error occurred")

    output = stream.getvalue()
    log_entry = json.loads(output)

    assert "exception" in log_entry
    assert "type" in log_entry["exception"]
    assert log_entry["exception"]["type"] == "ValueError"
    assert "message" in log_entry["exception"]
    assert "Test error" in log_entry["exception"]["message"]
    assert "traceback" in log_entry["exception"]
    assert "ValueError: Test error" in log_entry["exception"]["traceback"]


def test_clear_context() -> None:
    """Test that clear_context removes all context variables."""
    # Set all context variables
    set_request_id("req-123")
    set_composition_id("comp-456")
    set_user_id("user-789")
    set_job_id("job-abc")

    # Clear context
    clear_context()

    # Create a log handler to verify context is cleared
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(CustomJsonFormatter())

    logger = logging.getLogger("test_logger_clear")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    logger.info("After clear")

    output = stream.getvalue()
    log_entry = json.loads(output)

    # Context variables should not be present after clearing
    assert "request_id" not in log_entry
    assert "composition_id" not in log_entry
    assert "user_id" not in log_entry
    assert "job_id" not in log_entry


def test_setup_logging_development() -> None:
    """Test logging setup for development environment."""
    setup_logging(environment="development", log_level="DEBUG", enable_file_logging=False)

    # Check that root logger is configured with DEBUG level
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG

    # Check that child loggers can log DEBUG messages
    logger = get_logger("test_dev")
    assert logger.isEnabledFor(logging.DEBUG)


def test_setup_logging_production() -> None:
    """Test logging setup for production environment."""
    setup_logging(environment="production", log_level="WARNING", enable_file_logging=False)

    _ = get_logger("test_prod")
    # Root logger level should be WARNING for production
    assert logging.getLogger().level == logging.WARNING


def test_get_logger() -> None:
    """Test get_logger returns a logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_context_variable_isolation() -> None:
    """Test that context variables are properly isolated per context."""
    # Set request ID
    set_request_id("req-1")

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(CustomJsonFormatter())

    logger = logging.getLogger("test_isolation")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    logger.info("First log")

    # Change request ID
    set_request_id("req-2")
    logger.info("Second log")

    output = stream.getvalue()
    lines = output.strip().split("\n")

    first_log = json.loads(lines[0])
    second_log = json.loads(lines[1])

    assert first_log["request_id"] == "req-1"
    assert second_log["request_id"] == "req-2"

    # Clean up
    clear_context()
