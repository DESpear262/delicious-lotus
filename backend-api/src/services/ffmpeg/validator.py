"""
Filter Chain Validation for FFmpeg.

This module provides utilities for validating FFmpeg filter chains,
detecting errors before execution, and ensuring filter graph correctness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class FilterValidationError:
    """Represents a validation error in a filter chain.

    Attributes:
        message: Error message
        filter_index: Index of the filter with the error (if applicable)
        severity: Error severity (error, warning)
    """

    message: str
    filter_index: int | None = None
    severity: str = "error"

    def __str__(self) -> str:
        """String representation."""
        if self.filter_index is not None:
            return f"[{self.severity.upper()}] Filter {self.filter_index}: {self.message}"
        return f"[{self.severity.upper()}] {self.message}"


@dataclass
class ValidationResult:
    """Result of filter chain validation.

    Attributes:
        is_valid: Whether the filter chain is valid
        errors: List of validation errors
        warnings: List of validation warnings
    """

    is_valid: bool
    errors: list[FilterValidationError]
    warnings: list[FilterValidationError]

    def __bool__(self) -> bool:
        """Boolean representation (True if valid)."""
        return self.is_valid

    def __str__(self) -> str:
        """String representation."""
        lines = [f"Valid: {self.is_valid}"]

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)


class FilterChainValidator:
    """
    Validator for FFmpeg filter chains.

    Provides validation for filter expressions to catch errors before
    FFmpeg execution, including syntax errors, invalid parameters,
    and graph connectivity issues.

    Example:
        >>> validator = FilterChainValidator()
        >>> result = validator.validate_filter_expression(
        ...     "[0:v][1:v]xfade=duration=1.0:offset=5.0[out]"
        ... )
        >>> if result.is_valid:
        ...     print("Filter is valid!")
    """

    # Common FFmpeg filter names
    KNOWN_FILTERS = frozenset(
        [
            "scale",
            "fps",
            "trim",
            "setpts",
            "fade",
            "xfade",
            "concat",
            "drawtext",
            "overlay",
            "amerge",
            "amix",
            "volume",
            "afade",
            "acrossfade",
            "sidechaincompress",
            "loudnorm",
            "pad",
            "crop",
            "hflip",
            "vflip",
            "rotate",
            "transpose",
            "null",
            "anull",
        ]
    )

    # Pattern for matching stream specifiers like [0:v], [1:a:0], [label]
    STREAM_SPEC_PATTERN = re.compile(r"\[([^\]]+)\]")

    # Pattern for matching filter syntax: [input]filter=params[output]
    FILTER_PATTERN = re.compile(
        r"(?P<inputs>\[(?:[^\]]+)\](?:\[(?:[^\]]+)\])*)"  # One or more inputs
        r"(?P<filter>\w+)"  # Filter name
        r"(?:=(?P<params>[^\[]+))?"  # Optional parameters
        r"(?P<outputs>\[(?:[^\]]+)\](?:\[(?:[^\]]+)\])*)"  # One or more outputs
    )

    def __init__(self) -> None:
        """Initialize the validator."""
        self.errors: list[FilterValidationError] = []
        self.warnings: list[FilterValidationError] = []

    def validate_filter_expression(self, filter_expr: str) -> ValidationResult:
        """
        Validate a complete filter expression.

        Args:
            filter_expr: FFmpeg filter expression to validate

        Returns:
            ValidationResult with errors and warnings

        Example:
            >>> result = validator.validate_filter_expression(
            ...     "[0:v]scale=1920:1080[v0];[v0]fps=30[out]"
            ... )
        """
        self.errors = []
        self.warnings = []

        if not filter_expr or not filter_expr.strip():
            self.errors.append(
                FilterValidationError("Filter expression is empty")
            )
            return self._create_result()

        # Split into individual filters (separated by semicolons)
        filter_parts = [f.strip() for f in filter_expr.split(";") if f.strip()]

        if not filter_parts:
            self.errors.append(
                FilterValidationError("No valid filters found in expression")
            )
            return self._create_result()

        # Validate each filter
        stream_labels: set[str] = set()
        output_labels: set[str] = set()

        for i, filter_part in enumerate(filter_parts):
            self._validate_filter_syntax(filter_part, i, stream_labels, output_labels)

        # Check for unused outputs
        for label in output_labels:
            if label not in stream_labels and not self._is_final_output(label):
                self.warnings.append(
                    FilterValidationError(
                        f"Output stream [{label}] is never used",
                        severity="warning",
                    )
                )

        return self._create_result()

    def _validate_filter_syntax(
        self,
        filter_part: str,
        index: int,
        stream_labels: set[str],
        output_labels: set[str],
    ) -> None:
        """
        Validate syntax of a single filter.

        Args:
            filter_part: Single filter expression
            index: Filter index for error reporting
            stream_labels: Set of stream labels seen so far (updated)
            output_labels: Set of output labels created (updated)
        """
        # Check for basic structure
        if "[" not in filter_part or "]" not in filter_part:
            self.errors.append(
                FilterValidationError(
                    "Filter must have input/output stream specifiers",
                    filter_index=index,
                )
            )
            return

        # Extract all stream specifiers
        specifiers = self.STREAM_SPEC_PATTERN.findall(filter_part)

        if not specifiers:
            self.errors.append(
                FilterValidationError(
                    "No stream specifiers found",
                    filter_index=index,
                )
            )
            return

        # Parse filter structure
        match = self.FILTER_PATTERN.search(filter_part)

        if not match:
            # Try simpler pattern for filters without parameters
            simple_pattern = re.compile(
                r"(?P<inputs>\[(?:[^\]]+)\](?:\[(?:[^\]]+)\])*)"
                r"(?P<filter>\w+)"
                r"(?P<outputs>\[(?:[^\]]+)\](?:\[(?:[^\]]+)\])*)"
            )
            match = simple_pattern.search(filter_part)

        if not match:
            self.errors.append(
                FilterValidationError(
                    f"Invalid filter syntax: {filter_part}",
                    filter_index=index,
                )
            )
            return

        filter_name = match.group("filter")

        # Check if filter name is known (warning only)
        if filter_name not in self.KNOWN_FILTERS:
            self.warnings.append(
                FilterValidationError(
                    f"Unknown or uncommon filter: {filter_name}",
                    filter_index=index,
                    severity="warning",
                )
            )

        # Extract inputs and outputs
        input_specs = self.STREAM_SPEC_PATTERN.findall(match.group("inputs"))
        output_specs = self.STREAM_SPEC_PATTERN.findall(match.group("outputs"))

        # Validate inputs reference existing streams
        for input_spec in input_specs:
            if not self._is_input_reference(input_spec) and input_spec not in output_labels:
                self.errors.append(
                    FilterValidationError(
                        f"Input stream [{input_spec}] not found",
                        filter_index=index,
                    )
                )
            stream_labels.add(input_spec)

        # Add outputs to available labels
        for output_spec in output_specs:
            if output_spec in output_labels:
                self.warnings.append(
                    FilterValidationError(
                        f"Output stream [{output_spec}] already exists (will be overwritten)",
                        filter_index=index,
                        severity="warning",
                    )
                )
            output_labels.add(output_spec)

        # Validate parameters if present
        if match.group("params"):
            self._validate_filter_params(filter_name, match.group("params"), index)

    def _validate_filter_params(
        self,
        filter_name: str,
        params: str,
        index: int,
    ) -> None:
        """
        Validate filter parameters.

        Args:
            filter_name: Name of the filter
            params: Parameter string
            index: Filter index for error reporting
        """
        # Basic parameter validation
        param_parts = params.split(":")

        for param in param_parts:
            if "=" not in param:
                # Some filters allow positional parameters
                continue

            key, value = param.split("=", 1)

            # Check for empty values
            if not value.strip():
                self.warnings.append(
                    FilterValidationError(
                        f"Empty value for parameter '{key}'",
                        filter_index=index,
                        severity="warning",
                    )
                )

    def _is_input_reference(self, spec: str) -> bool:
        """
        Check if a stream specifier references an input file.

        Args:
            spec: Stream specifier (e.g., "0:v", "1:a:0")

        Returns:
            True if it's an input reference
        """
        # Input references are numeric like "0:v" or "1:a"
        return spec[0].isdigit() or ":" in spec

    def _is_final_output(self, label: str) -> bool:
        """
        Check if a label is a final output label.

        Args:
            label: Stream label

        Returns:
            True if it's a common final output label
        """
        # Common final output labels
        final_labels = {"out", "outv", "outa", "final", "v", "a", "vout", "aout"}
        return label.lower() in final_labels

    def _create_result(self) -> ValidationResult:
        """
        Create validation result from accumulated errors/warnings.

        Returns:
            ValidationResult object
        """
        is_valid = len(self.errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=self.errors.copy(),
            warnings=self.warnings.copy(),
        )

    def validate_resolution(
        self,
        width: int,
        height: int,
        max_width: int = 3840,
        max_height: int = 2160,
    ) -> ValidationResult:
        """
        Validate video resolution.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            max_width: Maximum allowed width (default: 4K)
            max_height: Maximum allowed height (default: 4K)

        Returns:
            ValidationResult
        """
        self.errors = []
        self.warnings = []

        if width <= 0 or height <= 0:
            self.errors.append(
                FilterValidationError("Resolution dimensions must be positive")
            )

        if width > max_width or height > max_height:
            self.errors.append(
                FilterValidationError(
                    f"Resolution {width}x{height} exceeds maximum {max_width}x{max_height}"
                )
            )

        # Check for reasonable aspect ratios
        aspect_ratio = width / height if height > 0 else 0

        if aspect_ratio > 4.0 or aspect_ratio < 0.25:
            self.warnings.append(
                FilterValidationError(
                    f"Unusual aspect ratio: {aspect_ratio:.2f}",
                    severity="warning",
                )
            )

        return self._create_result()

    def validate_framerate(
        self,
        fps: float,
        min_fps: float = 1.0,
        max_fps: float = 120.0,
    ) -> ValidationResult:
        """
        Validate frame rate.

        Args:
            fps: Frame rate in frames per second
            min_fps: Minimum allowed FPS
            max_fps: Maximum allowed FPS

        Returns:
            ValidationResult
        """
        self.errors = []
        self.warnings = []

        if fps <= 0:
            self.errors.append(
                FilterValidationError("Frame rate must be positive")
            )
        elif fps < min_fps:
            self.errors.append(
                FilterValidationError(f"Frame rate {fps} below minimum {min_fps}")
            )
        elif fps > max_fps:
            self.errors.append(
                FilterValidationError(f"Frame rate {fps} exceeds maximum {max_fps}")
            )

        # Common frame rates
        common_fps = {23.976, 24, 25, 29.97, 30, 50, 59.94, 60}

        if not any(abs(fps - common) < 0.01 for common in common_fps):
            self.warnings.append(
                FilterValidationError(
                    f"Unusual frame rate: {fps} FPS",
                    severity="warning",
                )
            )

        return self._create_result()
