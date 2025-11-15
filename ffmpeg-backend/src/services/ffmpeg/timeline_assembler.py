"""
Timeline Assembly Module for Video Composition.

This module provides functionality to assemble video timelines from clip metadata,
handling trim points, duration calculations, and timeline validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TimelineClip:
    """
    Represents a single clip in the assembled timeline.

    Attributes:
        clip_id: Unique identifier for this clip
        source_path: Path to the source video file (normalized)
        timeline_start: Start time in final timeline (seconds)
        timeline_end: End time in final timeline (seconds)
        source_start: Start trim point in source video (seconds)
        source_end: End trim point in source video (seconds, None for full duration)
        source_duration: Total duration of source video (seconds)
        index: Position of clip in timeline (0-indexed)
    """

    clip_id: str
    source_path: Path | str
    timeline_start: float
    timeline_end: float
    source_start: float = 0.0
    source_end: float | None = None
    source_duration: float | None = None
    index: int = 0

    def __post_init__(self) -> None:
        """Validate clip data after initialization."""
        if self.timeline_end <= self.timeline_start:
            raise ValueError(
                f"timeline_end ({self.timeline_end}) must be greater than "
                f"timeline_start ({self.timeline_start})"
            )

        if self.source_start < 0:
            raise ValueError(f"source_start ({self.source_start}) cannot be negative")

        if self.source_end is not None and self.source_end <= self.source_start:
            raise ValueError(
                f"source_end ({self.source_end}) must be greater than "
                f"source_start ({self.source_start})"
            )

    @property
    def timeline_duration(self) -> float:
        """Get duration of clip in the timeline."""
        return self.timeline_end - self.timeline_start

    @property
    def source_clip_duration(self) -> float:
        """Get duration of the clipped portion from source video."""
        if self.source_end is not None:
            return self.source_end - self.source_start
        elif self.source_duration is not None:
            return self.source_duration - self.source_start
        else:
            # If we don't know source duration, assume it matches timeline duration
            return self.timeline_duration

    @property
    def needs_trim(self) -> bool:
        """Check if this clip needs trimming."""
        return self.source_start > 0 or self.source_end is not None

    @property
    def is_partial(self) -> bool:
        """Check if this is a partial clip (not using full source duration)."""
        if self.source_duration is None:
            return self.needs_trim
        return self.needs_trim or self.source_clip_duration < self.source_duration

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"TimelineClip(id={self.clip_id!r}, "
            f"timeline={self.timeline_start:.2f}-{self.timeline_end:.2f}s, "
            f"source={self.source_start:.2f}-{self.source_end or 'end'}s, "
            f"index={self.index})"
        )


@dataclass
class AssembledTimeline:
    """
    Represents a fully assembled timeline.

    Attributes:
        clips: List of timeline clips in order
        total_duration: Total duration of the timeline
        gaps: List of gaps in the timeline (start, end, duration)
        has_gaps: Whether timeline contains any gaps
        clip_count: Number of clips in timeline
    """

    clips: list[TimelineClip] = field(default_factory=list)
    total_duration: float = 0.0
    gaps: list[tuple[float, float, float]] = field(default_factory=list)

    @property
    def has_gaps(self) -> bool:
        """Check if timeline has gaps between clips."""
        return len(self.gaps) > 0

    @property
    def clip_count(self) -> int:
        """Get number of clips in timeline."""
        return len(self.clips)

    @property
    def is_valid(self) -> bool:
        """Check if timeline is valid (has clips and no overlaps)."""
        return self.clip_count > 0 and not self._has_overlaps()

    def _has_overlaps(self) -> bool:
        """Check for overlapping clips."""
        for i in range(len(self.clips) - 1):
            if self.clips[i].timeline_end > self.clips[i + 1].timeline_start:
                return True
        return False

    def get_clip_at_time(self, time: float) -> TimelineClip | None:
        """
        Get the clip active at a specific timeline time.

        Args:
            time: Time in timeline (seconds)

        Returns:
            TimelineClip if found, None otherwise
        """
        for clip in self.clips:
            if clip.timeline_start <= time < clip.timeline_end:
                return clip
        return None

    def get_clips_in_range(
        self,
        start_time: float,
        end_time: float,
    ) -> list[TimelineClip]:
        """
        Get all clips that overlap with a time range.

        Args:
            start_time: Start of range (seconds)
            end_time: End of range (seconds)

        Returns:
            List of clips overlapping with range
        """
        clips = []
        for clip in self.clips:
            # Check if clip overlaps with range
            if clip.timeline_start < end_time and clip.timeline_end > start_time:
                clips.append(clip)
        return clips

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"AssembledTimeline(clips={self.clip_count}, "
            f"duration={self.total_duration:.2f}s, "
            f"gaps={len(self.gaps)})"
        )


class TimelineAssemblyError(Exception):
    """Exception raised for timeline assembly errors."""

    pass


class TimelineAssembler:
    """
    Service for assembling video timelines from clip metadata.

    This class handles the conversion of clip configurations into a structured
    timeline with accurate timestamps and trim point management.

    Example:
        >>> assembler = TimelineAssembler()
        >>> clips = [
        ...     {"clip_id": "1", "source_path": "video1.mp4", ...},
        ...     {"clip_id": "2", "source_path": "video2.mp4", ...},
        ... ]
        >>> timeline = assembler.assemble_timeline(clips)
        >>> print(f"Timeline duration: {timeline.total_duration}s")
    """

    def __init__(
        self,
        allow_gaps: bool = True,
        validate_sources: bool = False,
    ) -> None:
        """
        Initialize the timeline assembler.

        Args:
            allow_gaps: Whether to allow gaps between clips
            validate_sources: Whether to validate source files exist
        """
        self.allow_gaps = allow_gaps
        self.validate_sources = validate_sources

        logger.info(
            "Initialized TimelineAssembler",
            extra={
                "allow_gaps": allow_gaps,
                "validate_sources": validate_sources,
            },
        )

    def assemble_timeline(
        self,
        clips: list[dict[str, Any]],
        *,
        sort_clips: bool = True,
    ) -> AssembledTimeline:
        """
        Assemble a timeline from clip metadata.

        Args:
            clips: List of clip metadata dictionaries with keys:
                  - clip_id: Unique clip identifier
                  - source_path: Path to source video
                  - timeline_start: Start time in timeline
                  - timeline_end: End time in timeline
                  - source_start: Trim start (optional, default 0)
                  - source_end: Trim end (optional, default None)
                  - source_duration: Source video duration (optional)
            sort_clips: Whether to sort clips by timeline_start

        Returns:
            AssembledTimeline with processed clips and metadata

        Raises:
            TimelineAssemblyError: If timeline assembly fails
        """
        if not clips:
            raise TimelineAssemblyError("Cannot assemble timeline with no clips")

        logger.info(
            "Assembling timeline",
            extra={"clip_count": len(clips), "sort_clips": sort_clips},
        )

        # Convert dicts to TimelineClip objects
        timeline_clips: list[TimelineClip] = []

        for i, clip_data in enumerate(clips):
            try:
                timeline_clip = TimelineClip(
                    clip_id=clip_data["clip_id"],
                    source_path=Path(clip_data["source_path"]),
                    timeline_start=clip_data["timeline_start"],
                    timeline_end=clip_data["timeline_end"],
                    source_start=clip_data.get("source_start", 0.0),
                    source_end=clip_data.get("source_end"),
                    source_duration=clip_data.get("source_duration"),
                    index=i,
                )

                # Validate source file if required
                if self.validate_sources:
                    source_path = Path(timeline_clip.source_path)
                    if not source_path.exists():
                        raise TimelineAssemblyError(f"Source file not found: {source_path}")

                timeline_clips.append(timeline_clip)

            except (KeyError, ValueError) as e:
                raise TimelineAssemblyError(f"Invalid clip data at index {i}: {e}") from e

        # Sort clips by timeline start if requested
        if sort_clips:
            timeline_clips.sort(key=lambda c: c.timeline_start)
            # Update indices after sorting
            for i, clip in enumerate(timeline_clips):
                clip.index = i

        # Validate timeline consistency
        self._validate_timeline(timeline_clips)

        # Calculate total duration
        total_duration = max(clip.timeline_end for clip in timeline_clips)

        # Detect gaps
        gaps = self._detect_gaps(timeline_clips)

        if gaps and not self.allow_gaps:
            gap_desc = ", ".join(f"{start:.2f}-{end:.2f}s" for start, end, _ in gaps)
            raise TimelineAssemblyError(f"Timeline contains gaps which are not allowed: {gap_desc}")

        timeline = AssembledTimeline(
            clips=timeline_clips,
            total_duration=total_duration,
            gaps=gaps,
        )

        logger.info(
            "Timeline assembly completed",
            extra={
                "clip_count": timeline.clip_count,
                "duration": total_duration,
                "gaps": len(gaps),
                "has_gaps": timeline.has_gaps,
            },
        )

        return timeline

    def _validate_timeline(self, clips: list[TimelineClip]) -> None:
        """
        Validate timeline for common issues.

        Args:
            clips: List of timeline clips to validate

        Raises:
            TimelineAssemblyError: If validation fails
        """
        # Check for overlaps
        for i in range(len(clips) - 1):
            current = clips[i]
            next_clip = clips[i + 1]

            if current.timeline_end > next_clip.timeline_start:
                raise TimelineAssemblyError(
                    f"Clips overlap: clip {current.clip_id} ends at {current.timeline_end}s "
                    f"but clip {next_clip.clip_id} starts at {next_clip.timeline_start}s"
                )

        # Validate each clip's trim points vs expected duration
        for clip in clips:
            # Check if timeline duration matches source clip duration
            if clip.source_end is not None:
                expected_duration = clip.source_end - clip.source_start
                if abs(clip.timeline_duration - expected_duration) > 0.01:
                    logger.warning(
                        "Clip timeline duration doesn't match source clip duration",
                        extra={
                            "clip_id": clip.clip_id,
                            "timeline_duration": clip.timeline_duration,
                            "source_clip_duration": expected_duration,
                        },
                    )

    def _detect_gaps(self, clips: list[TimelineClip]) -> list[tuple[float, float, float]]:
        """
        Detect gaps between clips in the timeline.

        Args:
            clips: List of timeline clips (should be sorted)

        Returns:
            List of gaps as tuples (start, end, duration)
        """
        gaps: list[tuple[float, float, float]] = []

        # Check for gap at beginning
        if clips[0].timeline_start > 0:
            gap_start = 0.0
            gap_end = clips[0].timeline_start
            gaps.append((gap_start, gap_end, gap_end - gap_start))

        # Check for gaps between clips
        for i in range(len(clips) - 1):
            current = clips[i]
            next_clip = clips[i + 1]

            if current.timeline_end < next_clip.timeline_start:
                gap_start = current.timeline_end
                gap_end = next_clip.timeline_start
                gaps.append((gap_start, gap_end, gap_end - gap_start))

        return gaps

    def calculate_timestamps(
        self,
        timeline: AssembledTimeline,
    ) -> dict[str, dict[str, float | None | int]]:
        """
        Calculate detailed timestamps for each clip in the timeline.

        Args:
            timeline: Assembled timeline

        Returns:
            Dictionary mapping clip_id to timestamp data:
            {
                "clip_id": {
                    "timeline_start": float,
                    "timeline_end": float,
                    "timeline_duration": float,
                    "source_start": float,
                    "source_end": float | None,
                    "source_duration": float | None,
                    "index": int,
                }
            }
        """
        timestamps = {}

        for clip in timeline.clips:
            timestamps[clip.clip_id] = {
                "timeline_start": clip.timeline_start,
                "timeline_end": clip.timeline_end,
                "timeline_duration": clip.timeline_duration,
                "source_start": clip.source_start,
                "source_end": clip.source_end or clip.source_clip_duration + clip.source_start,
                "source_duration": clip.source_duration,
                "index": clip.index,
            }

        logger.debug(
            "Calculated timestamps for timeline",
            extra={"clip_count": len(timestamps)},
        )

        return timestamps

    def get_timeline_summary(self, timeline: AssembledTimeline) -> dict[str, Any]:
        """
        Get a summary of the timeline for logging/debugging.

        Args:
            timeline: Assembled timeline

        Returns:
            Dictionary with timeline summary information
        """
        return {
            "total_duration": timeline.total_duration,
            "clip_count": timeline.clip_count,
            "has_gaps": timeline.has_gaps,
            "gap_count": len(timeline.gaps),
            "gaps": [
                {
                    "start": start,
                    "end": end,
                    "duration": duration,
                }
                for start, end, duration in timeline.gaps
            ],
            "clips": [
                {
                    "clip_id": clip.clip_id,
                    "index": clip.index,
                    "timeline_start": clip.timeline_start,
                    "timeline_end": clip.timeline_end,
                    "timeline_duration": clip.timeline_duration,
                    "source_start": clip.source_start,
                    "source_end": clip.source_end,
                    "needs_trim": clip.needs_trim,
                    "is_partial": clip.is_partial,
                }
                for clip in timeline.clips
            ],
        }
