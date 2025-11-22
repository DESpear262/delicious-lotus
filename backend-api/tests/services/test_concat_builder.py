"""
Unit tests for Concat Demuxer Builder.

Tests the ConcatDemuxerBuilder class and timeline integration.
"""

import tempfile
from pathlib import Path

import pytest
from services.ffmpeg.concat_builder import (
    ConcatDemuxerBuilder,
    ConcatSegment,
    create_concat_segments_from_files,
    create_trimmed_segments,
)
from services.ffmpeg.timeline_assembler import AssembledTimeline, TimelineClip


class TestConcatSegment:
    """Test cases for ConcatSegment dataclass."""

    def test_basic_segment(self):
        """Test creating a basic segment."""
        segment = ConcatSegment(file_path="/tmp/video.mp4")

        assert str(segment.file_path) == "/tmp/video.mp4"
        assert segment.duration is None
        assert segment.inpoint == 0.0
        assert segment.outpoint is None

    def test_segment_with_trim_points(self):
        """Test segment with inpoint and outpoint."""
        segment = ConcatSegment(
            file_path="/tmp/video.mp4",
            inpoint=5.0,
            outpoint=15.0,
            duration=10.0,
        )

        assert segment.inpoint == 5.0
        assert segment.outpoint == 15.0
        assert segment.duration == 10.0

    def test_segment_repr(self):
        """Test string representation."""
        segment = ConcatSegment(
            file_path="/tmp/video.mp4",
            inpoint=5.0,
            outpoint=15.0,
        )

        repr_str = repr(segment)
        assert "ConcatSegment" in repr_str
        assert "5.0s" in repr_str
        assert "15.0" in repr_str


class TestConcatDemuxerBuilder:
    """Test cases for ConcatDemuxerBuilder."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_videos(self, temp_dir):
        """Create sample video files."""
        videos = []
        for i in range(1, 4):
            video = temp_dir / f"video{i}.mp4"
            video.write_text(f"fake video {i}")
            videos.append(video)
        return videos

    def test_builder_initialization(self, temp_dir):
        """Test builder initializes correctly."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        assert builder.temp_dir == temp_dir
        assert len(builder._created_files) == 0

    def test_generate_simple_concat_file(self, temp_dir, sample_videos):
        """Test generating a simple concat file."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        segments = [
            ConcatSegment(file_path=sample_videos[0]),
            ConcatSegment(file_path=sample_videos[1]),
            ConcatSegment(file_path=sample_videos[2]),
        ]

        concat_file = builder.generate_concat_file(segments)

        assert concat_file.exists()
        assert concat_file.suffix == ".txt"

        # Verify content
        content = concat_file.read_text()
        assert "file '" in content
        assert str(sample_videos[0]) in content
        assert str(sample_videos[1]) in content
        assert str(sample_videos[2]) in content

    def test_generate_concat_file_with_trim_points(self, temp_dir, sample_videos):
        """Test concat file with inpoint and outpoint."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        segments = [
            ConcatSegment(
                file_path=sample_videos[0],
                inpoint=5.0,
                outpoint=15.0,
                duration=10.0,
            ),
            ConcatSegment(
                file_path=sample_videos[1],
                inpoint=0.0,
                outpoint=20.0,
                duration=20.0,
            ),
        ]

        concat_file = builder.generate_concat_file(segments)
        content = concat_file.read_text()

        # Verify trim points are in the file
        assert "inpoint 5.0" in content
        assert "outpoint 15.0" in content
        assert "duration 10.0" in content

        assert "inpoint 0.0" not in content  # Don't write inpoint 0
        assert "outpoint 20.0" in content
        assert "duration 20.0" in content

    def test_generate_concat_file_no_segments(self, temp_dir):
        """Test that empty segments list raises error."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        with pytest.raises(ValueError, match="Need at least one segment"):
            builder.generate_concat_file([])

    def test_generate_concat_file_custom_path(self, temp_dir, sample_videos):
        """Test generating concat file with custom path."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)
        custom_path = temp_dir / "my_concat.txt"

        segments = [ConcatSegment(file_path=sample_videos[0])]

        concat_file = builder.generate_concat_file(segments, output_path=custom_path)

        assert concat_file == custom_path
        assert concat_file.exists()

    def test_generate_concat_file_safe_mode(self, temp_dir, sample_videos):
        """Test concat file generation with safe mode."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        segments = [ConcatSegment(file_path=sample_videos[0])]

        concat_file = builder.generate_concat_file(segments, safe_mode=True)
        content = concat_file.read_text()

        # In safe mode, paths should be absolute
        assert str(sample_videos[0].resolve()) in content

    def test_build_concat_command_args(self, temp_dir):
        """Test building FFmpeg command arguments."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        concat_file = temp_dir / "concat.txt"
        output_file = temp_dir / "output.mp4"

        args = builder.build_concat_command_args(concat_file, output_file)

        # Verify command structure
        assert "-f" in args
        assert "concat" in args
        assert "-safe" in args
        assert "1" in args  # Default safe mode is True (1)
        assert "-i" in args
        assert str(concat_file) in args
        assert "-c" in args
        assert "copy" in args
        assert str(output_file) in args

    def test_build_concat_command_args_safe_mode(self, temp_dir):
        """Test building command args with safe mode enabled."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        concat_file = temp_dir / "concat.txt"
        output_file = temp_dir / "output.mp4"

        args = builder.build_concat_command_args(
            concat_file,
            output_file,
            safe_mode=True,
        )

        # Verify safe mode is enabled
        safe_index = args.index("-safe")
        assert args[safe_index + 1] == "1"

    def test_build_concat_command_args_no_codec_copy(self, temp_dir):
        """Test building command without codec copy."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        concat_file = temp_dir / "concat.txt"
        output_file = temp_dir / "output.mp4"

        args = builder.build_concat_command_args(
            concat_file,
            output_file,
            codec_copy=False,
        )

        # Verify codec copy is not present
        assert "-c" not in args or "copy" not in args

    def test_cleanup(self, temp_dir, sample_videos):
        """Test cleanup of temporary files."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        segments = [ConcatSegment(file_path=sample_videos[0])]

        # Generate multiple concat files
        concat_file1 = builder.generate_concat_file(segments)
        concat_file2 = builder.generate_concat_file(segments)

        assert concat_file1.exists()
        assert concat_file2.exists()

        # Cleanup
        builder.cleanup()

        # Files should be deleted
        assert not concat_file1.exists()
        assert not concat_file2.exists()
        assert len(builder._created_files) == 0

    def test_context_manager(self, temp_dir, sample_videos):
        """Test context manager cleanup."""
        concat_file = None

        with ConcatDemuxerBuilder(temp_dir=temp_dir) as builder:
            segments = [ConcatSegment(file_path=sample_videos[0])]
            concat_file = builder.generate_concat_file(segments)

            assert concat_file.exists()

        # File should be cleaned up after exiting context
        assert not concat_file.exists()

    def test_create_segments_from_timeline(self, temp_dir, sample_videos):
        """Test creating concat segments from timeline."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        # Create timeline with clips
        clips = [
            TimelineClip(
                clip_id="clip1",
                source_path=sample_videos[0],
                timeline_start=0.0,
                timeline_end=10.0,
                source_start=0.0,
                source_end=10.0,
                index=0,
            ),
            TimelineClip(
                clip_id="clip2",
                source_path=sample_videos[1],
                timeline_start=10.0,
                timeline_end=25.0,
                source_start=5.0,
                source_end=20.0,
                index=1,
            ),
        ]

        timeline = AssembledTimeline(clips=clips, total_duration=25.0)

        segments = builder.create_segments_from_timeline(timeline)

        assert len(segments) == 2

        # Verify first segment
        assert segments[0].file_path == sample_videos[0]
        assert segments[0].inpoint == 0.0
        assert segments[0].outpoint == 10.0
        assert segments[0].duration == 10.0

        # Verify second segment
        assert segments[1].file_path == sample_videos[1]
        assert segments[1].inpoint == 5.0
        assert segments[1].outpoint == 20.0
        assert segments[1].duration == 15.0

    def test_create_segments_from_empty_timeline(self, temp_dir):
        """Test creating segments from empty timeline raises error."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)
        timeline = AssembledTimeline(clips=[], total_duration=0.0)

        with pytest.raises(ValueError, match="no clips"):
            builder.create_segments_from_timeline(timeline)

    def test_generate_concat_file_from_timeline(self, temp_dir, sample_videos):
        """Test generating concat file directly from timeline."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        clips = [
            TimelineClip(
                clip_id="clip1",
                source_path=sample_videos[0],
                timeline_start=0.0,
                timeline_end=10.0,
                source_start=2.0,
                source_end=12.0,
                index=0,
            ),
            TimelineClip(
                clip_id="clip2",
                source_path=sample_videos[1],
                timeline_start=10.0,
                timeline_end=20.0,
                source_start=0.0,
                source_end=10.0,
                index=1,
            ),
        ]

        timeline = AssembledTimeline(clips=clips, total_duration=20.0)

        concat_file = builder.generate_concat_file_from_timeline(timeline)

        assert concat_file.exists()

        content = concat_file.read_text()

        # Verify both videos are in concat file
        assert str(sample_videos[0]) in content
        assert str(sample_videos[1]) in content

        # Verify trim points
        assert "inpoint 2.0" in content
        assert "outpoint 12.0" in content
        assert "outpoint 10.0" in content

    def test_clip_to_segment_conversion(self, temp_dir, sample_videos):
        """Test internal _clip_to_segment method."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        clip = TimelineClip(
            clip_id="test",
            source_path=sample_videos[0],
            timeline_start=5.0,
            timeline_end=15.0,
            source_start=10.0,
            source_end=20.0,
            index=0,
        )

        segment = builder._clip_to_segment(clip)

        assert segment.file_path == sample_videos[0]
        assert segment.inpoint == 10.0
        assert segment.outpoint == 20.0
        assert segment.duration == 10.0

    def test_clip_to_segment_no_outpoint(self, temp_dir, sample_videos):
        """Test conversion when clip has no outpoint."""
        builder = ConcatDemuxerBuilder(temp_dir=temp_dir)

        clip = TimelineClip(
            clip_id="test",
            source_path=sample_videos[0],
            timeline_start=0.0,
            timeline_end=10.0,
            source_start=0.0,
            source_end=None,  # No explicit end
            index=0,
        )

        segment = builder._clip_to_segment(clip)

        assert segment.file_path == sample_videos[0]
        assert segment.inpoint == 0.0
        assert segment.outpoint is None
        assert segment.duration is None


class TestHelperFunctions:
    """Test helper functions for creating segments."""

    def test_create_concat_segments_from_files(self):
        """Test creating segments from file list."""
        files = ["/tmp/video1.mp4", "/tmp/video2.mp4", "/tmp/video3.mp4"]

        segments = create_concat_segments_from_files(files)

        assert len(segments) == 3
        for i, segment in enumerate(segments):
            assert str(segment.file_path) == files[i]
            assert segment.inpoint == 0.0
            assert segment.outpoint is None

    def test_create_concat_segments_from_files_with_durations(self):
        """Test creating segments with durations."""
        files = ["/tmp/video1.mp4", "/tmp/video2.mp4"]
        durations = [10.0, 20.0]

        segments = create_concat_segments_from_files(files, durations=durations)

        assert len(segments) == 2
        assert segments[0].duration == 10.0
        assert segments[1].duration == 20.0

    def test_create_trimmed_segments(self):
        """Test creating trimmed segments from single file."""
        file_path = "/tmp/video.mp4"
        trim_points = [(0.0, 10.0), (30.0, 40.0), (60.0, 70.0)]

        segments = create_trimmed_segments(file_path, trim_points)

        assert len(segments) == 3

        # Verify first segment
        assert segments[0].file_path == file_path
        assert segments[0].inpoint == 0.0
        assert segments[0].outpoint == 10.0
        assert segments[0].duration == 10.0

        # Verify second segment
        assert segments[1].inpoint == 30.0
        assert segments[1].outpoint == 40.0
        assert segments[1].duration == 10.0

        # Verify third segment
        assert segments[2].inpoint == 60.0
        assert segments[2].outpoint == 70.0
        assert segments[2].duration == 10.0


class TestIntegrationScenarios:
    """Test integration scenarios combining timeline and concat builder."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_complete_workflow(self, temp_dir):
        """Test complete workflow from timeline to concat file."""
        # Create sample videos
        videos = []
        for i in range(1, 4):
            video = temp_dir / f"video{i}.mp4"
            video.write_text(f"video {i}")
            videos.append(video)

        # Create timeline with various trim configurations
        clips = [
            TimelineClip(
                clip_id="intro",
                source_path=videos[0],
                timeline_start=0.0,
                timeline_end=5.0,
                source_start=0.0,
                source_end=5.0,
                index=0,
            ),
            TimelineClip(
                clip_id="main",
                source_path=videos[1],
                timeline_start=5.0,
                timeline_end=20.0,
                source_start=10.0,
                source_end=25.0,
                index=1,
            ),
            TimelineClip(
                clip_id="outro",
                source_path=videos[2],
                timeline_start=20.0,
                timeline_end=25.0,
                source_start=0.0,
                source_end=5.0,
                index=2,
            ),
        ]

        timeline = AssembledTimeline(clips=clips, total_duration=25.0)

        # Generate concat file
        with ConcatDemuxerBuilder(temp_dir=temp_dir) as builder:
            concat_file = builder.generate_concat_file_from_timeline(timeline)

            # Verify file was created
            assert concat_file.exists()

            # Verify content has all clips with correct trim points
            content = concat_file.read_text()

            assert str(videos[0]) in content
            assert str(videos[1]) in content
            assert str(videos[2]) in content

            # Verify trim points are correct
            lines = content.strip().split("\n")

            # Each clip should have: file, (optional inpoint), outpoint, duration
            # Count file directives
            file_lines = [line for line in lines if line.startswith("file ")]
            assert len(file_lines) == 3

        # File should be cleaned up after context exit
        assert not concat_file.exists()
