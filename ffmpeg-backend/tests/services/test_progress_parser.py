"""
Tests for FFmpeg Progress Parser.

Tests parsing of FFmpeg stderr output for progress tracking,
ETA calculation, and multi-stage progress management.
"""

from __future__ import annotations

import pytest
from services.ffmpeg.progress_parser import (
    FFmpegProgress,
    FFmpegProgressParser,
    MultiStageProgressParser,
)


class TestFFmpegProgress:
    """Tests for FFmpegProgress dataclass."""

    def test_default_creation(self):
        """Test creating progress with defaults."""
        progress = FFmpegProgress()

        assert progress.frame == 0
        assert progress.fps == 0.0
        assert progress.bitrate == 0.0
        assert progress.total_size == 0
        assert progress.out_time_ms == 0
        assert progress.speed == 0.0
        assert progress.progress_percent == 0.0
        assert progress.eta_seconds is None

    def test_custom_creation(self):
        """Test creating progress with custom values."""
        progress = FFmpegProgress(
            frame=100,
            fps=30.0,
            bitrate=2500.0,
            total_size=1024000,
            out_time_ms=3330000,
            speed=1.5,
            progress_percent=2.8,
            eta_seconds=115.5,
        )

        assert progress.frame == 100
        assert progress.fps == 30.0
        assert progress.bitrate == 2500.0
        assert progress.total_size == 1024000
        assert progress.out_time_ms == 3330000
        assert progress.speed == 1.5
        assert progress.progress_percent == 2.8
        assert progress.eta_seconds == 115.5

    def test_out_time_seconds_property(self):
        """Test converting out_time_ms to seconds."""
        progress = FFmpegProgress(out_time_ms=3330000)  # 3.33 seconds

        assert progress.out_time_seconds == 3.33

    def test_out_time_seconds_zero(self):
        """Test out_time_seconds with zero value."""
        progress = FFmpegProgress(out_time_ms=0)

        assert progress.out_time_seconds == 0.0

    def test_repr(self):
        """Test string representation."""
        progress = FFmpegProgress(
            frame=100,
            fps=30.5,
            speed=1.25,
            progress_percent=15.7,
        )

        repr_str = repr(progress)
        assert "frame=100" in repr_str
        assert "fps=30.5" in repr_str
        assert "speed=1.25x" in repr_str
        assert "progress=15.7%" in repr_str


class TestFFmpegProgressParser:
    """Tests for FFmpegProgressParser."""

    @pytest.fixture
    def parser(self) -> FFmpegProgressParser:
        """Create progress parser instance."""
        return FFmpegProgressParser(total_duration=120.0)

    def test_initialization(self, parser):
        """Test parser initialization."""
        assert parser.total_duration == 120.0
        assert parser.window_size == 10

    def test_initialization_without_duration(self):
        """Test parser initialization without duration."""
        parser = FFmpegProgressParser()

        assert parser.total_duration is None

    def test_parse_simple_progress_line(self, parser):
        """Test parsing a simple progress line."""
        line = "frame=  100 fps=30.0 q=-1.0 size=    1024kB time=00:00:03.33 bitrate=2510.3kbits/s speed=1.0x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert progress.frame == 100
        assert progress.fps == 30.0
        assert progress.total_size == 1024 * 1024  # kB to bytes
        assert abs(progress.out_time_seconds - 3.33) < 0.01
        assert progress.bitrate == 2510.3
        assert progress.speed == 1.0

    def test_parse_line_calculates_progress_percent(self, parser):
        """Test progress percentage calculation."""
        # 6 seconds out of 120 total = 5%
        line = "frame=  180 fps=30.0 time=00:00:06.00 bitrate=2500.0kbits/s speed=1.0x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert abs(progress.progress_percent - 5.0) < 0.1

    def test_parse_line_without_duration(self):
        """Test parsing without total duration set."""
        parser = FFmpegProgressParser()
        line = "frame=  100 fps=30.0 time=00:00:03.33 speed=1.0x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert progress.frame == 100
        assert progress.progress_percent == 0.0  # Can't calculate without duration

    def test_parse_line_with_large_time(self, parser):
        """Test parsing line with large time values."""
        line = "frame= 5400 fps=30.0 time=00:03:00.00 bitrate=2500.0kbits/s speed=1.5x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert progress.frame == 5400
        assert progress.out_time_seconds == 180.0  # 3 minutes

    def test_parse_line_invalid_line(self, parser):
        """Test parsing line without progress info."""
        line = "Starting FFmpeg encoding..."
        progress = parser.parse_line(line)

        assert progress is None

    def test_parse_line_partial_info(self, parser):
        """Test parsing line with partial information."""
        line = "frame=  100 time=00:00:03.33"
        progress = parser.parse_line(line)

        assert progress is not None
        assert progress.frame == 100
        assert progress.fps == 0.0  # Not in line
        assert abs(progress.out_time_seconds - 3.33) < 0.01

    def test_eta_calculation(self, parser):
        """Test ETA calculation with speed data."""
        # Parse multiple lines to build speed window
        lines = [
            "frame=  30 fps=30.0 time=00:00:01.00 speed=1.0x",
            "frame=  60 fps=30.0 time=00:00:02.00 speed=1.0x",
            "frame=  90 fps=30.0 time=00:00:03.00 speed=1.0x",
        ]

        for line in lines:
            progress = parser.parse_line(line)

        assert progress is not None
        assert progress.eta_seconds is not None
        # At 3 seconds processed, 117 seconds remaining, at 1.0x speed = 117s ETA
        assert 115 < progress.eta_seconds < 120

    def test_eta_with_varying_speed(self, parser):
        """Test ETA calculation with varying processing speeds."""
        lines = [
            "frame=  30 fps=30.0 time=00:00:01.00 speed=0.5x",
            "frame=  60 fps=30.0 time=00:00:02.00 speed=1.0x",
            "frame=  90 fps=30.0 time=00:00:03.00 speed=1.5x",
        ]

        progress = None
        for line in lines:
            progress = parser.parse_line(line)

        assert progress is not None
        assert progress.eta_seconds is not None
        # Should use average speed for calculation

    def test_parse_duration_line(self, parser):
        """Test parsing duration from FFmpeg output."""
        line = "  Duration: 00:02:30.45, start: 0.000000, bitrate: 1234 kb/s"
        duration = parser.parse_duration_line(line)

        assert duration is not None
        assert abs(duration - 150.45) < 0.01

    def test_parse_duration_line_short_video(self, parser):
        """Test parsing duration for short video."""
        line = "  Duration: 00:00:05.50, start: 0.000000, bitrate: 5000 kb/s"
        duration = parser.parse_duration_line(line)

        assert duration is not None
        assert abs(duration - 5.5) < 0.01

    def test_parse_duration_line_long_video(self, parser):
        """Test parsing duration for long video."""
        line = "  Duration: 01:30:25.75, start: 0.000000, bitrate: 2500 kb/s"
        duration = parser.parse_duration_line(line)

        assert duration is not None
        expected = 1 * 3600 + 30 * 60 + 25.75
        assert abs(duration - expected) < 0.01

    def test_parse_duration_line_no_duration(self, parser):
        """Test parsing line without duration info."""
        line = "frame=  100 fps=30.0 time=00:00:03.33"
        duration = parser.parse_duration_line(line)

        assert duration is None

    def test_set_total_duration(self, parser):
        """Test setting total duration."""
        parser.set_total_duration(240.0)

        assert parser.total_duration == 240.0

    def test_get_last_progress(self, parser):
        """Test retrieving last progress."""
        line = "frame=  100 fps=30.0 time=00:00:03.33 speed=1.0x"
        parser.parse_line(line)

        last = parser.get_last_progress()

        assert last.frame == 100
        assert last.fps == 30.0

    def test_reset(self, parser):
        """Test resetting parser state."""
        # Parse some lines
        parser.parse_line("frame=  100 fps=30.0 time=00:00:03.33 speed=1.0x")
        parser.parse_line("frame=  200 fps=30.0 time=00:00:06.67 speed=1.0x")

        # Reset
        parser.reset()

        last = parser.get_last_progress()
        assert last.frame == 0
        assert last.fps == 0.0

    def test_progress_caps_at_100_percent(self, parser):
        """Test progress doesn't exceed 100%."""
        # Time exceeds total duration
        line = "frame= 3600 fps=30.0 time=00:02:05.00 bitrate=2500.0kbits/s speed=1.0x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert progress.progress_percent <= 100.0

    def test_speed_window_accumulation(self, parser):
        """Test speed values accumulate in rolling window."""
        # Window size is 10, add 12 values
        for i in range(12):
            line = f"frame={30 * (i + 1)} fps=30.0 time=00:00:{i+1:02d}.00 speed={(i % 3) + 1.0}x"
            parser.parse_line(line)

        # Window should only keep last 10 values
        assert len(parser._speed_window) == 10

    def test_parse_line_with_fractional_fps(self, parser):
        """Test parsing line with fractional FPS."""
        line = "frame=  100 fps=29.97 time=00:00:03.34 speed=1.0x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert abs(progress.fps - 29.97) < 0.01

    def test_parse_line_with_high_bitrate(self, parser):
        """Test parsing line with high bitrate."""
        line = "frame=  100 fps=30.0 time=00:00:03.33 bitrate=25103.5kbits/s speed=1.0x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert abs(progress.bitrate - 25103.5) < 0.1


class TestMultiStageProgressParser:
    """Tests for MultiStageProgressParser."""

    @pytest.fixture
    def parser(self) -> MultiStageProgressParser:
        """Create multi-stage parser instance."""
        return MultiStageProgressParser(
            stage_weights={
                "normalize": 0.2,
                "compose": 0.6,
                "encode": 0.2,
            }
        )

    def test_initialization(self, parser):
        """Test parser initialization."""
        assert len(parser.stage_weights) == 3
        assert parser.stage_weights["normalize"] == 0.2
        assert parser.stage_weights["compose"] == 0.6
        assert parser.stage_weights["encode"] == 0.2

    def test_initialization_without_weights(self):
        """Test initialization without stage weights."""
        parser = MultiStageProgressParser()

        assert parser.stage_weights == {}

    def test_initialization_invalid_weights(self):
        """Test initialization with invalid weights."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            MultiStageProgressParser(
                stage_weights={
                    "stage1": 0.5,
                    "stage2": 0.3,  # Only sums to 0.8
                }
            )

    def test_set_stage(self, parser):
        """Test setting current stage."""
        parser.set_stage("normalize", duration=120.0)

        assert parser.current_stage == "normalize"
        assert "normalize" in parser.stage_parsers
        assert parser.stage_parsers["normalize"].total_duration == 120.0

    def test_set_stage_unknown(self, parser):
        """Test setting unknown stage."""
        with pytest.raises(ValueError, match="Unknown stage"):
            parser.set_stage("unknown_stage")

    def test_set_stage_updates_duration(self, parser):
        """Test updating stage duration."""
        parser.set_stage("normalize", duration=120.0)
        parser.set_stage("normalize", duration=240.0)

        assert parser.stage_parsers["normalize"].total_duration == 240.0

    def test_parse_line_single_stage(self, parser):
        """Test parsing with single stage progress."""
        parser.set_stage("normalize", duration=120.0)

        # 6 seconds out of 120 = 5% of normalize stage
        # 5% * 0.2 weight = 1% overall
        line = "frame=  180 fps=30.0 time=00:00:06.00 speed=1.0x"
        progress = parser.parse_line(line)

        assert progress is not None
        assert abs(progress.progress_percent - 1.0) < 0.1

    def test_parse_line_multiple_stages(self, parser):
        """Test parsing across multiple stages."""
        # Stage 1: Normalize (20% weight)
        parser.set_stage("normalize", duration=120.0)
        parser.parse_line("frame= 3600 fps=30.0 time=00:02:00.00 speed=1.0x")  # 100% of stage

        # Stage 2: Compose (60% weight)
        parser.set_stage("compose", duration=180.0)
        parser.parse_line("frame= 2700 fps=30.0 time=00:01:30.00 speed=1.0x")  # 50% of stage

        progress = parser.get_overall_progress()

        # 20% (normalize complete) + 30% (compose half done) = 50% overall
        assert abs(progress - 50.0) < 1.0

    def test_parse_line_no_stage_set(self, parser):
        """Test parsing without setting stage."""
        with pytest.raises(RuntimeError, match="No current stage set"):
            parser.parse_line("frame=  100 fps=30.0 time=00:00:03.33 speed=1.0x")

    def test_get_overall_progress(self, parser):
        """Test getting overall progress."""
        parser.set_stage("normalize", duration=100.0)
        parser.parse_line("frame= 3000 fps=30.0 time=00:01:40.00 speed=1.0x")  # 100%

        parser.set_stage("compose", duration=200.0)
        parser.parse_line("frame= 3000 fps=30.0 time=00:01:40.00 speed=1.0x")  # 50%

        overall = parser.get_overall_progress()

        # 100% * 0.2 + 50% * 0.6 + 0% * 0.2 = 50%
        assert abs(overall - 50.0) < 1.0

    def test_get_stage_progress(self, parser):
        """Test getting specific stage progress."""
        parser.set_stage("normalize", duration=120.0)
        parser.parse_line("frame= 1800 fps=30.0 time=00:01:00.00 speed=1.0x")  # 50%

        stage_progress = parser.get_stage_progress("normalize")

        assert abs(stage_progress - 50.0) < 1.0

    def test_get_stage_progress_unknown_stage(self, parser):
        """Test getting progress for unknown stage."""
        progress = parser.get_stage_progress("unknown")

        assert progress == 0.0

    def test_reset(self, parser):
        """Test resetting multi-stage parser."""
        parser.set_stage("normalize", duration=120.0)
        parser.parse_line("frame=  100 fps=30.0 time=00:00:03.33 speed=1.0x")

        parser.reset()

        assert parser.current_stage is None
        assert parser.get_overall_progress() == 0.0

    def test_complete_pipeline_workflow(self, parser):
        """Test complete multi-stage pipeline workflow."""
        # Stage 1: Normalize (20% weight, 60s duration)
        parser.set_stage("normalize", duration=60.0)
        parser.parse_line("frame= 1800 fps=30.0 time=00:01:00.00 speed=1.0x")  # 100%

        assert abs(parser.get_overall_progress() - 20.0) < 1.0

        # Stage 2: Compose (60% weight, 120s duration)
        parser.set_stage("compose", duration=120.0)
        parser.parse_line("frame= 1800 fps=30.0 time=00:01:00.00 speed=1.0x")  # 50%

        assert abs(parser.get_overall_progress() - 50.0) < 1.0

        # Continue compose to 100%
        parser.parse_line("frame= 3600 fps=30.0 time=00:02:00.00 speed=1.0x")  # 100%

        assert abs(parser.get_overall_progress() - 80.0) < 1.0

        # Stage 3: Encode (20% weight, 90s duration)
        parser.set_stage("encode", duration=90.0)
        parser.parse_line("frame= 2700 fps=30.0 time=00:01:30.00 speed=1.0x")  # 100%

        assert abs(parser.get_overall_progress() - 100.0) < 1.0


class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios."""

    def test_single_pass_encoding_workflow(self):
        """Test progress tracking for single-pass encoding."""
        parser = FFmpegProgressParser(total_duration=180.0)

        # Simulate FFmpeg output over time
        sample_lines = [
            "frame=   30 fps=30.0 time=00:00:01.00 bitrate=2500.0kbits/s speed=1.0x",
            "frame=  900 fps=30.0 time=00:00:30.00 bitrate=2500.0kbits/s speed=1.2x",
            "frame= 1800 fps=30.0 time=00:01:00.00 bitrate=2500.0kbits/s speed=1.1x",
            "frame= 2700 fps=30.0 time=00:01:30.00 bitrate=2500.0kbits/s speed=1.0x",
            "frame= 3600 fps=30.0 time=00:02:00.00 bitrate=2500.0kbits/s speed=1.0x",
            "frame= 4500 fps=30.0 time=00:02:30.00 bitrate=2500.0kbits/s speed=1.0x",
            "frame= 5400 fps=30.0 time=00:03:00.00 bitrate=2500.0kbits/s speed=1.0x",
        ]

        for line in sample_lines:
            progress = parser.parse_line(line)
            assert progress is not None

        # Final progress should be 100%
        assert abs(progress.progress_percent - 100.0) < 1.0

    def test_auto_detect_duration_workflow(self):
        """Test workflow with auto-detected duration."""
        parser = FFmpegProgressParser()

        # First, FFmpeg outputs duration
        duration_line = "  Duration: 00:02:00.00, start: 0.000000, bitrate: 2500 kb/s"
        duration = parser.parse_duration_line(duration_line)

        assert duration is not None
        parser.set_total_duration(duration)

        # Then parse progress
        progress_line = "frame= 1800 fps=30.0 time=00:01:00.00 speed=1.0x"
        progress = parser.parse_line(progress_line)

        assert progress is not None
        assert abs(progress.progress_percent - 50.0) < 1.0

    def test_two_pass_encoding_workflow(self):
        """Test two-pass encoding with multi-stage parser."""
        parser = MultiStageProgressParser(
            stage_weights={
                "pass1": 0.4,  # First pass analysis
                "pass2": 0.6,  # Second pass encoding
            }
        )

        # Pass 1: Analysis (faster, 40% weight)
        parser.set_stage("pass1", duration=120.0)
        parser.parse_line("frame= 3600 fps=30.0 time=00:02:00.00 speed=2.0x")  # 100%

        assert abs(parser.get_overall_progress() - 40.0) < 1.0

        # Pass 2: Encoding (slower, 60% weight)
        parser.set_stage("pass2", duration=120.0)
        parser.parse_line("frame= 1800 fps=30.0 time=00:01:00.00 speed=0.8x")  # 50%

        assert abs(parser.get_overall_progress() - 70.0) < 1.0

    def test_composition_pipeline_workflow(self):
        """Test full composition pipeline with normalization, composition, and encoding."""
        parser = MultiStageProgressParser(
            stage_weights={
                "normalize": 0.15,
                "compose": 0.50,
                "encode": 0.35,
            }
        )

        # Stage 1: Normalize clips
        parser.set_stage("normalize", duration=90.0)
        for i in range(1, 4):
            time = i * 30
            parser.parse_line(f"frame={900 * i} fps=30.0 time=00:00:{time:02d}.00 speed=1.5x")

        assert abs(parser.get_overall_progress() - 15.0) < 1.0

        # Stage 2: Compose timeline
        parser.set_stage("compose", duration=180.0)
        for i in range(1, 7):
            time = i * 30
            parser.parse_line(f"frame={900 * i} fps=30.0 time=00:00:{time:02d}.00 speed=1.0x")

        assert abs(parser.get_overall_progress() - 65.0) < 1.0

        # Stage 3: Final encoding
        parser.set_stage("encode", duration=120.0)
        parser.parse_line("frame= 3600 fps=30.0 time=00:02:00.00 speed=0.9x")  # 100%

        assert abs(parser.get_overall_progress() - 100.0) < 1.0

    def test_eta_accuracy_over_time(self):
        """Test that ETA becomes more accurate as processing continues."""
        parser = FFmpegProgressParser(total_duration=300.0)

        # Early in processing (high variance expected)
        parser.parse_line("frame=   30 fps=30.0 time=00:00:01.00 speed=0.5x")
        early_eta = parser.get_last_progress().eta_seconds

        # Later in processing (more accurate)
        for i in range(2, 11):
            parser.parse_line(f"frame={30 * i} fps=30.0 time=00:00:{i:02d}.00 speed=1.0x")

        late_eta = parser.get_last_progress().eta_seconds

        # Both should be reasonable
        assert early_eta is not None
        assert late_eta is not None
        assert late_eta > 0
