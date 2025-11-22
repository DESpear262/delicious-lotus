"""
Unit tests for Transition Processor.

Tests the TransitionProcessor class with various transition scenarios.
"""

import tempfile
from pathlib import Path

import pytest
from services.ffmpeg.filter_builder import TransitionType
from services.ffmpeg.timeline_assembler import AssembledTimeline, TimelineClip
from services.ffmpeg.transition_processor import (
    ProcessedTransition,
    TransitionConfig,
    TransitionProcessor,
    TransitionProcessorError,
    TransitionStyle,
)


class TestTransitionConfig:
    """Test cases for TransitionConfig."""

    def test_default_config(self):
        """Test default transition configuration."""
        config = TransitionConfig()

        assert config.type == TransitionType.CROSSFADE
        assert config.style == TransitionStyle.FADE
        assert config.duration == 1.0
        assert config.from_clip_id is None
        assert config.to_clip_id is None

    def test_custom_config(self):
        """Test custom transition configuration."""
        config = TransitionConfig(
            type=TransitionType.FADE,
            style=TransitionStyle.WIPELEFT,
            duration=2.0,
            from_clip_id="clip1",
            to_clip_id="clip2",
        )

        assert config.type == TransitionType.FADE
        assert config.style == TransitionStyle.WIPELEFT
        assert config.duration == 2.0
        assert config.from_clip_id == "clip1"
        assert config.to_clip_id == "clip2"

    def test_invalid_duration(self):
        """Test validation of invalid duration."""
        with pytest.raises(ValueError, match="duration must be positive"):
            TransitionConfig(duration=0)

        with pytest.raises(ValueError, match="duration must be positive"):
            TransitionConfig(duration=-1.0)


class TestTransitionProcessor:
    """Test cases for TransitionProcessor."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def simple_timeline(self, temp_dir):
        """Create a simple timeline with two clips."""
        # Create fake video files
        video1 = temp_dir / "video1.mp4"
        video2 = temp_dir / "video2.mp4"
        video1.write_text("video 1")
        video2.write_text("video 2")

        clips = [
            TimelineClip(
                clip_id="clip1",
                source_path=video1,
                timeline_start=0.0,
                timeline_end=10.0,
                index=0,
            ),
            TimelineClip(
                clip_id="clip2",
                source_path=video2,
                timeline_start=10.0,
                timeline_end=20.0,
                index=1,
            ),
        ]

        return AssembledTimeline(clips=clips, total_duration=20.0)

    @pytest.fixture
    def multi_clip_timeline(self, temp_dir):
        """Create timeline with multiple clips."""
        clips = []
        for i in range(1, 4):
            video = temp_dir / f"video{i}.mp4"
            video.write_text(f"video {i}")

            clip = TimelineClip(
                clip_id=f"clip{i}",
                source_path=video,
                timeline_start=(i - 1) * 10.0,
                timeline_end=i * 10.0,
                index=i - 1,
            )
            clips.append(clip)

        return AssembledTimeline(clips=clips, total_duration=30.0)

    def test_processor_initialization(self):
        """Test processor initializes correctly."""
        processor = TransitionProcessor()

        assert processor.filter_builder is not None

    def test_process_crossfade_transition(self, simple_timeline):
        """Test processing a crossfade transition."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                style=TransitionStyle.FADE,
                duration=1.0,
                from_clip_id="clip1",
                to_clip_id="clip2",
            )
        ]

        filter_complex = processor.process_transitions(simple_timeline, transitions)

        # Verify filter contains xfade
        assert "xfade" in filter_complex
        assert "transition=fade" in filter_complex
        assert "duration=1.0" in filter_complex
        assert "offset=9.0" in filter_complex  # 10 - 1

    def test_process_fade_in_transition(self, simple_timeline):
        """Test processing a fade-in transition."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.FADE,
                duration=2.0,
                to_clip_id="clip1",  # Fade in clip1
            )
        ]

        filter_complex = processor.process_transitions(simple_timeline, transitions)

        # Verify filter contains fade in
        assert "fade=t=in" in filter_complex
        assert "st=0" in filter_complex
        assert "d=2.0" in filter_complex

    def test_process_fade_out_transition(self, simple_timeline):
        """Test processing a fade-out transition."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.FADE,
                duration=2.0,
                from_clip_id="clip2",  # Fade out clip2
            )
        ]

        filter_complex = processor.process_transitions(simple_timeline, transitions)

        # Verify filter contains fade out
        assert "fade=t=out" in filter_complex
        assert "st=8.0" in filter_complex  # 10 - 2
        assert "d=2.0" in filter_complex

    def test_process_cut_transition(self, simple_timeline):
        """Test processing a cut transition (no effect)."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CUT,
                from_clip_id="clip1",
                to_clip_id="clip2",
            )
        ]

        filter_complex = processor.process_transitions(simple_timeline, transitions)

        # Cut should produce simple concat or empty filter
        assert filter_complex is not None

    def test_process_multiple_transitions(self, multi_clip_timeline):
        """Test processing multiple transitions."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                duration=1.0,
                from_clip_id="clip1",
                to_clip_id="clip2",
            ),
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                duration=1.5,
                from_clip_id="clip2",
                to_clip_id="clip3",
            ),
        ]

        filter_complex = processor.process_transitions(multi_clip_timeline, transitions)

        # Verify both transitions are in filter
        assert filter_complex.count("xfade") == 2
        assert "duration=1.0" in filter_complex
        assert "duration=1.5" in filter_complex

    def test_transition_validation_invalid_from_clip(self, simple_timeline):
        """Test validation catches invalid from_clip_id."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                from_clip_id="nonexistent",  # Invalid
                to_clip_id="clip2",
            )
        ]

        with pytest.raises(TransitionProcessorError, match="not found in timeline"):
            processor.process_transitions(simple_timeline, transitions)

    def test_transition_validation_invalid_to_clip(self, simple_timeline):
        """Test validation catches invalid to_clip_id."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                from_clip_id="clip1",
                to_clip_id="nonexistent",  # Invalid
            )
        ]

        with pytest.raises(TransitionProcessorError, match="not found in timeline"):
            processor.process_transitions(simple_timeline, transitions)

    def test_crossfade_requires_both_clips(self, simple_timeline):
        """Test crossfade requires both from and to clips."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                from_clip_id="clip1",
                # Missing to_clip_id
            )
        ]

        with pytest.raises(
            TransitionProcessorError, match="requires both from_clip_id and to_clip_id"
        ):
            processor.process_transitions(simple_timeline, transitions)

    def test_fade_requires_one_clip(self, simple_timeline):
        """Test fade requires either from or to clip."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.FADE,
                # Missing both from_clip_id and to_clip_id
            )
        ]

        with pytest.raises(TransitionProcessorError, match="requires either from_clip_id"):
            processor.process_transitions(simple_timeline, transitions)

    def test_empty_timeline_fails(self):
        """Test processing fails with empty timeline."""
        processor = TransitionProcessor()
        empty_timeline = AssembledTimeline(clips=[], total_duration=0.0)

        with pytest.raises(TransitionProcessorError, match="no clips"):
            processor.process_transitions(empty_timeline, [])

    def test_create_default_transitions(self, multi_clip_timeline):
        """Test creating default transitions between all clips."""
        processor = TransitionProcessor()

        transitions = processor.create_default_transitions(
            multi_clip_timeline,
            transition_type=TransitionType.CROSSFADE,
            transition_style=TransitionStyle.WIPELEFT,
            duration=1.5,
        )

        # Should create n-1 transitions for n clips
        assert len(transitions) == 2  # 3 clips = 2 transitions

        # Verify first transition
        assert transitions[0].type == TransitionType.CROSSFADE
        assert transitions[0].style == TransitionStyle.WIPELEFT
        assert transitions[0].duration == 1.5
        assert transitions[0].from_clip_id == "clip1"
        assert transitions[0].to_clip_id == "clip2"

        # Verify second transition
        assert transitions[1].from_clip_id == "clip2"
        assert transitions[1].to_clip_id == "clip3"

    def test_different_transition_styles(self, simple_timeline):
        """Test different crossfade styles."""
        processor = TransitionProcessor()

        styles_to_test = [
            TransitionStyle.FADE,
            TransitionStyle.WIPELEFT,
            TransitionStyle.SLIDEUP,
            TransitionStyle.CIRCLECROP,
        ]

        for style in styles_to_test:
            transitions = [
                TransitionConfig(
                    type=TransitionType.CROSSFADE,
                    style=style,
                    duration=1.0,
                    from_clip_id="clip1",
                    to_clip_id="clip2",
                )
            ]

            filter_complex = processor.process_transitions(simple_timeline, transitions)

            # Verify the style is in the filter
            assert f"transition={style.value}" in filter_complex

    def test_processed_transition_attributes(self, simple_timeline):
        """Test ProcessedTransition contains correct attributes."""
        processor = TransitionProcessor()

        transition = TransitionConfig(
            type=TransitionType.CROSSFADE,
            duration=1.0,
            from_clip_id="clip1",
            to_clip_id="clip2",
        )

        # Process internally
        result = processor._process_single_transition(simple_timeline, transition)

        assert isinstance(result, ProcessedTransition)
        assert result.config == transition
        assert result.filter_expression is not None
        assert result.start_time == 9.0  # 10 - 1
        assert result.end_time == 11.0  # 10 + 1
        assert result.from_clip_index == 0
        assert result.to_clip_index == 1

    def test_crossfade_offset_calculation(self, simple_timeline):
        """Test crossfade offset is calculated correctly."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                duration=2.0,  # 2 second crossfade
                from_clip_id="clip1",
                to_clip_id="clip2",
            )
        ]

        filter_complex = processor.process_transitions(simple_timeline, transitions)

        # Offset should be clip1_duration - transition_duration
        # 10 - 2 = 8
        assert "offset=8.0" in filter_complex

    def test_fade_in_at_timeline_start(self, simple_timeline):
        """Test fade-in at the start of timeline."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.FADE,
                duration=1.5,
                to_clip_id="clip1",
            )
        ]

        result = processor._process_single_transition(simple_timeline, transitions[0])

        assert result.start_time == 0.0
        assert result.end_time == 1.5
        assert "st=0" in result.filter_expression

    def test_fade_out_at_timeline_end(self, simple_timeline):
        """Test fade-out at the end of timeline."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.FADE,
                duration=2.0,
                from_clip_id="clip2",
            )
        ]

        result = processor._process_single_transition(simple_timeline, transitions[0])

        # Fade out should start at clip_duration - fade_duration
        # 10 - 2 = 8
        assert result.start_time == 18.0  # timeline: 10-20, fade starts at 18
        assert result.end_time == 20.0
        assert "st=8.0" in result.filter_expression  # relative to clip start

    def test_no_transitions_produces_concat(self, simple_timeline):
        """Test no transitions produces simple concat."""
        processor = TransitionProcessor()

        filter_complex = processor.process_transitions(simple_timeline, [])

        # Should produce concat filter
        assert "concat" in filter_complex

    def test_transition_with_different_durations(self, multi_clip_timeline):
        """Test transitions with varying durations."""
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                duration=0.5,
                from_clip_id="clip1",
                to_clip_id="clip2",
            ),
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                duration=2.0,
                from_clip_id="clip2",
                to_clip_id="clip3",
            ),
        ]

        filter_complex = processor.process_transitions(multi_clip_timeline, transitions)

        assert "duration=0.5" in filter_complex
        assert "duration=2.0" in filter_complex


class TestIntegrationScenarios:
    """Test integration scenarios with complete workflows."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_complete_video_composition_workflow(self, temp_dir):
        """Test complete workflow: timeline + transitions."""
        # Create video files
        videos = []
        for i in range(1, 4):
            video = temp_dir / f"video{i}.mp4"
            video.write_text(f"video {i}")
            videos.append(video)

        # Create timeline
        clips = [
            TimelineClip("intro", videos[0], 0.0, 5.0, index=0),
            TimelineClip("main", videos[1], 5.0, 15.0, index=1),
            TimelineClip("outro", videos[2], 15.0, 20.0, index=2),
        ]

        timeline = AssembledTimeline(clips=clips, total_duration=20.0)

        # Create transitions
        processor = TransitionProcessor()

        transitions = [
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                style=TransitionStyle.FADE,
                duration=0.5,
                from_clip_id="intro",
                to_clip_id="main",
            ),
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                style=TransitionStyle.WIPELEFT,
                duration=0.5,
                from_clip_id="main",
                to_clip_id="outro",
            ),
        ]

        filter_complex = processor.process_transitions(timeline, transitions)

        # Verify both transitions are present
        assert "xfade" in filter_complex
        assert "transition=fade" in filter_complex
        assert "transition=wipeleft" in filter_complex
        assert filter_complex.count("xfade") == 2

    def test_mixed_transition_types(self, temp_dir):
        """Test mixing different transition types."""
        # Create videos
        videos = []
        for i in range(1, 4):
            video = temp_dir / f"video{i}.mp4"
            video.write_text(f"video {i}")
            videos.append(video)

        # Create timeline
        clips = [
            TimelineClip("clip1", videos[0], 0.0, 10.0, index=0),
            TimelineClip("clip2", videos[1], 10.0, 20.0, index=1),
            TimelineClip("clip3", videos[2], 20.0, 30.0, index=2),
        ]

        timeline = AssembledTimeline(clips=clips, total_duration=30.0)

        # Mix of transitions: fade in, crossfade, cut, fade out
        processor = TransitionProcessor()

        transitions = [
            # Fade in at start
            TransitionConfig(
                type=TransitionType.FADE,
                duration=1.0,
                to_clip_id="clip1",
            ),
            # Crossfade between clip1 and clip2
            TransitionConfig(
                type=TransitionType.CROSSFADE,
                duration=1.0,
                from_clip_id="clip1",
                to_clip_id="clip2",
            ),
            # Cut between clip2 and clip3
            TransitionConfig(
                type=TransitionType.CUT,
                from_clip_id="clip2",
                to_clip_id="clip3",
            ),
            # Fade out at end
            TransitionConfig(
                type=TransitionType.FADE,
                duration=1.0,
                from_clip_id="clip3",
            ),
        ]

        filter_complex = processor.process_transitions(timeline, transitions)

        # Verify different transition types are present
        assert "fade=t=in" in filter_complex
        assert "fade=t=out" in filter_complex
        assert "xfade" in filter_complex
