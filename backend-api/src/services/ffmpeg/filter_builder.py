"""
FFmpeg Filter Complex Builder for video transitions and effects.

This module provides utilities for building complex FFmpeg filter graphs
including transitions (crossfade, fade, cuts), video concatenation, and
advanced filter chain construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TransitionType(str, Enum):
    """Supported video transition types."""

    FADE = "fade"  # Simple fade to/from black
    CROSSFADE = "xfade"  # Crossfade between clips
    CUT = "cut"  # Hard cut (no transition)


class FadeDirection(str, Enum):
    """Fade direction for fade transitions."""

    IN = "in"  # Fade in from black
    OUT = "out"  # Fade out to black


@dataclass
class Clip:
    """Represents a video clip with duration and trim points.

    Attributes:
        input_index: Index of the input file (0, 1, 2, ...)
        duration: Total duration of the clip in seconds
        start_time: Start time in timeline (when this clip begins)
        trim_start: Trim from beginning of source (default: 0)
        trim_end: Trim from end of source (default: 0)
    """

    input_index: int
    duration: float
    start_time: float = 0.0
    trim_start: float = 0.0
    trim_end: float = 0.0

    @property
    def effective_duration(self) -> float:
        """Get the effective duration after trimming."""
        return max(0.0, self.duration - self.trim_start - self.trim_end)

    @property
    def end_time(self) -> float:
        """Get the end time in the timeline."""
        return self.start_time + self.effective_duration

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Clip[{self.input_index}]: "
            f"{self.start_time:.2f}s - {self.end_time:.2f}s "
            f"(duration: {self.effective_duration:.2f}s)"
        )


@dataclass
class Transition:
    """Represents a transition between two clips.

    Attributes:
        type: Type of transition
        duration: Transition duration in seconds
        offset: Offset where transition starts (from start of second clip)
    """

    type: TransitionType
    duration: float = 1.0
    offset: float = 0.0

    def __repr__(self) -> str:
        """String representation."""
        return f"Transition({self.type.value}, duration={self.duration}s, offset={self.offset}s)"


class FilterComplexBuilder:
    """
    Builder for creating complex FFmpeg filter graphs.

    Provides methods for constructing filter chains with transitions,
    concatenation, and other video effects.

    Example:
        >>> builder = FilterComplexBuilder()
        >>> clips = [
        ...     Clip(input_index=0, duration=10.0),
        ...     Clip(input_index=1, duration=10.0),
        ... ]
        >>> transition = Transition(type=TransitionType.CROSSFADE, duration=1.0)
        >>> filter_expr = builder.build_crossfade_transition(clips, [transition])
    """

    def __init__(self) -> None:
        """Initialize the filter complex builder."""
        self._filters: list[str] = []
        self._stream_labels: dict[str, str] = {}
        self._label_counter = 0

    def _generate_label(self, prefix: str = "stream") -> str:
        """
        Generate a unique stream label.

        Args:
            prefix: Prefix for the label

        Returns:
            Unique label string
        """
        label = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return label

    def build_fade(
        self,
        input_index: int,
        direction: FadeDirection,
        duration: float = 1.0,
        start_time: float = 0.0,
        output_label: str | None = None,
    ) -> str:
        """
        Build a fade in/out filter.

        Args:
            input_index: Input file index
            direction: Fade direction (in or out)
            duration: Fade duration in seconds
            start_time: Start time of fade (for fade out, typically video_duration - duration)
            output_label: Optional label for output stream

        Returns:
            Filter expression string

        Example:
            >>> builder.build_fade(0, FadeDirection.IN, duration=2.0)
            '[0:v]fade=t=in:st=0.0:d=2.0[v0]'
        """
        if output_label is None:
            output_label = self._generate_label("v")

        fade_type = "in" if direction == FadeDirection.IN else "out"

        filter_expr = f"[{input_index}:v]fade=t={fade_type}:st={start_time}:d={duration}[{output_label}]"

        return filter_expr

    def build_crossfade_between_two_clips(
        self,
        clip1_index: int,
        clip2_index: int,
        transition_duration: float,
        clip1_duration: float,
        offset: float = 0.0,
        output_label: str | None = None,
        transition_effect: str = "fade",
    ) -> str:
        """
        Build a crossfade transition between two clips using the xfade filter.

        Args:
            clip1_index: Index of first clip
            clip2_index: Index of second clip
            transition_duration: Duration of crossfade in seconds
            clip1_duration: Duration of first clip (to calculate offset)
            offset: Offset from end of first clip (default: 0.0)
            output_label: Optional label for output stream
            transition_effect: Transition effect name (fade, wipeleft, wiperight, etc.)

        Returns:
            Filter expression string

        Example:
            >>> builder.build_crossfade_between_two_clips(0, 1, 1.0, 10.0)
            '[0:v][1:v]xfade=transition=fade:duration=1.0:offset=9.0[v0]'
        """
        if output_label is None:
            output_label = self._generate_label("v")

        # Calculate offset (when to start transition)
        # offset is typically: clip1_duration - transition_duration
        transition_offset = clip1_duration - transition_duration + offset

        filter_expr = (
            f"[{clip1_index}:v][{clip2_index}:v]"
            f"xfade=transition={transition_effect}:duration={transition_duration}:offset={transition_offset}"
            f"[{output_label}]"
        )

        return filter_expr

    def build_concat_filter(
        self,
        input_indices: list[int],
        output_label: str | None = None,
        include_audio: bool = True,
    ) -> str:
        """
        Build a concat filter for concatenating multiple clips.

        Args:
            input_indices: List of input file indices
            output_label: Optional label for output stream
            include_audio: Whether to concatenate audio streams as well

        Returns:
            Filter expression string

        Example:
            >>> builder.build_concat_filter([0, 1, 2])
            '[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[outv][outa]'
        """
        if output_label is None:
            output_label = self._generate_label("out")

        n = len(input_indices)

        # Build input stream specifiers
        input_streams = []
        for idx in input_indices:
            input_streams.append(f"[{idx}:v]")
            if include_audio:
                input_streams.append(f"[{idx}:a]")

        # Output labels
        v_out = f"{output_label}v"
        outputs = [f"[{v_out}]"]

        if include_audio:
            a_out = f"{output_label}a"
            outputs.append(f"[{a_out}]")

        # Build concat filter
        a_value = 1 if include_audio else 0
        filter_expr = f"{''.join(input_streams)}concat=n={n}:v=1:a={a_value}{''.join(outputs)}"

        return filter_expr

    def build_multi_clip_crossfade(
        self,
        clips: list[Clip],
        transitions: list[Transition] | None = None,
        output_label: str = "final",
    ) -> str:
        """
        Build a complex filter for multiple clips with crossfade transitions.

        This creates a chain of crossfade transitions between multiple clips.

        Args:
            clips: List of Clip objects
            transitions: List of Transition objects (length should be len(clips) - 1)
            output_label: Label for final output stream

        Returns:
            Complete filter complex expression

        Example:
            >>> clips = [Clip(0, 10.0), Clip(1, 10.0), Clip(2, 10.0)]
            >>> transitions = [Transition(TransitionType.CROSSFADE, 1.0)] * 2
            >>> filter_expr = builder.build_multi_clip_crossfade(clips, transitions)
        """
        if len(clips) < 2:
            raise ValueError("Need at least 2 clips for transitions")

        # Default transitions if not provided
        if transitions is None:
            transitions = [Transition(TransitionType.CROSSFADE, 1.0) for _ in range(len(clips) - 1)]

        if len(transitions) != len(clips) - 1:
            raise ValueError(f"Need {len(clips) - 1} transitions for {len(clips)} clips")

        filter_parts: list[str] = []

        # For chaining: we start with first two clips, then keep adding
        current_label = None

        for i in range(len(clips) - 1):
            clip1 = clips[i]
            clip2 = clips[i + 1]
            transition = transitions[i]

            # Determine input labels
            if i == 0:
                # First transition uses direct input indices
                input1 = f"[{clip1.input_index}:v]"
            else:
                # Subsequent transitions use previous output
                input1 = f"[{current_label}]"

            input2 = f"[{clip2.input_index}:v]"

            # Generate output label
            if i == len(clips) - 2:
                # Last transition uses final output label
                current_label = output_label
            else:
                # Intermediate label
                current_label = self._generate_label("v")

            # Build transition based on type
            if transition.type == TransitionType.CROSSFADE:
                # Calculate offset for this transition
                offset = clip1.effective_duration - transition.duration + transition.offset

                filter_expr = (
                    f"{input1}{input2}"
                    f"xfade=transition=fade:duration={transition.duration}:offset={offset}"
                    f"[{current_label}]"
                )
                filter_parts.append(filter_expr)

            elif transition.type == TransitionType.CUT:
                # For hard cuts, we use concat
                filter_expr = f"{input1}{input2}concat=n=2:v=1:a=0[{current_label}]"
                filter_parts.append(filter_expr)

        # Join all filter parts with semicolon
        return ";".join(filter_parts)

    def build_scale_filter(
        self,
        input_index: int,
        width: int,
        height: int,
        output_label: str | None = None,
        scaling_algorithm: str = "bicubic",
    ) -> str:
        """
        Build a scale filter to resize video.

        Args:
            input_index: Input file index
            width: Target width in pixels
            height: Target height in pixels (use -1 to maintain aspect ratio)
            output_label: Optional label for output stream
            scaling_algorithm: Scaling algorithm (bicubic, bilinear, lanczos, etc.)

        Returns:
            Filter expression string

        Example:
            >>> builder.build_scale_filter(0, 1920, 1080)
            '[0:v]scale=1920:1080:flags=bicubic[v0]'
        """
        if output_label is None:
            output_label = self._generate_label("v")

        filter_expr = (
            f"[{input_index}:v]scale={width}:{height}:flags={scaling_algorithm}[{output_label}]"
        )

        return filter_expr

    def build_fps_filter(
        self,
        input_index: int,
        fps: float,
        output_label: str | None = None,
    ) -> str:
        """
        Build an FPS filter to change frame rate.

        Args:
            input_index: Input file index
            fps: Target frame rate
            output_label: Optional label for output stream

        Returns:
            Filter expression string

        Example:
            >>> builder.build_fps_filter(0, 30)
            '[0:v]fps=fps=30.0[v0]'
        """
        if output_label is None:
            output_label = self._generate_label("v")

        filter_expr = f"[{input_index}:v]fps=fps={fps}[{output_label}]"

        return filter_expr

    def build_trim_filter(
        self,
        input_index: int,
        start: float | None = None,
        end: float | None = None,
        duration: float | None = None,
        output_label: str | None = None,
    ) -> str:
        """
        Build a trim filter to extract a portion of video.

        Args:
            input_index: Input file index
            start: Start time in seconds (default: beginning)
            end: End time in seconds (default: end of video)
            duration: Duration in seconds (alternative to end)
            output_label: Optional label for output stream

        Returns:
            Filter expression string

        Example:
            >>> builder.build_trim_filter(0, start=5.0, duration=10.0)
            '[0:v]trim=start=5.0:duration=10.0,setpts=PTS-STARTPTS[v0]'
        """
        if output_label is None:
            output_label = self._generate_label("v")

        trim_params: list[str] = []

        if start is not None:
            trim_params.append(f"start={start}")

        if end is not None:
            trim_params.append(f"end={end}")
        elif duration is not None:
            trim_params.append(f"duration={duration}")

        trim_str = ":".join(trim_params) if trim_params else ""

        # setpts resets timestamps after trimming
        filter_expr = f"[{input_index}:v]trim={trim_str},setpts=PTS-STARTPTS[{output_label}]"

        return filter_expr

    def build_pad_filter(
        self,
        input_index: int,
        width: int,
        height: int,
        x: int | str = 0,
        y: int | str = 0,
        color: str = "black",
        output_label: str | None = None,
    ) -> str:
        """
        Build a pad filter to add padding/borders to video.

        Args:
            input_index: Input file index
            width: Output width
            height: Output height
            x: X position of input video (can be expression like "(ow-iw)/2" for center)
            y: Y position of input video (can be expression like "(oh-ih)/2" for center)
            color: Padding color
            output_label: Optional label for output stream

        Returns:
            Filter expression string

        Example:
            >>> builder.build_pad_filter(0, 1920, 1080, x="(ow-iw)/2", y="(oh-ih)/2")
            '[0:v]pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black[v0]'
        """
        if output_label is None:
            output_label = self._generate_label("v")

        filter_expr = f"[{input_index}:v]pad={width}:{height}:{x}:{y}:color={color}[{output_label}]"

        return filter_expr

    def chain_filters(self, filters: list[str]) -> str:
        """
        Chain multiple filters together with semicolons.

        Args:
            filters: List of filter expressions

        Returns:
            Combined filter expression

        Example:
            >>> filters = ["[0:v]scale=1920:1080[v0]", "[v0]fps=30[v1]"]
            >>> builder.chain_filters(filters)
            '[0:v]scale=1920:1080[v0];[v0]fps=30[v1]'
        """
        return ";".join(filters)
