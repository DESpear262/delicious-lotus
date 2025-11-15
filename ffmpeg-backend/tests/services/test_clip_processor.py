"""
Unit tests for Clip Processor Service.

Tests clip processing, format validation, and error handling.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from services.clip_processor import (
    ClipFormat,
    ClipProcessingOptions,
    ClipProcessingResult,
    ClipProcessor,
    ProcessingStatus,
    UnsupportedFormatError,
)
from services.ffmpeg.normalizer import NormalizationResult, NormalizationSettings


class TestClipFormat:
    """Test cases for ClipFormat enum."""

    def test_supported_formats(self):
        """Test that all expected formats are supported."""
        expected_formats = {"mp4", "mov", "avi", "mkv", "webm"}
        actual_formats = {fmt.value for fmt in ClipFormat}
        assert actual_formats == expected_formats


class TestClipProcessingOptions:
    """Test cases for ClipProcessingOptions."""

    def test_default_options(self):
        """Test default processing options."""
        options = ClipProcessingOptions()
        assert options.target_resolution == "720p"
        assert options.target_fps == 30
        assert options.video_codec == "libx264"
        assert options.audio_codec == "aac"
        assert options.crf == 23
        assert options.audio_bitrate == "128k"
        assert options.maintain_aspect_ratio is True

    def test_custom_options(self):
        """Test custom processing options."""
        options = ClipProcessingOptions(
            target_resolution="1080p",
            target_fps=60,
            crf=18,
        )
        assert options.target_resolution == "1080p"
        assert options.target_fps == 60
        assert options.crf == 18

    def test_to_normalization_settings_720p(self):
        """Test conversion to NormalizationSettings for 720p."""
        options = ClipProcessingOptions(target_resolution="720p", target_fps=30)
        settings = options.to_normalization_settings()

        assert isinstance(settings, NormalizationSettings)
        assert settings.target_width == 1280
        assert settings.target_height == 720
        assert settings.target_fps == 30.0

    def test_to_normalization_settings_1080p(self):
        """Test conversion to NormalizationSettings for 1080p."""
        options = ClipProcessingOptions(target_resolution="1080p")
        settings = options.to_normalization_settings()

        assert settings.target_width == 1920
        assert settings.target_height == 1080

    def test_to_normalization_settings_4k(self):
        """Test conversion to NormalizationSettings for 4K."""
        options = ClipProcessingOptions(target_resolution="4k")
        settings = options.to_normalization_settings()

        assert settings.target_width == 3840
        assert settings.target_height == 2160

    def test_to_normalization_settings_preserve_aspect_ratio(self):
        """Test aspect ratio preservation in normalization settings."""
        options = ClipProcessingOptions(maintain_aspect_ratio=True)
        settings = options.to_normalization_settings()
        assert settings.preserve_aspect_ratio is True
        assert settings.scale_mode == "fit"

        options = ClipProcessingOptions(maintain_aspect_ratio=False)
        settings = options.to_normalization_settings()
        assert settings.preserve_aspect_ratio is False
        assert settings.scale_mode == "force"


class TestClipProcessor:
    """Test cases for ClipProcessor."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for testing."""
        return tmp_path / "clip_processor"

    @pytest.fixture
    def processor(self, temp_dir):
        """Create ClipProcessor instance for testing."""
        with patch("services.clip_processor.get_settings") as mock_settings:
            mock_settings.return_value.temp_dir = str(temp_dir)
            mock_settings.return_value.ffmpeg_path = "ffmpeg"
            mock_settings.return_value.ffprobe_path = "ffprobe"

            return ClipProcessor(temp_dir=temp_dir)

    def test_processor_initialization(self, processor, temp_dir):
        """Test processor initializes correctly."""
        assert processor.temp_dir == temp_dir
        assert processor.temp_dir.exists()
        assert processor.cache_dir.exists()
        assert processor.normalizer is not None

    def test_validate_format_supported(self, processor):
        """Test validation of supported formats."""
        for fmt in ClipFormat:
            test_path = Path(f"test.{fmt.value}")
            assert processor.validate_format(test_path) is True

    def test_validate_format_unsupported(self, processor):
        """Test validation rejects unsupported formats."""
        unsupported_formats = ["flv", "wmv", "3gp", "vob"]

        for fmt in unsupported_formats:
            test_path = Path(f"test.{fmt}")
            with pytest.raises(UnsupportedFormatError, match=f"Unsupported format: {fmt}"):
                processor.validate_format(test_path)

    def test_validate_format_case_insensitive(self, processor):
        """Test format validation is case insensitive."""
        test_paths = [
            Path("test.MP4"),
            Path("test.Mp4"),
            Path("test.MOV"),
        ]

        for path in test_paths:
            assert processor.validate_format(path) is True

    @patch("services.clip_processor.VideoNormalizer")
    def test_process_clip_success(self, mock_normalizer_class, processor):
        """Test successful clip processing."""
        # Mock normalizer
        mock_normalizer = MagicMock()
        mock_normalizer_class.return_value = mock_normalizer

        # Mock normalization result
        mock_result = NormalizationResult(
            output_path=Path("/tmp/output.mp4"),
            was_cached=False,
            original_resolution="1920x1080",
            original_fps=24.0,
            processing_time=10.5,
            file_size=1024 * 1024 * 10,  # 10 MB
        )
        mock_normalizer.normalize_video.return_value = mock_result

        # Replace processor's normalizer with mock
        processor.normalizer = mock_normalizer

        # Process clip
        input_path = Path("/tmp/input.mp4")
        result = processor.process_clip(input_path=input_path)

        assert result.success is True
        assert result.output_path == Path("/tmp/output.mp4")
        assert result.original_resolution == "1920x1080"
        assert result.original_fps == 24.0
        assert result.file_size == 1024 * 1024 * 10

    @patch("services.clip_processor.VideoNormalizer")
    def test_process_clip_with_options(self, mock_normalizer_class, processor):
        """Test clip processing with custom options."""
        mock_normalizer = MagicMock()
        mock_normalizer_class.return_value = mock_normalizer
        processor.normalizer = mock_normalizer

        mock_result = NormalizationResult(
            output_path=Path("/tmp/output.mp4"),
            was_cached=False,
        )
        mock_normalizer.normalize_video.return_value = mock_result

        # Custom options
        options = ClipProcessingOptions(
            target_resolution="1080p",
            target_fps=60,
            crf=18,
        )

        input_path = Path("/tmp/input.mp4")
        result = processor.process_clip(input_path=input_path, options=options)

        assert result.success is True

        # Verify normalizer was called with correct settings
        mock_normalizer.normalize_video.assert_called_once()
        call_args = mock_normalizer.normalize_video.call_args
        settings = call_args.kwargs["settings"]

        assert settings.target_width == 1920
        assert settings.target_height == 1080
        assert settings.target_fps == 60.0

    def test_process_clip_unsupported_format(self, processor):
        """Test processing fails for unsupported format."""
        input_path = Path("/tmp/input.flv")
        result = processor.process_clip(input_path=input_path)

        assert result.success is False
        assert "Unsupported format" in result.error

    @patch("services.clip_processor.VideoNormalizer")
    def test_process_clip_with_progress_callback(self, mock_normalizer_class, processor):
        """Test progress callback is called during processing."""
        mock_normalizer = MagicMock()
        mock_normalizer_class.return_value = mock_normalizer
        processor.normalizer = mock_normalizer

        mock_result = NormalizationResult(
            output_path=Path("/tmp/output.mp4"),
            was_cached=False,
        )
        mock_normalizer.normalize_video.return_value = mock_result

        # Progress callback
        progress_calls = []

        def progress_callback(status, progress):
            progress_calls.append({"status": status, "progress": progress})

        input_path = Path("/tmp/input.mp4")
        result = processor.process_clip(
            input_path=input_path,
            progress_callback=progress_callback,
        )

        assert result.success is True
        assert len(progress_calls) >= 2  # At least start and end

        # Check processing started
        assert any(call["status"] == ProcessingStatus.PROCESSING for call in progress_calls)

        # Check completion
        assert any(call["status"] == ProcessingStatus.COMPLETED for call in progress_calls)

    @patch("services.clip_processor.VideoNormalizer")
    def test_process_clip_failure_calls_progress_callback(self, mock_normalizer_class, processor):
        """Test progress callback is called on failure."""
        mock_normalizer = MagicMock()
        mock_normalizer_class.return_value = mock_normalizer
        processor.normalizer = mock_normalizer

        # Make normalizer raise exception
        mock_normalizer.normalize_video.side_effect = Exception("Processing failed")

        progress_calls = []

        def progress_callback(status, progress):
            progress_calls.append({"status": status, "progress": progress})

        input_path = Path("/tmp/input.mp4")
        result = processor.process_clip(
            input_path=input_path,
            progress_callback=progress_callback,
        )

        assert result.success is False
        assert "Processing failed" in result.error

        # Check failure status was reported
        assert any(call["status"] == ProcessingStatus.FAILED for call in progress_calls)

    @patch("services.clip_processor.VideoNormalizer")
    def test_process_from_url_success(self, mock_normalizer_class, processor, tmp_path):
        """Test processing from URL."""
        mock_normalizer = MagicMock()
        mock_normalizer_class.return_value = mock_normalizer
        processor.normalizer = mock_normalizer

        # Create a test input file
        input_file = tmp_path / "test_input.mp4"
        input_file.touch()

        mock_result = NormalizationResult(
            output_path=Path("/tmp/output.mp4"),
            was_cached=False,
        )
        mock_normalizer.normalize_video.return_value = mock_result

        # Process from "URL" (actually a file path for testing)
        result = processor.process_from_url(
            clip_url=str(input_file),
            clip_id="clip-123",
        )

        assert result.success is True

    def test_process_from_url_file_not_found(self, processor):
        """Test processing from URL fails if file doesn't exist."""
        result = processor.process_from_url(
            clip_url="/nonexistent/file.mp4",
            clip_id="clip-123",
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_cleanup_temp_files(self, processor, temp_dir):
        """Test cleanup of temporary files."""
        # Create some temp files
        old_file = temp_dir / "processed_old.mp4"
        old_file.touch()

        new_file = temp_dir / "processed_new.mp4"
        new_file.touch()

        # Set old file modification time to 25 hours ago
        import time

        old_time = time.time() - (25 * 3600)
        import os

        os.utime(old_file, (old_time, old_time))

        # Cleanup files older than 24 hours
        deleted = processor.cleanup_temp_files(older_than_hours=24)

        assert deleted >= 1
        assert not old_file.exists()
        assert new_file.exists()  # Should still exist

    def test_cleanup_temp_files_no_files(self, processor):
        """Test cleanup when no files exist."""
        deleted = processor.cleanup_temp_files()
        assert deleted == 0


class TestClipProcessingResult:
    """Test cases for ClipProcessingResult."""

    def test_successful_result(self):
        """Test creation of successful result."""
        result = ClipProcessingResult(
            success=True,
            output_path=Path("/tmp/output.mp4"),
            processing_time=10.5,
            file_size=1024 * 1024,
        )

        assert result.success is True
        assert result.output_path == Path("/tmp/output.mp4")
        assert result.error is None

    def test_failed_result(self):
        """Test creation of failed result."""
        result = ClipProcessingResult(
            success=False,
            error="Processing failed",
        )

        assert result.success is False
        assert result.error == "Processing failed"
        assert result.output_path is None
