"""
FFmpeg Progress Parser for real-time progress calculation.

This module parses FFmpeg stderr output to extract progress information
including frame numbers, timecodes, processing speed, and calculates ETA.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass


@dataclass
class FFmpegProgress:
    """
    FFmpeg progress information extracted from output.

    Attributes:
        frame: Current frame number
        fps: Current processing frames per second
        bitrate: Current bitrate in kbps
        total_size: Total size processed in bytes
        out_time_ms: Output time in milliseconds
        speed: Processing speed multiplier (1.0x, 2.5x, etc.)
        progress_percent: Calculated progress percentage (0-100)
        eta_seconds: Estimated time to completion in seconds
    """

    frame: int = 0
    fps: float = 0.0
    bitrate: float = 0.0
    total_size: int = 0
    out_time_ms: int = 0
    speed: float = 0.0
    progress_percent: float = 0.0
    eta_seconds: float | None = None

    @property
    def out_time_seconds(self) -> float:
        """Get output time in seconds."""
        return self.out_time_ms / 1000000.0 if self.out_time_ms > 0 else 0.0

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FFmpegProgress(frame={self.frame}, fps={self.fps:.1f}, "
            f"speed={self.speed:.2f}x, progress={self.progress_percent:.1f}%)"
        )


class FFmpegProgressParser:
    """
    Parser for FFmpeg stderr output to extract progress information.

    FFmpeg outputs progress information to stderr in this format:
    ```
    frame=   42 fps=0.0 q=-1.0 size=       0kB time=00:00:01.40 bitrate=   0.3kbits/s speed=2.79x
    ```

    This parser extracts these values and calculates completion percentage
    based on expected total duration.

    Example:
        >>> parser = FFmpegProgressParser(total_duration=120.0)
        >>> progress = parser.parse_line("frame=  100 fps=30 q=-1.0 size=1024kB time=00:00:03.33 bitrate=2510.3kbits/s speed=1.0x")
        >>> print(f"Progress: {progress.progress_percent:.1f}%")
        Progress: 2.8%
    """

    # Regex patterns for parsing FFmpeg output
    FRAME_PATTERN = re.compile(r"frame=\s*(\d+)")
    FPS_PATTERN = re.compile(r"fps=\s*([\d.]+)")
    BITRATE_PATTERN = re.compile(r"bitrate=\s*([\d.]+)kbits/s")
    SIZE_PATTERN = re.compile(r"size=\s*(\d+)kB")
    TIME_PATTERN = re.compile(r"time=\s*(\d{2}):(\d{2}):([\d.]+)")
    SPEED_PATTERN = re.compile(r"speed=\s*([\d.]+)x")

    def __init__(
        self,
        total_duration: float | None = None,
        window_size: int = 10,
    ) -> None:
        """
        Initialize the progress parser.

        Args:
            total_duration: Expected total duration in seconds (for % calculation)
            window_size: Number of samples for rolling average calculation
        """
        self.total_duration = total_duration
        self.window_size = window_size

        # Rolling window for ETA calculation
        self._speed_window: deque[float] = deque(maxlen=window_size)
        self._last_progress = FFmpegProgress()

    def parse_line(self, line: str) -> FFmpegProgress | None:  # noqa: C901
        """
        Parse a single line of FFmpeg stderr output.

        Args:
            line: Line of FFmpeg stderr output

        Returns:
            FFmpegProgress object if progress info found, None otherwise

        Example:
            >>> parser = FFmpegProgressParser(total_duration=120.0)
            >>> line = "frame=  100 fps=30 time=00:00:03.33 bitrate=2510.3kbits/s speed=1.0x"
            >>> progress = parser.parse_line(line)
            >>> progress.frame
            100
        """
        # Skip lines that don't contain progress info
        if "frame=" not in line:
            return None

        progress = FFmpegProgress()

        # Extract frame number
        frame_match = self.FRAME_PATTERN.search(line)
        if frame_match:
            progress.frame = int(frame_match.group(1))

        # Extract FPS
        fps_match = self.FPS_PATTERN.search(line)
        if fps_match:
            progress.fps = float(fps_match.group(1))

        # Extract bitrate
        bitrate_match = self.BITRATE_PATTERN.search(line)
        if bitrate_match:
            progress.bitrate = float(bitrate_match.group(1))

        # Extract size
        size_match = self.SIZE_PATTERN.search(line)
        if size_match:
            progress.total_size = int(size_match.group(1)) * 1024  # Convert kB to bytes

        # Extract time
        time_match = self.TIME_PATTERN.search(line)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            # Convert to microseconds for compatibility
            total_seconds = hours * 3600 + minutes * 60 + seconds
            progress.out_time_ms = int(total_seconds * 1000000)

        # Extract speed
        speed_match = self.SPEED_PATTERN.search(line)
        if speed_match:
            progress.speed = float(speed_match.group(1))
            # Add to rolling window for ETA calculation
            if progress.speed > 0:
                self._speed_window.append(progress.speed)

        # Calculate progress percentage if total duration known
        if self.total_duration and self.total_duration > 0:
            current_time = progress.out_time_seconds
            progress.progress_percent = min(100.0, (current_time / self.total_duration) * 100.0)

            # Calculate ETA using rolling average of speed
            if len(self._speed_window) > 0:
                avg_speed = sum(self._speed_window) / len(self._speed_window)
                if avg_speed > 0:
                    remaining_time = self.total_duration - current_time
                    progress.eta_seconds = remaining_time / avg_speed

        # Store as last progress
        self._last_progress = progress

        return progress

    def parse_duration_line(self, line: str) -> float | None:
        """
        Parse FFmpeg output to extract duration information.

        FFmpeg prints duration in format:
        "Duration: 00:02:30.45, start: 0.000000, bitrate: 1234 kb/s"

        Args:
            line: Line of FFmpeg stderr output

        Returns:
            Duration in seconds if found, None otherwise

        Example:
            >>> parser = FFmpegProgressParser()
            >>> duration = parser.parse_duration_line("Duration: 00:02:30.45")
            >>> duration
            150.45
        """
        duration_pattern = re.compile(r"Duration:\s*(\d{2}):(\d{2}):([\d.]+)")
        match = duration_pattern.search(line)

        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds

        return None

    def set_total_duration(self, duration: float) -> None:
        """
        Set the total duration for progress calculation.

        Args:
            duration: Total duration in seconds
        """
        self.total_duration = duration

    def get_last_progress(self) -> FFmpegProgress:
        """
        Get the last parsed progress information.

        Returns:
            Last FFmpegProgress object
        """
        return self._last_progress

    def reset(self) -> None:
        """Reset parser state."""
        self._speed_window.clear()
        self._last_progress = FFmpegProgress()


class MultiStageProgressParser:
    """
    Progress parser for multi-stage FFmpeg processing.

    Some operations require multiple FFmpeg passes (e.g., two-pass encoding,
    normalization + composition). This class manages progress across multiple
    stages with weighted progress calculation.

    Example:
        >>> # Define stages: normalization (20%), composition (60%), encoding (20%)
        >>> parser = MultiStageProgressParser(
        ...     stage_weights={"normalize": 0.2, "compose": 0.6, "encode": 0.2}
        ... )
        >>> parser.set_stage("normalize", duration=120.0)
        >>> progress = parser.parse_line("frame=  100 fps=30 time=00:00:03.33 speed=1.0x")
        >>> print(f"Overall progress: {progress.progress_percent:.1f}%")
        Overall progress: 0.6%
    """

    def __init__(
        self,
        stage_weights: dict[str, float] | None = None,
        window_size: int = 10,
    ) -> None:
        """
        Initialize multi-stage progress parser.

        Args:
            stage_weights: Dictionary mapping stage names to weights (must sum to 1.0)
            window_size: Number of samples for rolling average

        Raises:
            ValueError: If stage weights don't sum to 1.0
        """
        self.stage_weights = stage_weights or {}
        self.window_size = window_size

        # Validate weights sum to 1.0
        if self.stage_weights:
            total_weight = sum(self.stage_weights.values())
            if not (0.99 <= total_weight <= 1.01):  # Allow small float precision errors
                raise ValueError(f"Stage weights must sum to 1.0, got {total_weight}")

        self.current_stage: str | None = None
        self.stage_parsers: dict[str, FFmpegProgressParser] = {}
        self.stage_progress: dict[str, float] = {stage: 0.0 for stage in self.stage_weights}

    def set_stage(
        self,
        stage_name: str,
        duration: float | None = None,
    ) -> None:
        """
        Set the current processing stage.

        Args:
            stage_name: Name of the current stage
            duration: Expected duration for this stage in seconds

        Raises:
            ValueError: If stage_name not in defined weights
        """
        if self.stage_weights and stage_name not in self.stage_weights:
            raise ValueError(f"Unknown stage: {stage_name}")

        self.current_stage = stage_name

        # Create parser for this stage if not exists
        if stage_name not in self.stage_parsers:
            self.stage_parsers[stage_name] = FFmpegProgressParser(
                total_duration=duration,
                window_size=self.window_size,
            )
        elif duration is not None:
            # Update duration if provided
            self.stage_parsers[stage_name].set_total_duration(duration)

    def parse_line(self, line: str) -> FFmpegProgress | None:
        """
        Parse FFmpeg output line and calculate overall progress.

        Args:
            line: Line of FFmpeg stderr output

        Returns:
            FFmpegProgress with overall progress percentage

        Raises:
            RuntimeError: If no current stage set
        """
        if self.current_stage is None:
            raise RuntimeError("No current stage set. Call set_stage() first.")

        # Parse using current stage's parser
        parser = self.stage_parsers[self.current_stage]
        progress = parser.parse_line(line)

        if progress is None:
            return None

        # Update stage progress
        self.stage_progress[self.current_stage] = progress.progress_percent

        # Calculate overall progress as weighted sum
        if self.stage_weights:
            overall_progress = 0.0
            for stage_name, weight in self.stage_weights.items():
                stage_pct = self.stage_progress.get(stage_name, 0.0)
                overall_progress += stage_pct * weight

            # Create new progress object with overall percentage
            overall = FFmpegProgress(
                frame=progress.frame,
                fps=progress.fps,
                bitrate=progress.bitrate,
                total_size=progress.total_size,
                out_time_ms=progress.out_time_ms,
                speed=progress.speed,
                progress_percent=overall_progress,
                eta_seconds=progress.eta_seconds,  # ETA for current stage only
            )

            return overall

        return progress

    def get_overall_progress(self) -> float:
        """
        Get current overall progress percentage.

        Returns:
            Overall progress (0-100)
        """
        if not self.stage_weights:
            return 0.0

        overall = 0.0
        for stage_name, weight in self.stage_weights.items():
            stage_pct = self.stage_progress.get(stage_name, 0.0)
            overall += stage_pct * weight

        return overall

    def get_stage_progress(self, stage_name: str) -> float:
        """
        Get progress for a specific stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Progress percentage for that stage (0-100)
        """
        return self.stage_progress.get(stage_name, 0.0)

    def reset(self) -> None:
        """Reset all stage parsers and progress."""
        self.current_stage = None
        for parser in self.stage_parsers.values():
            parser.reset()
        self.stage_progress = {stage: 0.0 for stage in self.stage_weights}
