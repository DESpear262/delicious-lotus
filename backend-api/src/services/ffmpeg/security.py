"""
Security and Validation for FFmpeg Command Building.

This module provides utilities for safely escaping command arguments,
validating inputs, and preventing injection attacks.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any


class FFmpegSecurityError(Exception):
    """Exception raised for security violations in FFmpeg commands."""

    pass


class FFmpegCommandValidator:
    """
    Validator for FFmpeg commands and arguments.

    Provides security checks to prevent command injection and ensure
    safe command execution.
    """

    # Dangerous shell metacharacters
    SHELL_METACHARACTERS = frozenset([";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"])

    # Allowed FFmpeg option prefixes
    ALLOWED_OPTION_PREFIXES = frozenset(["-", "--"])

    # Maximum reasonable length for various inputs
    MAX_PATH_LENGTH = 4096
    MAX_FILTER_LENGTH = 32768  # 32KB for filter expressions
    MAX_COMMAND_LENGTH = 65536  # 64KB for entire command

    # Dangerous path patterns
    DANGEROUS_PATH_PATTERNS = [
        re.compile(r"\.\."),  # Parent directory traversal
        re.compile(r"~"),  # Home directory expansion
        re.compile(r"\$"),  # Variable expansion
        re.compile(r"`"),  # Command substitution
    ]

    def __init__(self, strict_mode: bool = True) -> None:
        """
        Initialize the validator.

        Args:
            strict_mode: Enable strict validation (reject more edge cases)
        """
        self.strict_mode = strict_mode

    def escape_path(self, path: str | Path) -> str:
        """
        Safely escape a file path for shell execution.

        Uses shlex.quote to prevent shell injection attacks.

        Args:
            path: File path to escape

        Returns:
            Safely quoted path string

        Raises:
            FFmpegSecurityError: If path is invalid or dangerous
        """
        path_str = str(path)

        # Validate path length
        if len(path_str) > self.MAX_PATH_LENGTH:
            raise FFmpegSecurityError(f"Path too long: {len(path_str)} > {self.MAX_PATH_LENGTH}")

        # Check for dangerous patterns
        if self.strict_mode:
            for pattern in self.DANGEROUS_PATH_PATTERNS:
                if pattern.search(path_str):
                    raise FFmpegSecurityError(
                        f"Dangerous path pattern detected: {pattern.pattern}"
                    )

        # Use shlex.quote for safe escaping
        return shlex.quote(path_str)

    def validate_path(
        self,
        path: str | Path,
        must_exist: bool = False,
        allowed_extensions: list[str] | None = None,
    ) -> bool:
        """
        Validate a file path for security and correctness.

        Args:
            path: Path to validate
            must_exist: Whether the path must exist
            allowed_extensions: List of allowed file extensions (e.g., [".mp4", ".mov"])

        Returns:
            True if valid

        Raises:
            FFmpegSecurityError: If validation fails
        """
        path_obj = Path(path)
        path_str = str(path)

        # Length check
        if len(path_str) > self.MAX_PATH_LENGTH:
            raise FFmpegSecurityError(f"Path exceeds maximum length: {len(path_str)}")

        # Dangerous pattern check
        for pattern in self.DANGEROUS_PATH_PATTERNS:
            if pattern.search(path_str):
                raise FFmpegSecurityError(
                    f"Path contains dangerous pattern: {pattern.pattern}"
                )

        # Shell metacharacter check
        for char in self.SHELL_METACHARACTERS:
            if char in path_str:
                raise FFmpegSecurityError(f"Path contains shell metacharacter: {repr(char)}")

        # Null byte check
        if "\x00" in path_str:
            raise FFmpegSecurityError("Path contains null byte")

        # Existence check
        if must_exist and not path_obj.exists():
            raise FFmpegSecurityError(f"Path does not exist: {path}")

        # Extension check
        if allowed_extensions is not None:
            extension = path_obj.suffix.lower()
            if extension not in [ext.lower() for ext in allowed_extensions]:
                raise FFmpegSecurityError(
                    f"File extension {extension} not in allowed list: {allowed_extensions}"
                )

        return True

    def validate_filter_expression(self, filter_expr: str) -> bool:
        """
        Validate an FFmpeg filter expression.

        Args:
            filter_expr: Filter expression to validate

        Returns:
            True if valid

        Raises:
            FFmpegSecurityError: If validation fails
        """
        # Length check
        if len(filter_expr) > self.MAX_FILTER_LENGTH:
            raise FFmpegSecurityError(
                f"Filter expression too long: {len(filter_expr)} > {self.MAX_FILTER_LENGTH}"
            )

        # Null byte check
        if "\x00" in filter_expr:
            raise FFmpegSecurityError("Filter expression contains null byte")

        # Check for suspicious command injection attempts
        if self.strict_mode:
            # Check for shell metacharacters that shouldn't be in filters
            dangerous_chars = {";", "&", "|", "`", "$", "<", ">"}
            for char in dangerous_chars:
                if char in filter_expr:
                    raise FFmpegSecurityError(
                        f"Filter expression contains suspicious character: {repr(char)}"
                    )

        return True

    def validate_option(self, option: str, value: Any | None = None) -> bool:
        """
        Validate an FFmpeg option flag.

        Args:
            option: Option flag (e.g., "-c:v", "--help")
            value: Optional value for the option

        Returns:
            True if valid

        Raises:
            FFmpegSecurityError: If validation fails
        """
        # Check option starts with - or --
        if not any(option.startswith(prefix) for prefix in self.ALLOWED_OPTION_PREFIXES):
            raise FFmpegSecurityError(
                f"Option must start with - or --, got: {option}"
            )

        # Check for shell metacharacters
        for char in self.SHELL_METACHARACTERS:
            if char in option:
                raise FFmpegSecurityError(
                    f"Option contains shell metacharacter: {repr(char)}"
                )

        # Validate value if provided
        if value is not None:
            value_str = str(value)

            # Null byte check
            if "\x00" in value_str:
                raise FFmpegSecurityError("Option value contains null byte")

            # Length check
            if len(value_str) > 10000:
                raise FFmpegSecurityError(f"Option value too long: {len(value_str)}")

        return True

    def validate_command_length(self, command: str | list[str]) -> bool:
        """
        Validate total command length.

        Args:
            command: Complete command string or argument list

        Returns:
            True if valid

        Raises:
            FFmpegSecurityError: If command is too long
        """
        if isinstance(command, list):
            command_str = " ".join(command)
        else:
            command_str = command

        if len(command_str) > self.MAX_COMMAND_LENGTH:
            raise FFmpegSecurityError(
                f"Command too long: {len(command_str)} > {self.MAX_COMMAND_LENGTH}"
            )

        return True

    def sanitize_text(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize user-provided text for use in filters (like drawtext).

        Args:
            text: Text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text

        Raises:
            FFmpegSecurityError: If text is invalid
        """
        # Length check
        if len(text) > max_length:
            raise FFmpegSecurityError(f"Text too long: {len(text)} > {max_length}")

        # Null byte check
        if "\x00" in text:
            raise FFmpegSecurityError("Text contains null byte")

        # Remove or escape control characters (except newline and tab)
        sanitized = "".join(
            char if (char.isprintable() or char in "\n\t") else "" for char in text
        )

        return sanitized


def safe_quote(value: Any) -> str:
    """
    Safely quote a value for shell execution.

    Args:
        value: Value to quote

    Returns:
        Safely quoted string
    """
    return shlex.quote(str(value))


def safe_join_args(args: list[str]) -> str:
    """
    Safely join command arguments into a shell command string.

    Args:
        args: List of command arguments

    Returns:
        Shell-safe command string
    """
    return " ".join(shlex.quote(arg) for arg in args)


def validate_duration(duration: float, max_duration: float = 3600.0) -> bool:
    """
    Validate a duration value.

    Args:
        duration: Duration in seconds
        max_duration: Maximum allowed duration (default: 1 hour)

    Returns:
        True if valid

    Raises:
        FFmpegSecurityError: If duration is invalid
    """
    if duration < 0:
        raise FFmpegSecurityError(f"Duration cannot be negative: {duration}")

    if duration > max_duration:
        raise FFmpegSecurityError(f"Duration too long: {duration} > {max_duration}")

    return True


def validate_numeric_range(
    value: int | float,
    min_value: int | float,
    max_value: int | float,
    name: str = "value",
) -> bool:
    """
    Validate a numeric value is within range.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        name: Name of the value (for error messages)

    Returns:
        True if valid

    Raises:
        FFmpegSecurityError: If value is out of range
    """
    if value < min_value or value > max_value:
        raise FFmpegSecurityError(
            f"{name} must be between {min_value} and {max_value}, got {value}"
        )

    return True
