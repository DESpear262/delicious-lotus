"""
Unit tests for Timeline Assembler.

Tests the TimelineAssembler class with various timeline scenarios.
"""

import tempfile
from pathlib import Path

import pytest
from services.ffmpeg.timeline_assembler import (
    AssembledTimeline,
    TimelineAssembler,
    TimelineAssemblyError,
    TimelineClip,
)


class TestTimelineClip:
    """Test cases for TimelineClip dataclass."""

    def test_basic_clip_creation(self):
        """Test creating a basic timeline clip."""
        clip = TimelineClip(
            clip_id="clip1",
            source_path="/tmp/video.mp4",
            timeline_start=0.0,
            timeline_end=10.0,
            source_start=0.0,
        )

        assert clip.clip_id == "clip1"
        assert clip.timeline_start == 0.0
        assert clip.timeline_end == 10.0
        assert clip.timeline_duration == 10.0

    def test_clip_with_trim_points(self):
        """Test clip with source trim points."""
        clip = TimelineClip(
            clip_id="clip1",
            source_path="/tmp/video.mp4",
            timeline_start=5.0,
            timeline_end=15.0,
            source_start=2.0,
            source_end=12.0,
            source_duration=60.0,
        )

        assert clip.timeline_duration == 10.0
        assert clip.source_clip_duration == 10.0
        assert clip.needs_trim is True
        assert clip.is_partial is True

    def test_clip_duration_properties(self):
        """Test clip duration calculation properties."""
        # Full clip (no trim)
        full_clip = TimelineClip(
            clip_id="full",
            source_path="/tmp/video.mp4",
            timeline_start=0.0,
            timeline_end=30.0,
            source_duration=30.0,
        )

        assert full_clip.timeline_duration == 30.0
        assert full_clip.source_clip_duration == 30.0
        assert full_clip.needs_trim is False

        # Partial clip with trim start
        partial_clip = TimelineClip(
            clip_id="partial",
            source_path="/tmp/video.mp4",
            timeline_start=0.0,
            timeline_end=10.0,
            source_start=5.0,
            source_duration=30.0,
        )

        assert partial_clip.source_clip_duration == 25.0
        assert partial_clip.needs_trim is True
        assert partial_clip.is_partial is True

    def test_invalid_timeline_times(self):
        """Test validation of invalid timeline times."""
        with pytest.raises(ValueError, match="timeline_end.*must be greater"):
            TimelineClip(
                clip_id="bad",
                source_path="/tmp/video.mp4",
                timeline_start=10.0,
                timeline_end=5.0,  # Invalid: end before start
            )

    def test_invalid_source_times(self):
        """Test validation of invalid source times."""
        with pytest.raises(ValueError, match="source_start.*cannot be negative"):
            TimelineClip(
                clip_id="bad",
                source_path="/tmp/video.mp4",
                timeline_start=0.0,
                timeline_end=10.0,
                source_start=-1.0,  # Invalid: negative trim
            )

        with pytest.raises(ValueError, match="source_end.*must be greater"):
            TimelineClip(
                clip_id="bad",
                source_path="/tmp/video.mp4",
                timeline_start=0.0,
                timeline_end=10.0,
                source_start=5.0,
                source_end=3.0,  # Invalid: end before start
            )


class TestAssembledTimeline:
    """Test cases for AssembledTimeline dataclass."""

    def test_empty_timeline(self):
        """Test empty timeline."""
        timeline = AssembledTimeline()

        assert timeline.clip_count == 0
        assert timeline.total_duration == 0.0
        assert timeline.has_gaps is False
        assert timeline.is_valid is False  # Invalid because no clips

    def test_simple_timeline(self):
        """Test simple timeline with sequential clips."""
        clips = [
            TimelineClip(
                clip_id="1",
                source_path="/tmp/v1.mp4",
                timeline_start=0.0,
                timeline_end=10.0,
                index=0,
            ),
            TimelineClip(
                clip_id="2",
                source_path="/tmp/v2.mp4",
                timeline_start=10.0,
                timeline_end=20.0,
                index=1,
            ),
        ]

        timeline = AssembledTimeline(
            clips=clips,
            total_duration=20.0,
            gaps=[],
        )

        assert timeline.clip_count == 2
        assert timeline.total_duration == 20.0
        assert timeline.has_gaps is False
        assert timeline.is_valid is True

    def test_timeline_with_gaps(self):
        """Test timeline with gaps between clips."""
        clips = [
            TimelineClip(
                clip_id="1",
                source_path="/tmp/v1.mp4",
                timeline_start=0.0,
                timeline_end=10.0,
                index=0,
            ),
            TimelineClip(
                clip_id="2",
                source_path="/tmp/v2.mp4",
                timeline_start=15.0,  # 5-second gap
                timeline_end=25.0,
                index=1,
            ),
        ]

        timeline = AssembledTimeline(
            clips=clips,
            total_duration=25.0,
            gaps=[(10.0, 15.0, 5.0)],
        )

        assert timeline.has_gaps is True
        assert len(timeline.gaps) == 1
        assert timeline.gaps[0] == (10.0, 15.0, 5.0)

    def test_get_clip_at_time(self):
        """Test getting clip at specific time."""
        clips = [
            TimelineClip(
                clip_id="1",
                source_path="/tmp/v1.mp4",
                timeline_start=0.0,
                timeline_end=10.0,
                index=0,
            ),
            TimelineClip(
                clip_id="2",
                source_path="/tmp/v2.mp4",
                timeline_start=10.0,
                timeline_end=20.0,
                index=1,
            ),
        ]

        timeline = AssembledTimeline(clips=clips, total_duration=20.0)

        # Test times within clips
        clip_at_5 = timeline.get_clip_at_time(5.0)
        assert clip_at_5 is not None
        assert clip_at_5.clip_id == "1"

        clip_at_15 = timeline.get_clip_at_time(15.0)
        assert clip_at_15 is not None
        assert clip_at_15.clip_id == "2"

        # Test time in gap/outside
        clip_at_25 = timeline.get_clip_at_time(25.0)
        assert clip_at_25 is None

    def test_get_clips_in_range(self):
        """Test getting clips within a time range."""
        clips = [
            TimelineClip("1", "/tmp/v1.mp4", 0.0, 10.0, index=0),
            TimelineClip("2", "/tmp/v2.mp4", 10.0, 20.0, index=1),
            TimelineClip("3", "/tmp/v3.mp4", 20.0, 30.0, index=2),
        ]

        timeline = AssembledTimeline(clips=clips, total_duration=30.0)

        # Get clips in range 5-25 (should include clips 1, 2, 3)
        clips_in_range = timeline.get_clips_in_range(5.0, 25.0)
        assert len(clips_in_range) == 3

        # Get clips in range 15-18 (should only include clip 2)
        clips_in_range = timeline.get_clips_in_range(15.0, 18.0)
        assert len(clips_in_range) == 1
        assert clips_in_range[0].clip_id == "2"

        # Get clips in range 35-40 (outside timeline, no clips)
        clips_in_range = timeline.get_clips_in_range(35.0, 40.0)
        assert len(clips_in_range) == 0


class TestTimelineAssembler:
    """Test cases for TimelineAssembler."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_clips(self, temp_dir):
        """Create sample clip metadata."""
        # Create dummy video files
        (temp_dir / "video1.mp4").write_text("fake video 1")
        (temp_dir / "video2.mp4").write_text("fake video 2")
        (temp_dir / "video3.mp4").write_text("fake video 3")

        return [
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "video1.mp4"),
                "timeline_start": 0.0,
                "timeline_end": 10.0,
                "source_start": 0.0,
                "source_duration": 30.0,
            },
            {
                "clip_id": "clip2",
                "source_path": str(temp_dir / "video2.mp4"),
                "timeline_start": 10.0,
                "timeline_end": 20.0,
                "source_start": 5.0,
                "source_end": 15.0,
                "source_duration": 60.0,
            },
            {
                "clip_id": "clip3",
                "source_path": str(temp_dir / "video3.mp4"),
                "timeline_start": 20.0,
                "timeline_end": 30.0,
                "source_start": 0.0,
                "source_duration": 10.0,
            },
        ]

    def test_assembler_initialization(self):
        """Test assembler initializes with correct settings."""
        assembler = TimelineAssembler(allow_gaps=False, validate_sources=True)

        assert assembler.allow_gaps is False
        assert assembler.validate_sources is True

    def test_assemble_simple_timeline(self, sample_clips):
        """Test assembling a simple timeline."""
        assembler = TimelineAssembler(validate_sources=True)
        timeline = assembler.assemble_timeline(sample_clips)

        assert timeline.clip_count == 3
        assert timeline.total_duration == 30.0
        assert timeline.has_gaps is False
        assert timeline.is_valid is True

    def test_assemble_timeline_with_sorting(self, temp_dir):
        """Test timeline assembly with clip sorting."""
        # Create clips out of order
        (temp_dir / "v1.mp4").write_text("v1")
        (temp_dir / "v2.mp4").write_text("v2")

        clips = [
            {
                "clip_id": "clip2",
                "source_path": str(temp_dir / "v2.mp4"),
                "timeline_start": 10.0,
                "timeline_end": 20.0,
            },
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "v1.mp4"),
                "timeline_start": 0.0,
                "timeline_end": 10.0,
            },
        ]

        assembler = TimelineAssembler(validate_sources=True)
        timeline = assembler.assemble_timeline(clips, sort_clips=True)

        # Verify clips are sorted
        assert timeline.clips[0].clip_id == "clip1"
        assert timeline.clips[1].clip_id == "clip2"
        assert timeline.clips[0].index == 0
        assert timeline.clips[1].index == 1

    def test_assemble_timeline_no_clips(self):
        """Test assembling timeline with no clips raises error."""
        assembler = TimelineAssembler()

        with pytest.raises(TimelineAssemblyError, match="no clips"):
            assembler.assemble_timeline([])

    def test_assemble_timeline_missing_fields(self):
        """Test assembling timeline with missing required fields."""
        assembler = TimelineAssembler()

        invalid_clips = [
            {
                "clip_id": "clip1",
                # Missing source_path, timeline_start, timeline_end
            }
        ]

        with pytest.raises(TimelineAssemblyError, match="Invalid clip data"):
            assembler.assemble_timeline(invalid_clips)

    def test_assemble_timeline_overlapping_clips(self, temp_dir):
        """Test assembling timeline with overlapping clips."""
        (temp_dir / "v1.mp4").write_text("v1")
        (temp_dir / "v2.mp4").write_text("v2")

        overlapping_clips = [
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "v1.mp4"),
                "timeline_start": 0.0,
                "timeline_end": 15.0,
            },
            {
                "clip_id": "clip2",
                "source_path": str(temp_dir / "v2.mp4"),
                "timeline_start": 10.0,  # Overlaps with clip1
                "timeline_end": 20.0,
            },
        ]

        assembler = TimelineAssembler(validate_sources=True)

        with pytest.raises(TimelineAssemblyError, match="overlap"):
            assembler.assemble_timeline(overlapping_clips, sort_clips=True)

    def test_assemble_timeline_with_gaps_allowed(self, temp_dir):
        """Test assembling timeline with gaps when allowed."""
        (temp_dir / "v1.mp4").write_text("v1")
        (temp_dir / "v2.mp4").write_text("v2")

        clips_with_gaps = [
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "v1.mp4"),
                "timeline_start": 0.0,
                "timeline_end": 10.0,
            },
            {
                "clip_id": "clip2",
                "source_path": str(temp_dir / "v2.mp4"),
                "timeline_start": 15.0,  # 5-second gap
                "timeline_end": 25.0,
            },
        ]

        assembler = TimelineAssembler(allow_gaps=True, validate_sources=True)
        timeline = assembler.assemble_timeline(clips_with_gaps)

        assert timeline.has_gaps is True
        assert len(timeline.gaps) == 1
        assert timeline.gaps[0] == (10.0, 15.0, 5.0)

    def test_assemble_timeline_with_gaps_not_allowed(self, temp_dir):
        """Test assembling timeline with gaps when not allowed."""
        (temp_dir / "v1.mp4").write_text("v1")
        (temp_dir / "v2.mp4").write_text("v2")

        clips_with_gaps = [
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "v1.mp4"),
                "timeline_start": 0.0,
                "timeline_end": 10.0,
            },
            {
                "clip_id": "clip2",
                "source_path": str(temp_dir / "v2.mp4"),
                "timeline_start": 15.0,
                "timeline_end": 25.0,
            },
        ]

        assembler = TimelineAssembler(allow_gaps=False, validate_sources=True)

        with pytest.raises(TimelineAssemblyError, match="gaps which are not allowed"):
            assembler.assemble_timeline(clips_with_gaps)

    def test_detect_gap_at_beginning(self, temp_dir):
        """Test detection of gap at beginning of timeline."""
        (temp_dir / "v1.mp4").write_text("v1")

        clips = [
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "v1.mp4"),
                "timeline_start": 5.0,  # Starts at 5s, gap from 0-5
                "timeline_end": 15.0,
            },
        ]

        assembler = TimelineAssembler(allow_gaps=True, validate_sources=True)
        timeline = assembler.assemble_timeline(clips)

        assert timeline.has_gaps is True
        assert len(timeline.gaps) == 1
        assert timeline.gaps[0] == (0.0, 5.0, 5.0)

    def test_calculate_timestamps(self, sample_clips):
        """Test timestamp calculation for timeline clips."""
        assembler = TimelineAssembler(validate_sources=True)
        timeline = assembler.assemble_timeline(sample_clips)

        timestamps = assembler.calculate_timestamps(timeline)

        assert len(timestamps) == 3
        assert "clip1" in timestamps
        assert "clip2" in timestamps
        assert "clip3" in timestamps

        # Verify clip1 timestamps
        clip1_ts = timestamps["clip1"]
        assert clip1_ts["timeline_start"] == 0.0
        assert clip1_ts["timeline_end"] == 10.0
        assert clip1_ts["timeline_duration"] == 10.0
        assert clip1_ts["source_start"] == 0.0

        # Verify clip2 timestamps (has trim points)
        clip2_ts = timestamps["clip2"]
        assert clip2_ts["timeline_start"] == 10.0
        assert clip2_ts["timeline_end"] == 20.0
        assert clip2_ts["source_start"] == 5.0
        assert clip2_ts["source_end"] == 15.0

    def test_get_timeline_summary(self, sample_clips):
        """Test getting timeline summary."""
        assembler = TimelineAssembler(validate_sources=True)
        timeline = assembler.assemble_timeline(sample_clips)

        summary = assembler.get_timeline_summary(timeline)

        assert summary["total_duration"] == 30.0
        assert summary["clip_count"] == 3
        assert summary["has_gaps"] is False
        assert summary["gap_count"] == 0
        assert len(summary["clips"]) == 3

        # Check first clip in summary
        first_clip = summary["clips"][0]
        assert first_clip["clip_id"] == "clip1"
        assert first_clip["timeline_start"] == 0.0
        assert first_clip["timeline_end"] == 10.0

    def test_source_file_validation(self, temp_dir):
        """Test source file validation when enabled."""
        clips = [
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "nonexistent.mp4"),  # Doesn't exist
                "timeline_start": 0.0,
                "timeline_end": 10.0,
            },
        ]

        assembler = TimelineAssembler(validate_sources=True)

        with pytest.raises(TimelineAssemblyError, match="Source file not found"):
            assembler.assemble_timeline(clips)

    def test_source_file_validation_disabled(self, temp_dir):
        """Test source file validation when disabled."""
        clips = [
            {
                "clip_id": "clip1",
                "source_path": str(temp_dir / "nonexistent.mp4"),  # Doesn't exist
                "timeline_start": 0.0,
                "timeline_end": 10.0,
            },
        ]

        assembler = TimelineAssembler(validate_sources=False)  # Validation disabled

        # Should not raise error even though file doesn't exist
        timeline = assembler.assemble_timeline(clips)
        assert timeline.clip_count == 1

    def test_complex_timeline_with_trims(self, temp_dir):
        """Test complex timeline with various trim configurations."""
        for i in range(1, 5):
            (temp_dir / f"video{i}.mp4").write_text(f"video {i}")

        clips = [
            {
                "clip_id": "intro",
                "source_path": str(temp_dir / "video1.mp4"),
                "timeline_start": 0.0,
                "timeline_end": 5.0,
                "source_start": 0.0,
                "source_end": 5.0,
                "source_duration": 30.0,
            },
            {
                "clip_id": "main",
                "source_path": str(temp_dir / "video2.mp4"),
                "timeline_start": 5.0,
                "timeline_end": 25.0,
                "source_start": 10.0,
                "source_end": 30.0,
                "source_duration": 60.0,
            },
            {
                "clip_id": "outro",
                "source_path": str(temp_dir / "video3.mp4"),
                "timeline_start": 25.0,
                "timeline_end": 30.0,
                "source_start": 20.0,
                "source_duration": 25.0,
            },
        ]

        assembler = TimelineAssembler(validate_sources=True)
        timeline = assembler.assemble_timeline(clips)

        assert timeline.clip_count == 3
        assert timeline.total_duration == 30.0
        assert timeline.has_gaps is False

        # Verify all clips have correct trim information
        for clip in timeline.clips:
            assert clip.needs_trim is True or clip.is_partial is True
