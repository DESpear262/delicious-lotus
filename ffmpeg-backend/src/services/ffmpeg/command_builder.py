"""
FFmpeg Command Builder - Core class for building complex FFmpeg commands.

This module provides a fluent API for constructing FFmpeg commands with support for:
- Multiple input files with automatic indexing
- Complex filter graphs (transitions, overlays, etc.)
- Audio mixing and processing
- H.264 encoding with quality control
- Security and validation
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InputFile:
    """Represents an FFmpeg input file with metadata and options.

    Attributes:
        path: Path to the input file
        index: Automatic index assigned by FFmpeg (0, 1, 2, ...)
        options: Dict of input-specific options (e.g., -ss, -t, -f)
        label: Optional label for referencing in filters
    """

    path: str | Path
    index: int
    options: dict[str, Any] = field(default_factory=dict)
    label: str | None = None

    def __str__(self) -> str:
        """String representation showing index and path."""
        return f"Input[{self.index}]: {self.path}"


@dataclass
class OutputFile:
    """Represents an FFmpeg output file with encoding settings.

    Attributes:
        path: Path to the output file
        options: Dict of output-specific options (codec, quality, etc.)
    """

    path: str | Path
    options: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation showing path."""
        return f"Output: {self.path}"


class FFmpegCommandBuilder:
    """
    Fluent API builder for constructing complex FFmpeg commands.

    This class provides a chainable interface for building FFmpeg commands with
    proper escaping, validation, and support for advanced features like filter
    complex graphs, audio mixing, and transitions.

    Example:
        >>> builder = FFmpegCommandBuilder()
        >>> command = (
        ...     builder
        ...     .add_input("video1.mp4")
        ...     .add_input("video2.mp4")
        ...     .add_global_option("-y")  # Overwrite output
        ...     .set_output("output.mp4", codec="libx264", crf=21)
        ...     .build()
        ... )
        >>> print(command)
        ffmpeg -y -i video1.mp4 -i video2.mp4 -c:v libx264 -crf 21 output.mp4
    """

    def __init__(self) -> None:
        """Initialize the command builder with empty component lists."""
        self._global_options: list[str] = []
        self._inputs: list[InputFile] = []
        self._output: OutputFile | None = None
        self._filter_complex: list[str] = []
        self._video_codec: str | None = None
        self._audio_codec: str | None = None
        self._additional_output_options: dict[str, Any] = {}

    def add_global_option(self, option: str, value: str | None = None) -> FFmpegCommandBuilder:
        """
        Add a global FFmpeg option (before inputs).

        Global options affect the entire FFmpeg process, such as:
        - -y: Overwrite output files
        - -n: Never overwrite output files
        - -loglevel: Set logging level

        Args:
            option: The option flag (e.g., "-y", "-loglevel")
            value: Optional value for the option (e.g., "quiet" for -loglevel)

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_global_option("-y")  # Overwrite without asking
            >>> builder.add_global_option("-loglevel", "error")
        """
        self._global_options.append(option)
        if value is not None:
            self._global_options.append(value)
        return self

    def add_input(
        self,
        path: str | Path,
        *,
        label: str | None = None,
        seek: float | None = None,
        duration: float | None = None,
        format: str | None = None,
        **options: Any,
    ) -> FFmpegCommandBuilder:
        """
        Add an input file to the command.

        Inputs are automatically assigned sequential indices (0, 1, 2, ...) which
        can be referenced in filter expressions.

        Args:
            path: Path to the input file
            label: Optional label for referencing in filters (default: None)
            seek: Start position in seconds (-ss option)
            duration: Duration to process in seconds (-t option)
            format: Force input format (-f option)
            **options: Additional input-specific options

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_input("video.mp4", seek=10.0, duration=30.0)
            >>> builder.add_input("audio.mp3", label="background_music")
        """
        input_options: dict[str, Any] = {}

        # Add common options
        if seek is not None:
            input_options["-ss"] = str(seek)
        if duration is not None:
            input_options["-t"] = str(duration)
        if format is not None:
            input_options["-f"] = format

        # Merge with additional options
        input_options.update(options)

        # Create input file with auto-assigned index
        input_file = InputFile(
            path=path,
            index=len(self._inputs),  # Auto-increment index
            options=input_options,
            label=label,
        )

        self._inputs.append(input_file)
        return self

    def set_output(
        self,
        path: str | Path,
        *,
        codec: str | None = None,
        crf: int | None = None,
        preset: str | None = None,
        **options: Any,
    ) -> FFmpegCommandBuilder:
        """
        Set the output file and encoding parameters.

        Args:
            path: Path to the output file
            codec: Video codec (e.g., "libx264", "libx265")
            crf: Constant Rate Factor for quality (18-28 recommended)
            preset: Encoding preset (e.g., "ultrafast", "medium", "slow")
            **options: Additional output-specific options

        Returns:
            Self for method chaining

        Example:
            >>> builder.set_output("output.mp4", codec="libx264", crf=21, preset="medium")
        """
        output_options: dict[str, Any] = {}

        # Video codec
        if codec is not None:
            output_options["-c:v"] = codec
            self._video_codec = codec

        # CRF quality
        if crf is not None:
            output_options["-crf"] = str(crf)

        # Encoding preset
        if preset is not None:
            output_options["-preset"] = preset

        # Merge with additional options
        output_options.update(options)

        self._output = OutputFile(path=path, options=output_options)
        self._additional_output_options = output_options
        return self

    def add_filter_complex(self, filter_expression: str) -> FFmpegCommandBuilder:
        """
        Add a filter complex expression.

        Filter complex allows combining and processing multiple streams with
        advanced filters like transitions, overlays, and audio mixing.

        Args:
            filter_expression: FFmpeg filter complex expression

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_filter_complex("[0:v][1:v]concat=n=2:v=1:a=0[outv]")
        """
        self._filter_complex.append(filter_expression)
        return self

    def set_video_codec(self, codec: str, **options: Any) -> FFmpegCommandBuilder:
        """
        Set video codec and related options.

        Args:
            codec: Video codec name (e.g., "libx264", "libx265", "copy")
            **options: Codec-specific options

        Returns:
            Self for method chaining
        """
        self._video_codec = codec
        self._additional_output_options["-c:v"] = codec
        self._additional_output_options.update(options)
        return self

    def set_audio_codec(self, codec: str, **options: Any) -> FFmpegCommandBuilder:
        """
        Set audio codec and related options.

        Args:
            codec: Audio codec name (e.g., "aac", "mp3", "copy")
            **options: Codec-specific options

        Returns:
            Self for method chaining
        """
        self._audio_codec = codec
        self._additional_output_options["-c:a"] = codec
        self._additional_output_options.update(options)
        return self

    def _escape_path(self, path: str | Path) -> str:
        """
        Safely escape a file path for shell execution.

        Uses shlex.quote to prevent command injection attacks.

        Args:
            path: File path to escape

        Returns:
            Safely escaped path string
        """
        return shlex.quote(str(path))

    def _build_input_args(self) -> list[str]:
        """
        Build the input arguments portion of the command.

        Returns:
            List of command arguments for inputs
        """
        args: list[str] = []

        for input_file in self._inputs:
            # Add input-specific options before the -i flag
            for key, value in input_file.options.items():
                args.append(key)
                if isinstance(value, bool):
                    # Boolean flags don't need values
                    continue
                args.append(str(value))

            # Add -i flag and escaped path
            args.append("-i")
            args.append(self._escape_path(input_file.path))

        return args

    def _build_filter_complex_args(self) -> list[str]:
        """
        Build the filter complex arguments.

        Returns:
            List of command arguments for filter complex
        """
        if not self._filter_complex:
            return []

        # Join all filter expressions with semicolons
        filter_expression = ";".join(self._filter_complex)

        return ["-filter_complex", shlex.quote(filter_expression)]

    def _build_output_args(self) -> list[str]:
        """
        Build the output arguments portion of the command.

        Returns:
            List of command arguments for output

        Raises:
            ValueError: If no output file is set
        """
        if self._output is None:
            raise ValueError("Output file must be set before building command")

        args: list[str] = []

        # Add output options
        for key, value in self._output.options.items():
            args.append(key)
            if isinstance(value, bool):
                # Boolean flags don't need values
                continue
            args.append(str(value))

        # Add output path (escaped)
        args.append(self._escape_path(self._output.path))

        return args

    def build(self) -> str:
        """
        Build the complete FFmpeg command string.

        Returns:
            Complete FFmpeg command ready for execution

        Raises:
            ValueError: If required components are missing (e.g., no output)

        Example:
            >>> command = builder.build()
            >>> print(command)
            ffmpeg -y -i input.mp4 -c:v libx264 -crf 21 output.mp4
        """
        if self._output is None:
            raise ValueError("Cannot build command without output file")

        if not self._inputs:
            raise ValueError("Cannot build command without input files")

        # Start with ffmpeg command
        parts: list[str] = ["ffmpeg"]

        # Add global options
        parts.extend(self._global_options)

        # Add inputs
        parts.extend(self._build_input_args())

        # Add filter complex (if any)
        parts.extend(self._build_filter_complex_args())

        # Add output
        parts.extend(self._build_output_args())

        # Join all parts into final command
        return " ".join(parts)

    def build_args(self) -> list[str]:
        """
        Build the command as a list of arguments (for subprocess execution).

        This is safer than build() for subprocess execution as it avoids
        shell interpretation issues.

        Returns:
            List of command arguments

        Example:
            >>> args = builder.build_args()
            >>> subprocess.run(args)
        """
        if self._output is None:
            raise ValueError("Cannot build command without output file")

        if not self._inputs:
            raise ValueError("Cannot build command without input files")

        args: list[str] = ["ffmpeg"]

        # Add global options
        args.extend(self._global_options)

        # Add inputs (without shell escaping for subprocess)
        for input_file in self._inputs:
            for key, value in input_file.options.items():
                args.append(key)
                if not isinstance(value, bool):
                    args.append(str(value))
            args.append("-i")
            args.append(str(input_file.path))

        # Add filter complex
        if self._filter_complex:
            filter_expression = ";".join(self._filter_complex)
            args.extend(["-filter_complex", filter_expression])

        # Add output
        for key, value in self._output.options.items():
            args.append(key)
            if not isinstance(value, bool):
                args.append(str(value))
        args.append(str(self._output.path))

        return args

    def get_input_count(self) -> int:
        """
        Get the number of input files.

        Returns:
            Number of inputs added to the builder
        """
        return len(self._inputs)

    def get_input_by_index(self, index: int) -> InputFile | None:
        """
        Get an input file by its index.

        Args:
            index: Index of the input file (0-based)

        Returns:
            InputFile if found, None otherwise
        """
        if 0 <= index < len(self._inputs):
            return self._inputs[index]
        return None

    def get_input_by_label(self, label: str) -> InputFile | None:
        """
        Get an input file by its label.

        Args:
            label: Label of the input file

        Returns:
            InputFile if found, None otherwise
        """
        for input_file in self._inputs:
            if input_file.label == label:
                return input_file
        return None

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"FFmpegCommandBuilder("
            f"inputs={len(self._inputs)}, "
            f"output={self._output.path if self._output else None}, "
            f"filters={len(self._filter_complex)})"
        )
