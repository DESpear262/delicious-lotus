"""
Transition Effects Processor for Video Composition.

This module provides high-level transition processing that integrates with
the timeline assembly system to apply fade, crossfade, and cut transitions
between video clips.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from services.ffmpeg.filter_builder import FilterComplexBuilder, TransitionType

if TYPE_CHECKING:
    from services.ffmpeg.timeline_assembler import AssembledTimeline, TimelineClip

logger = logging.getLogger(__name__)


class TransitionStyle(str, Enum):
    """Transition visual styles for xfade filter."""

    FADE = "fade"  # Simple fade/dissolve
    WIPELEFT = "wipeleft"  # Wipe from left to right
    WIPERIGHT = "wiperight"  # Wipe from right to left
    WIPEUP = "wipeup"  # Wipe from bottom to top
    WIPEDOWN = "wipedown"  # Wipe from top to bottom
    SLIDELEFT = "slideleft"  # Slide left
    SLIDERIGHT = "slideright"  # Slide right
    SLIDEUP = "slideup"  # Slide up
    SLIDEDOWN = "slidedown"  # Slide down
    CIRCLECROP = "circlecrop"  # Circular crop
    RECTCROP = "rectcrop"  # Rectangular crop
    DISTANCE = "distance"  # Distance effect
    FADEBLACK = "fadeblack"  # Fade through black
    FADEWHITE = "fadewhite"  # Fade through white
    RADIAL = "radial"  # Radial transition
    SMOOTHLEFT = "smoothleft"  # Smooth slide left
    SMOOTHRIGHT = "smoothright"  # Smooth slide right
    SMOOTHUP = "smoothup"  # Smooth slide up
    SMOOTHDOWN = "smoothdown"  # Smooth slide down
    CIRCLEOPEN = "circleopen"  # Circle opening
    CIRCLECLOSE = "circleclose"  # Circle closing
    VERTOPEN = "vertopen"  # Vertical opening
    VERTCLOSE = "vertclose"  # Vertical closing
    HORZOPEN = "horzopen"  # Horizontal opening
    HORZCLOSE = "horzclose"  # Horizontal closing
    DISSOLVE = "dissolve"  # Dissolve effect
    PIXELIZE = "pixelize"  # Pixelization effect


@dataclass
class TransitionConfig:
    """
    Configuration for a transition between clips.

    Attributes:
        type: Type of transition (fade, crossfade, cut)
        style: Visual style for crossfade (only applies to CROSSFADE type)
        duration: Duration of transition in seconds
        from_clip_id: ID of clip transitioning from (None for fade-in at start)
        to_clip_id: ID of clip transitioning to (None for fade-out at end)
    """

    type: TransitionType = TransitionType.CROSSFADE
    style: TransitionStyle = TransitionStyle.FADE
    duration: float = 1.0
    from_clip_id: str | None = None
    to_clip_id: str | None = None

    def __post_init__(self) -> None:
        """Validate transition configuration."""
        if self.duration <= 0:
            raise ValueError("Transition duration must be positive")
        if self.duration > 5.0:
            logger.warning(f"Long transition duration: {self.duration}s (max recommended: 5s)")


@dataclass
class ProcessedTransition:
    """
    Result of processing a transition with timeline context.

    Attributes:
        config: Original transition configuration
        filter_expression: Generated FFmpeg filter expression
        start_time: Start time of transition in timeline
        end_time: End time of transition in timeline
        from_clip_index: Index of source clip
        to_clip_index: Index of destination clip
    """

    config: TransitionConfig
    filter_expression: str
    start_time: float
    end_time: float
    from_clip_index: int | None = None
    to_clip_index: int | None = None


class TransitionProcessorError(Exception):
    """Exception raised for transition processing errors."""

    pass


class TransitionProcessor:
    """
    High-level processor for video transitions integrated with timeline.

    This class processes transitions between clips in an assembled timeline,
    generating appropriate FFmpeg filter complex expressions.

    Example:
        >>> from services.ffmpeg.timeline_assembler import TimelineAssembler
        >>> assembler = TimelineAssembler()
        >>> timeline = assembler.assemble_timeline(clips)
        >>>
        >>> processor = TransitionProcessor()
        >>> transitions = [
        ...     TransitionConfig(
        ...         type=TransitionType.CROSSFADE,
        ...         duration=1.0,
        ...         from_clip_id="clip1",
        ...         to_clip_id="clip2"
        ...     )
        ... ]
        >>> filter_complex = processor.process_transitions(timeline, transitions)
    """

    def __init__(self) -> None:
        """Initialize the transition processor."""
        self.filter_builder = FilterComplexBuilder()

        logger.info("Initialized TransitionProcessor")

    def process_transitions(
        self,
        timeline: AssembledTimeline,
        transitions: list[TransitionConfig],
    ) -> str:
        """
        Process all transitions for a timeline.

        Args:
            timeline: Assembled timeline with clips
            transitions: List of transition configurations

        Returns:
            Complete FFmpeg filter complex expression

        Raises:
            TransitionProcessorError: If processing fails
        """
        if not timeline.clips:
            raise TransitionProcessorError("Timeline has no clips")

        logger.info(
            "Processing transitions",
            extra={
                "clip_count": timeline.clip_count,
                "transition_count": len(transitions),
            },
        )

        # Validate transitions reference valid clips
        self._validate_transitions(timeline, transitions)

        # Process each transition
        processed: list[ProcessedTransition] = []
        for transition in transitions:
            result = self._process_single_transition(timeline, transition)
            processed.append(result)

        # Build complete filter complex
        filter_complex = self._build_filter_complex(timeline, processed)

        logger.info(
            "Transitions processed successfully",
            extra={"processed_count": len(processed)},
        )

        return filter_complex

    def _validate_transitions(
        self,
        timeline: AssembledTimeline,
        transitions: list[TransitionConfig],
    ) -> None:
        """
        Validate that transitions reference valid clips.

        Args:
            timeline: Timeline to validate against
            transitions: Transitions to validate

        Raises:
            TransitionProcessorError: If validation fails
        """
        clip_ids = {clip.clip_id for clip in timeline.clips}

        for i, transition in enumerate(transitions):
            if transition.from_clip_id and transition.from_clip_id not in clip_ids:
                raise TransitionProcessorError(
                    f"Transition {i}: from_clip_id '{transition.from_clip_id}' not found in timeline"
                )

            if transition.to_clip_id and transition.to_clip_id not in clip_ids:
                raise TransitionProcessorError(
                    f"Transition {i}: to_clip_id '{transition.to_clip_id}' not found in timeline"
                )

    def _process_single_transition(
        self,
        timeline: AssembledTimeline,
        transition: TransitionConfig,
    ) -> ProcessedTransition:
        """
        Process a single transition.

        Args:
            timeline: Timeline context
            transition: Transition to process

        Returns:
            ProcessedTransition with filter expression
        """
        # Find clips involved in transition
        from_clip = None
        to_clip = None

        if transition.from_clip_id:
            from_clip = next(
                (c for c in timeline.clips if c.clip_id == transition.from_clip_id),
                None,
            )

        if transition.to_clip_id:
            to_clip = next(
                (c for c in timeline.clips if c.clip_id == transition.to_clip_id),
                None,
            )

        # Generate filter expression based on transition type
        if transition.type == TransitionType.CROSSFADE:
            if not from_clip or not to_clip:
                raise TransitionProcessorError(
                    "CROSSFADE transition requires both from_clip_id and to_clip_id"
                )

            filter_expr = self._build_crossfade_filter(from_clip, to_clip, transition)

            start_time = from_clip.timeline_end - transition.duration
            end_time = from_clip.timeline_end + transition.duration

        elif transition.type == TransitionType.FADE:
            # Fade in or fade out
            if from_clip and not to_clip:
                # Fade out at end of from_clip
                filter_expr = self._build_fade_out_filter(from_clip, transition)
                start_time = from_clip.timeline_end - transition.duration
                end_time = from_clip.timeline_end

            elif to_clip and not from_clip:
                # Fade in at start of to_clip
                filter_expr = self._build_fade_in_filter(to_clip, transition)
                start_time = to_clip.timeline_start
                end_time = to_clip.timeline_start + transition.duration

            else:
                raise TransitionProcessorError(
                    "FADE transition requires either from_clip_id (fade out) or to_clip_id (fade in)"
                )

        elif transition.type == TransitionType.CUT:
            # Hard cut - no filter needed
            filter_expr = ""
            if from_clip and to_clip:
                start_time = from_clip.timeline_end
                end_time = to_clip.timeline_start
            else:
                start_time = 0.0
                end_time = 0.0

        else:
            raise TransitionProcessorError(f"Unknown transition type: {transition.type}")

        return ProcessedTransition(
            config=transition,
            filter_expression=filter_expr,
            start_time=start_time,
            end_time=end_time,
            from_clip_index=from_clip.index if from_clip else None,
            to_clip_index=to_clip.index if to_clip else None,
        )

    def _build_crossfade_filter(
        self,
        from_clip: TimelineClip,
        to_clip: TimelineClip,
        transition: TransitionConfig,
    ) -> str:
        """
        Build crossfade filter expression.

        Args:
            from_clip: Clip to transition from
            to_clip: Clip to transition to
            transition: Transition configuration

        Returns:
            Filter expression string
        """
        # Calculate offset (when transition starts relative to first clip)
        offset = from_clip.timeline_duration - transition.duration

        filter_expr = (
            f"[{from_clip.index}:v][{to_clip.index}:v]"
            f"xfade=transition={transition.style.value}:"
            f"duration={transition.duration}:"
            f"offset={offset}"
            f"[vt{from_clip.index}_{to_clip.index}]"
        )

        logger.debug(
            "Built crossfade filter",
            extra={
                "from_clip": from_clip.clip_id,
                "to_clip": to_clip.clip_id,
                "duration": transition.duration,
                "offset": offset,
                "style": transition.style.value,
            },
        )

        return filter_expr

    def _build_fade_in_filter(
        self,
        clip: TimelineClip,
        transition: TransitionConfig,
    ) -> str:
        """
        Build fade-in filter expression.

        Args:
            clip: Clip to fade in
            transition: Transition configuration

        Returns:
            Filter expression string
        """
        filter_expr = (
            f"[{clip.index}:v]" f"fade=t=in:st=0:d={transition.duration}" f"[vfadein{clip.index}]"
        )

        logger.debug(
            "Built fade-in filter",
            extra={
                "clip": clip.clip_id,
                "duration": transition.duration,
            },
        )

        return filter_expr

    def _build_fade_out_filter(
        self,
        clip: TimelineClip,
        transition: TransitionConfig,
    ) -> str:
        """
        Build fade-out filter expression.

        Args:
            clip: Clip to fade out
            transition: Transition configuration

        Returns:
            Filter expression string
        """
        # Start fade at (clip_duration - fade_duration)
        start_time = clip.timeline_duration - transition.duration

        filter_expr = (
            f"[{clip.index}:v]"
            f"fade=t=out:st={start_time}:d={transition.duration}"
            f"[vfadeout{clip.index}]"
        )

        logger.debug(
            "Built fade-out filter",
            extra={
                "clip": clip.clip_id,
                "duration": transition.duration,
                "start_time": start_time,
            },
        )

        return filter_expr

    def _build_filter_complex(
        self,
        timeline: AssembledTimeline,
        transitions: list[ProcessedTransition],
    ) -> str:
        """
        Build complete filter complex from processed transitions.

        Args:
            timeline: Timeline context
            transitions: Processed transitions

        Returns:
            Complete filter complex expression
        """
        if not transitions:
            # No transitions - simple concat
            return self._build_simple_concat(timeline)

        # Combine transition filters
        filter_parts = []

        for transition in transitions:
            if transition.filter_expression:
                filter_parts.append(transition.filter_expression)

        # If we have transitions, chain them
        if filter_parts:
            return ";".join(filter_parts)
        else:
            return self._build_simple_concat(timeline)

    def _build_simple_concat(self, timeline: AssembledTimeline) -> str:
        """
        Build simple concatenation filter (no transitions).

        Args:
            timeline: Timeline to concatenate

        Returns:
            Concat filter expression
        """
        return self.filter_builder.build_concat_filter(
            input_indices=[clip.index for clip in timeline.clips],
            output_label="final",
            include_audio=True,
        )

    def create_default_transitions(
        self,
        timeline: AssembledTimeline,
        transition_type: TransitionType = TransitionType.CROSSFADE,
        transition_style: TransitionStyle = TransitionStyle.FADE,
        duration: float = 1.0,
    ) -> list[TransitionConfig]:
        """
        Create default transitions between all clips in timeline.

        Args:
            timeline: Timeline to create transitions for
            transition_type: Type of transition to use
            transition_style: Visual style for crossfades
            duration: Duration of each transition

        Returns:
            List of transition configurations
        """
        transitions = []

        for i in range(len(timeline.clips) - 1):
            from_clip = timeline.clips[i]
            to_clip = timeline.clips[i + 1]

            transition = TransitionConfig(
                type=transition_type,
                style=transition_style,
                duration=duration,
                from_clip_id=from_clip.clip_id,
                to_clip_id=to_clip.clip_id,
            )

            transitions.append(transition)

        logger.info(
            "Created default transitions",
            extra={
                "count": len(transitions),
                "type": transition_type.value,
                "duration": duration,
            },
        )

        return transitions
