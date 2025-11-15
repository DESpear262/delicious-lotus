"""
Concat Demuxer Builder for FFmpeg video concatenation.

This module provides utilities for generating FFmpeg concat demuxer files
and building concatenation commands for seamless video joining.
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from services.ffmpeg.timeline_assembler import AssembledTimeline, TimelineClip

logger = logging.getLogger(__name__)


@dataclass
class ConcatSegment:
    """Represents a segment in a concat demuxer file.

    Attributes:
        file_path: Path to the video file
        duration: Optional duration of the segment
        inpoint: Start point in the file (seconds)
        outpoint: End point in the file (seconds)
    """

    file_path: str | Path
    duration: float | None = None
    inpoint: float = 0.0
    outpoint: float | None = None

    def __repr__(self) -> str:
        """String representation."""
        return f"ConcatSegment({self.file_path}, {self.inpoint}s - {self.outpoint or 'end'})"


class ConcatDemuxerBuilder:
    """
    Builder for FFmpeg concat demuxer files.

    The concat demuxer is FFmpeg's protocol for concatenating media files
    without re-encoding. It uses a text file listing all input files.

    Example:
        >>> builder = ConcatDemuxerBuilder()
        >>> segments = [
        ...     ConcatSegment("video1.mp4"),
        ...     ConcatSegment("video2.mp4"),
        ...     ConcatSegment("video3.mp4"),
        ... ]
        >>> concat_file = builder.generate_concat_file(segments)
        >>> # Use with: ffmpeg -f concat -safe 0 -i {concat_file} output.mp4
    """

    def __init__(self, temp_dir: str | Path | None = None) -> None:
        """
        Initialize the concat demuxer builder.

        Args:
            temp_dir: Directory for temporary files (default: system temp)
        """
        self.temp_dir = Path(temp_dir) if temp_dir else None
        self._created_files: list[Path] = []

    def generate_concat_file(
        self,
        segments: list[ConcatSegment],
        output_path: str | Path | None = None,
        safe_mode: bool = False,
    ) -> Path:
        """
        Generate a concat demuxer file from segments.

        Creates a text file in the format required by FFmpeg's concat demuxer:
        ```
        file 'video1.mp4'
        file 'video2.mp4'
        file 'video3.mp4'
        ```

        With durations and in/out points:
        ```
        file 'video1.mp4'
        inpoint 5.0
        outpoint 15.0
        duration 10.0
        ```

        Args:
            segments: List of ConcatSegment objects
            output_path: Path for concat file (default: temp file)
            safe_mode: Use safe mode (requires absolute paths)

        Returns:
            Path to generated concat file

        Example:
            >>> segments = [ConcatSegment("video1.mp4"), ConcatSegment("video2.mp4")]
            >>> concat_file = builder.generate_concat_file(segments)
        """
        if not segments:
            raise ValueError("Need at least one segment for concat file")

        # Create output file
        if output_path is None:
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(
                suffix=".txt",
                prefix="ffmpeg_concat_",
                dir=self.temp_dir,
            )
            output_path = Path(temp_path)
            # Close the file descriptor, we'll write with open()
            import os

            os.close(fd)
        else:
            output_path = Path(output_path)

        # Track created file for cleanup
        self._created_files.append(output_path)

        # Generate concat file content
        lines: list[str] = []

        for segment in segments:
            # Convert to absolute path if safe mode
            file_path = Path(segment.file_path)
            if safe_mode:
                file_path = file_path.resolve()

            # Add file directive
            # Use single quotes to handle spaces and special characters
            lines.append(f"file '{file_path}'")

            # Add inpoint if specified
            if segment.inpoint > 0:
                lines.append(f"inpoint {segment.inpoint}")

            # Add outpoint if specified
            if segment.outpoint is not None:
                lines.append(f"outpoint {segment.outpoint}")

            # Add duration if specified
            if segment.duration is not None:
                lines.append(f"duration {segment.duration}")

        # Write to file
        content = "\n".join(lines) + "\n"
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def build_concat_command_args(
        self,
        concat_file_path: str | Path,
        output_path: str | Path,
        safe_mode: bool = True,
        codec_copy: bool = True,
    ) -> list[str]:
        """
        Build FFmpeg command arguments for concat demuxer.

        Args:
            concat_file_path: Path to concat demuxer file
            output_path: Output video path
            safe_mode: Disable safe mode (required for relative paths)
            codec_copy: Use codec copy (no re-encoding)

        Returns:
            List of FFmpeg command arguments

        Example:
            >>> args = builder.build_concat_command_args("concat.txt", "output.mp4")
            >>> subprocess.run(["ffmpeg"] + args)
        """
        args: list[str] = []

        # Input format
        args.extend(["-f", "concat"])

        # Safe mode (0 = disabled, allows relative paths)
        safe_value = "1" if safe_mode else "0"
        args.extend(["-safe", safe_value])

        # Input file
        args.extend(["-i", str(concat_file_path)])

        # Codec settings
        if codec_copy:
            args.extend(["-c", "copy"])  # Copy both video and audio codecs

        # Output
        args.append(str(output_path))

        return args

    def cleanup(self) -> None:
        """
        Clean up temporary concat files.

        Removes all concat files created by this builder instance.
        """
        for file_path in self._created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:  # noqa: S110
                # Ignore cleanup errors - best effort cleanup
                logger.debug(f"Failed to cleanup file {file_path}: {e}")

        self._created_files.clear()

    def __enter__(self) -> ConcatDemuxerBuilder:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - cleanup files."""
        self.cleanup()

    def __del__(self) -> None:
        """Destructor - cleanup files."""
        self.cleanup()

    def create_segments_from_timeline(
        self,
        timeline: AssembledTimeline,
    ) -> list[ConcatSegment]:
        """
        Create concat segments from an assembled timeline.

        This method converts TimelineClip objects into ConcatSegment objects
        with proper trim points for the FFmpeg concat demuxer.

        Args:
            timeline: AssembledTimeline with clips to convert

        Returns:
            List of ConcatSegment objects ready for concat demuxer

        Example:
            >>> from services.ffmpeg.timeline_assembler import TimelineAssembler
            >>> assembler = TimelineAssembler()
            >>> timeline = assembler.assemble_timeline(clips)
            >>> builder = ConcatDemuxerBuilder()
            >>> segments = builder.create_segments_from_timeline(timeline)
            >>> concat_file = builder.generate_concat_file(segments)
        """
        if not timeline.clips:
            raise ValueError("Timeline has no clips to convert to segments")

        segments: list[ConcatSegment] = []

        logger.info(
            "Creating concat segments from timeline",
            extra={"clip_count": timeline.clip_count},
        )

        for clip in timeline.clips:
            segment = self._clip_to_segment(clip)
            segments.append(segment)

            logger.debug(
                "Created concat segment from timeline clip",
                extra={
                    "clip_id": clip.clip_id,
                    "source_path": str(clip.source_path),
                    "inpoint": segment.inpoint,
                    "outpoint": segment.outpoint,
                    "duration": segment.duration,
                },
            )

        logger.info(
            "Created concat segments from timeline",
            extra={"segment_count": len(segments)},
        )

        return segments

    def _clip_to_segment(self, clip: TimelineClip) -> ConcatSegment:
        """
        Convert a TimelineClip to a ConcatSegment.

        Args:
            clip: TimelineClip to convert

        Returns:
            ConcatSegment with appropriate trim points
        """
        # Determine duration
        duration = None
        if clip.source_end is not None:
            # Calculate exact duration from trim points
            duration = clip.source_end - clip.source_start

        return ConcatSegment(
            file_path=clip.source_path,
            duration=duration,
            inpoint=clip.source_start,
            outpoint=clip.source_end,
        )

    def generate_concat_file_from_timeline(
        self,
        timeline: AssembledTimeline,
        output_path: str | Path | None = None,
        safe_mode: bool = False,
    ) -> Path:
        """
        Generate a concat demuxer file directly from a timeline.

        This is a convenience method that combines create_segments_from_timeline
        and generate_concat_file into a single call.

        Args:
            timeline: AssembledTimeline to convert to concat file
            output_path: Path for concat file (default: temp file)
            safe_mode: Use safe mode (requires absolute paths)

        Returns:
            Path to generated concat file

        Example:
            >>> timeline = assembler.assemble_timeline(clips)
            >>> builder = ConcatDemuxerBuilder()
            >>> concat_file = builder.generate_concat_file_from_timeline(timeline)
        """
        segments = self.create_segments_from_timeline(timeline)
        return self.generate_concat_file(
            segments=segments,
            output_path=output_path,
            safe_mode=safe_mode,
        )


def create_concat_segments_from_files(
    file_paths: list[str | Path],
    durations: list[float] | None = None,
) -> list[ConcatSegment]:
    """
    Helper function to create concat segments from a list of files.

    Args:
        file_paths: List of video file paths
        durations: Optional list of durations (must match file_paths length)

    Returns:
        List of ConcatSegment objects

    Example:
        >>> files = ["video1.mp4", "video2.mp4", "video3.mp4"]
        >>> segments = create_concat_segments_from_files(files)
    """
    segments: list[ConcatSegment] = []

    for i, file_path in enumerate(file_paths):
        duration = durations[i] if durations and i < len(durations) else None
        segment = ConcatSegment(file_path=file_path, duration=duration)
        segments.append(segment)

    return segments


def create_trimmed_segments(
    file_path: str | Path,
    trim_points: list[tuple[float, float]],
) -> list[ConcatSegment]:
    """
    Create concat segments from a single file with multiple trim points.

    Useful for extracting multiple segments from the same source file.

    Args:
        file_path: Source video file
        trim_points: List of (inpoint, outpoint) tuples in seconds

    Returns:
        List of ConcatSegment objects

    Example:
        >>> # Extract three 10-second clips from same video
        >>> segments = create_trimmed_segments(
        ...     "source.mp4",
        ...     [(0, 10), (30, 40), (60, 70)]
        ... )
    """
    segments: list[ConcatSegment] = []

    for inpoint, outpoint in trim_points:
        duration = outpoint - inpoint if outpoint > inpoint else None
        segment = ConcatSegment(
            file_path=file_path,
            duration=duration,
            inpoint=inpoint,
            outpoint=outpoint,
        )
        segments.append(segment)

    return segments
