"""
Unit tests for Thumbnail Generator Service.

Tests thumbnail generation, multiple sizes, formats, and error handling.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from services.thumbnail_generator import (
    THUMBNAIL_DIMENSIONS,
    ThumbnailFormat,
    ThumbnailGenerator,
    ThumbnailGeneratorError,
    ThumbnailSize,
)


class TestThumbnailSize:
    """Test cases for ThumbnailSize enum."""

    def test_thumbnail_sizes(self):
        """Test that all expected sizes are defined."""
        assert ThumbnailSize.SMALL == "small"
        assert ThumbnailSize.MEDIUM == "medium"
        assert ThumbnailSize.LARGE == "large"

    def test_thumbnail_dimensions(self):
        """Test that dimensions are correct for each size."""
        assert THUMBNAIL_DIMENSIONS[ThumbnailSize.SMALL] == (320, 180)
        assert THUMBNAIL_DIMENSIONS[ThumbnailSize.MEDIUM] == (640, 360)
        assert THUMBNAIL_DIMENSIONS[ThumbnailSize.LARGE] == (1280, 720)


class TestThumbnailFormat:
    """Test cases for ThumbnailFormat enum."""

    def test_thumbnail_formats(self):
        """Test that all expected formats are defined."""
        assert ThumbnailFormat.WEBP == "webp"
        assert ThumbnailFormat.JPEG == "jpeg"
        assert ThumbnailFormat.PNG == "png"


class TestThumbnailGenerator:
    """Test cases for ThumbnailGenerator."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for testing."""
        return tmp_path / "thumbnails"

    @pytest.fixture
    def generator(self, temp_dir):
        """Create ThumbnailGenerator instance for testing."""
        with patch("services.thumbnail_generator.get_settings") as mock_settings:
            mock_settings.return_value.temp_dir = str(temp_dir.parent)
            mock_settings.return_value.ffmpeg_path = "ffmpeg"
            mock_settings.return_value.ffprobe_path = "ffprobe"

            return ThumbnailGenerator(output_dir=temp_dir)

    def test_generator_initialization(self, generator, temp_dir):
        """Test generator initializes correctly."""
        assert generator.output_dir == temp_dir
        assert generator.output_dir.exists()
        assert generator.ffmpeg_path == "ffmpeg"
        assert generator.ffprobe_path == "ffprobe"

    def test_generate_thumbnail_file_not_found(self, generator):
        """Test that FileNotFoundError is raised for non-existent video."""
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            generator.generate_thumbnail(video_path="/nonexistent/video.mp4")

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_generate_thumbnail_success(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test successful thumbnail generation."""
        # Create test video file
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 10.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # Mock subprocess
        mock_run.return_value = MagicMock(returncode=0)

        # Create output file (simulating FFmpeg)
        output_path = generator.output_dir / "test_medium_1s.webp"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        output_path.write_bytes(b"fake thumbnail data")

        # Generate thumbnail
        result = generator.generate_thumbnail(
            video_path=video_file,
            output_path=output_path,
            timestamp=1.0,
            size=ThumbnailSize.MEDIUM,
        )

        assert result.path == output_path
        assert result.metadata.size == "medium"
        assert result.metadata.width == 640
        assert result.metadata.height == 360
        assert result.metadata.timestamp == 1.0
        assert result.was_fallback is False

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_generate_thumbnail_different_sizes(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test generating thumbnails of different sizes."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 10.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # Mock subprocess
        mock_run.return_value = MagicMock(returncode=0)

        for size in [ThumbnailSize.SMALL, ThumbnailSize.MEDIUM, ThumbnailSize.LARGE]:
            output_path = generator.output_dir / f"test_{size.value}.webp"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.touch()

            result = generator.generate_thumbnail(
                video_path=video_file,
                output_path=output_path,
                size=size,
            )

            width, height = THUMBNAIL_DIMENSIONS[size]
            assert result.metadata.width == width
            assert result.metadata.height == height

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_generate_thumbnail_webp_fallback_to_jpeg(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test fallback from WebP to JPEG when WebP fails."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 10.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # First call (WebP) fails, second call (JPEG) succeeds
        call_count = [0]

        def run_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # WebP fails
                raise subprocess.CalledProcessError(1, "ffmpeg", stderr="WebP encoding failed")
            else:
                # JPEG succeeds
                # Create JPEG output
                output_path = generator.output_dir / "test_medium_1s.jpeg"
                output_path.touch()
                return MagicMock(returncode=0)

        mock_run.side_effect = run_side_effect

        # Generate with WebP (should fallback to JPEG)
        result = generator.generate_thumbnail(
            video_path=video_file,
            timestamp=1.0,
            size=ThumbnailSize.MEDIUM,
            format=ThumbnailFormat.WEBP,
            use_fallback=True,
        )

        assert result.was_fallback is True
        assert result.metadata.format == "jpeg"
        assert result.path.suffix == ".jpeg"

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_generate_thumbnail_no_fallback_raises_error(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test that error is raised when fallback is disabled."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 10.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # FFmpeg fails
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "ffmpeg", stderr="WebP encoding failed"
        )

        with pytest.raises(ThumbnailGeneratorError, match="FFmpeg failed"):
            generator.generate_thumbnail(
                video_path=video_file,
                format=ThumbnailFormat.WEBP,
                use_fallback=False,
            )

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_generate_thumbnail_timeout(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test timeout handling."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 10.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # FFmpeg times out
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 30)

        with pytest.raises(ThumbnailGeneratorError, match="timed out"):
            generator.generate_thumbnail(video_path=video_file, timeout=30)

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_generate_multiple_thumbnails(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test generating multiple thumbnail sizes."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 10.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # Mock subprocess
        def run_side_effect(*args, **kwargs):
            # Create output file based on command
            cmd = args[0]
            output_path = Path(cmd[-1])
            output_path.touch()
            return MagicMock(returncode=0)

        mock_run.side_effect = run_side_effect

        # Generate multiple sizes
        results = generator.generate_multiple_thumbnails(
            video_path=video_file,
            timestamp=1.0,
        )

        assert len(results) == 3
        assert "small" in results
        assert "medium" in results
        assert "large" in results

        for size_name, result in results.items():
            assert result.metadata.size == size_name
            assert result.path.exists()

    @patch("services.thumbnail_generator.InputFileManager")
    def test_smart_timestamp_selection(self, mock_input_manager_class, generator, tmp_path):
        """Test smart timestamp selection to avoid edges."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Test timestamp adjustment for video start
        adjusted = generator._select_smart_timestamp(
            video_path=video_file,
            requested_timestamp=0.1,  # Too close to start
            video_duration=10.0,
        )
        assert adjusted >= 0.5  # Should be at least 0.5s in

        # Test timestamp adjustment for video end
        adjusted = generator._select_smart_timestamp(
            video_path=video_file,
            requested_timestamp=9.9,  # Too close to end
            video_duration=10.0,
        )
        assert adjusted <= 9.5  # Should be at least 0.5s before end

        # Test valid timestamp (no adjustment needed)
        adjusted = generator._select_smart_timestamp(
            video_path=video_file,
            requested_timestamp=5.0,
            video_duration=10.0,
        )
        assert adjusted == 5.0

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_timestamp_exceeds_duration(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test handling of timestamp that exceeds video duration."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager with short duration
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 5.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # Mock subprocess
        mock_run.return_value = MagicMock(returncode=0)

        # Create output
        output_path = generator.output_dir / "test.webp"
        output_path.touch()

        # Try to generate at timestamp beyond duration
        result = generator.generate_thumbnail(
            video_path=video_file,
            output_path=output_path,
            timestamp=10.0,  # Exceeds 5.0s duration
        )

        # Should use adjusted timestamp
        assert result.metadata.timestamp < 5.0

    def test_cleanup_thumbnails(self, generator, temp_dir):
        """Test cleanup of old thumbnail files."""
        # Create some thumbnail files
        old_file = temp_dir / "old_thumbnail.webp"
        old_file.touch()

        new_file = temp_dir / "new_thumbnail.webp"
        new_file.touch()

        # Set old file modification time to 25 hours ago
        import os
        import time

        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))

        # Cleanup files older than 24 hours
        deleted = generator.cleanup_thumbnails(older_than_hours=24)

        assert deleted >= 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_cleanup_thumbnails_no_files(self, generator):
        """Test cleanup when no files exist."""
        deleted = generator.cleanup_thumbnails()
        assert deleted == 0

    @patch("services.thumbnail_generator.InputFileManager")
    @patch("subprocess.run")
    def test_generate_thumbnail_png_format(
        self, mock_run, mock_input_manager_class, generator, tmp_path
    ):
        """Test generating PNG format thumbnail."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()

        # Mock input manager
        mock_manager = MagicMock()
        mock_manager.probe_file.return_value.duration = 10.0
        mock_input_manager_class.return_value = mock_manager
        generator.input_manager = mock_manager

        # Mock subprocess
        mock_run.return_value = MagicMock(returncode=0)

        # Create PNG output
        output_path = generator.output_dir / "test.png"
        output_path.touch()

        result = generator.generate_thumbnail(
            video_path=video_file,
            output_path=output_path,
            format=ThumbnailFormat.PNG,
        )

        assert result.metadata.format == "png"
        assert result.path.suffix == ".png"
