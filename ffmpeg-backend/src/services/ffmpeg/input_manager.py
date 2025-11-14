"""
Input File Management and Stream Detection for FFmpeg operations.

This module provides utilities for managing input files, detecting streams,
and validating media file properties using ffprobe.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StreamInfo:
    """Information about a media stream from ffprobe.

    Attributes:
        index: Stream index within the file
        codec_type: Type of stream (video, audio, subtitle)
        codec_name: Codec name (h264, aac, etc.)
        width: Video width in pixels (video streams only)
        height: Video height in pixels (video streams only)
        fps: Frame rate (video streams only)
        duration: Stream duration in seconds
        bit_rate: Bitrate in bits per second
        sample_rate: Audio sample rate (audio streams only)
        channels: Number of audio channels (audio streams only)
    """

    index: int
    codec_type: str
    codec_name: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    duration: float | None = None
    bit_rate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None

    @property
    def is_video(self) -> bool:
        """Check if this is a video stream."""
        return self.codec_type == "video"

    @property
    def is_audio(self) -> bool:
        """Check if this is an audio stream."""
        return self.codec_type == "audio"

    @property
    def is_subtitle(self) -> bool:
        """Check if this is a subtitle stream."""
        return self.codec_type == "subtitle"

    @property
    def resolution(self) -> str | None:
        """Get resolution as WIDTHxHEIGHT string."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return None

    def __repr__(self) -> str:
        """String representation showing key stream info."""
        if self.is_video:
            return f"VideoStream[{self.index}]: {self.codec_name} {self.resolution} @ {self.fps}fps"
        elif self.is_audio:
            return f"AudioStream[{self.index}]: {self.codec_name} {self.sample_rate}Hz {self.channels}ch"
        else:
            return f"Stream[{self.index}]: {self.codec_type} ({self.codec_name})"


@dataclass
class MediaFileInfo:
    """Complete information about a media file.

    Attributes:
        path: Path to the media file
        format_name: Container format (mp4, mov, avi, etc.)
        duration: Total duration in seconds
        size: File size in bytes
        bit_rate: Overall bitrate in bits per second
        streams: List of all streams in the file
    """

    path: Path
    format_name: str | None = None
    duration: float | None = None
    size: int | None = None
    bit_rate: int | None = None
    streams: list[StreamInfo] = None  # type: ignore

    def __post_init__(self) -> None:
        """Initialize streams list if not provided."""
        if self.streams is None:
            self.streams = []

    @property
    def video_streams(self) -> list[StreamInfo]:
        """Get all video streams."""
        return [s for s in self.streams if s.is_video]

    @property
    def audio_streams(self) -> list[StreamInfo]:
        """Get all audio streams."""
        return [s for s in self.streams if s.is_audio]

    @property
    def has_video(self) -> bool:
        """Check if file has video streams."""
        return len(self.video_streams) > 0

    @property
    def has_audio(self) -> bool:
        """Check if file has audio streams."""
        return len(self.audio_streams) > 0

    @property
    def primary_video_stream(self) -> StreamInfo | None:
        """Get the first video stream (usually the primary one)."""
        return self.video_streams[0] if self.video_streams else None

    @property
    def primary_audio_stream(self) -> StreamInfo | None:
        """Get the first audio stream (usually the primary one)."""
        return self.audio_streams[0] if self.audio_streams else None

    def __repr__(self) -> str:
        """String representation showing file summary."""
        return (
            f"MediaFile: {self.path.name} "
            f"({self.format_name}, {self.duration:.2f}s, "
            f"{len(self.video_streams)}V + {len(self.audio_streams)}A)"
        )


class InputFileManager:
    """
    Manager for input file operations including stream detection and validation.

    This class provides utilities for working with media files including:
    - Stream detection using ffprobe
    - File validation
    - Format and codec information extraction
    """

    def __init__(self, ffprobe_path: str = "ffprobe") -> None:
        """
        Initialize the input file manager.

        Args:
            ffprobe_path: Path to ffprobe executable (default: "ffprobe" from PATH)
        """
        self.ffprobe_path = ffprobe_path

    def probe_file(self, file_path: str | Path) -> MediaFileInfo:
        """
        Probe a media file and extract comprehensive information.

        Uses ffprobe to analyze the file and extract stream information,
        format details, and metadata.

        Args:
            file_path: Path to the media file

        Returns:
            MediaFileInfo object with complete file information

        Raises:
            FileNotFoundError: If file doesn't exist
            subprocess.CalledProcessError: If ffprobe fails
            ValueError: If ffprobe output is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {path}")

        # Run ffprobe to get JSON output
        cmd = [
            self.ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,  # 30 second timeout
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"ffprobe failed for {path}: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise ValueError(f"ffprobe timed out for {path}") from e

        # Parse JSON output
        try:
            probe_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid ffprobe output for {path}") from e

        # Extract format information
        format_info = probe_data.get("format", {})
        format_name = format_info.get("format_name")
        duration = float(format_info.get("duration", 0)) if format_info.get("duration") else None
        size = int(format_info.get("size", 0)) if format_info.get("size") else None
        bit_rate = int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None

        # Extract stream information
        streams: list[StreamInfo] = []
        for stream_data in probe_data.get("streams", []):
            stream = self._parse_stream_info(stream_data)
            if stream:
                streams.append(stream)

        return MediaFileInfo(
            path=path,
            format_name=format_name,
            duration=duration,
            size=size,
            bit_rate=bit_rate,
            streams=streams,
        )

    def _parse_stream_info(self, stream_data: dict[str, Any]) -> StreamInfo | None:
        """
        Parse stream information from ffprobe output.

        Args:
            stream_data: Stream data dict from ffprobe JSON

        Returns:
            StreamInfo object or None if parsing fails
        """
        try:
            index = int(stream_data.get("index", -1))
            codec_type = stream_data.get("codec_type", "unknown")
            codec_name = stream_data.get("codec_name")

            # Common fields
            duration = None
            if "duration" in stream_data:
                try:
                    duration = float(stream_data["duration"])
                except (ValueError, TypeError):
                    pass

            bit_rate = None
            if "bit_rate" in stream_data:
                try:
                    bit_rate = int(stream_data["bit_rate"])
                except (ValueError, TypeError):
                    pass

            # Video-specific fields
            width = int(stream_data.get("width", 0)) or None
            height = int(stream_data.get("height", 0)) or None

            # Frame rate calculation
            fps = None
            if "r_frame_rate" in stream_data:
                try:
                    # r_frame_rate is in format "30000/1001" or "30/1"
                    fps_parts = stream_data["r_frame_rate"].split("/")
                    if len(fps_parts) == 2:
                        numerator = float(fps_parts[0])
                        denominator = float(fps_parts[1])
                        if denominator > 0:
                            fps = numerator / denominator
                except (ValueError, ZeroDivisionError):
                    pass

            # Audio-specific fields
            sample_rate = None
            if "sample_rate" in stream_data:
                try:
                    sample_rate = int(stream_data["sample_rate"])
                except (ValueError, TypeError):
                    pass

            channels = int(stream_data.get("channels", 0)) or None

            return StreamInfo(
                index=index,
                codec_type=codec_type,
                codec_name=codec_name,
                width=width,
                height=height,
                fps=fps,
                duration=duration,
                bit_rate=bit_rate,
                sample_rate=sample_rate,
                channels=channels,
            )

        except Exception:
            # If parsing fails for any reason, return None
            return None

    def validate_file(
        self,
        file_path: str | Path,
        *,
        require_video: bool = False,
        require_audio: bool = False,
        max_duration: float | None = None,
        allowed_formats: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Validate a media file against requirements.

        Args:
            file_path: Path to the media file
            require_video: Require at least one video stream
            require_audio: Require at least one audio stream
            max_duration: Maximum allowed duration in seconds
            allowed_formats: List of allowed format names (e.g., ["mp4", "mov"])

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file meets all requirements
            - error_message: None if valid, otherwise description of validation failure
        """
        try:
            info = self.probe_file(file_path)
        except Exception as e:
            return False, f"Failed to probe file: {str(e)}"

        # Check video requirement
        if require_video and not info.has_video:
            return False, "File must contain at least one video stream"

        # Check audio requirement
        if require_audio and not info.has_audio:
            return False, "File must contain at least one audio stream"

        # Check duration
        if max_duration is not None and info.duration is not None:
            if info.duration > max_duration:
                return False, f"Duration {info.duration:.2f}s exceeds maximum {max_duration:.2f}s"

        # Check format
        if allowed_formats is not None and info.format_name is not None:
            # format_name can be comma-separated like "mov,mp4,m4a,3gp,3g2,mj2"
            file_formats = {fmt.strip() for fmt in info.format_name.split(",")}
            allowed_formats_set = {fmt.lower() for fmt in allowed_formats}

            if not file_formats.intersection(allowed_formats_set):
                return False, f"Format {info.format_name} not in allowed formats: {allowed_formats}"

        return True, None

    def get_stream_specifier(
        self,
        file_index: int,
        stream_type: str | None = None,
        stream_index: int = 0,
    ) -> str:
        """
        Generate an FFmpeg stream specifier string.

        Stream specifiers are used in FFmpeg to reference specific streams
        from input files in filters and output mapping.

        Args:
            file_index: Input file index (0, 1, 2, ...)
            stream_type: Stream type ("v" for video, "a" for audio, None for all)
            stream_index: Index within streams of that type (default: 0)

        Returns:
            Stream specifier string (e.g., "[0:v:0]", "[1:a]", "[2:v]")

        Examples:
            >>> manager.get_stream_specifier(0, "v", 0)  # First video stream of first input
            '[0:v:0]'
            >>> manager.get_stream_specifier(1, "a")  # First audio stream of second input
            '[1:a]'
            >>> manager.get_stream_specifier(2)  # All streams of third input
            '[2]'
        """
        if stream_type is None:
            return f"[{file_index}]"
        elif stream_index == 0:
            # Common case: first stream of type
            return f"[{file_index}:{stream_type}]"
        else:
            return f"[{file_index}:{stream_type}:{stream_index}]"
