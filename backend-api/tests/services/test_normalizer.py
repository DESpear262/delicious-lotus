"""
Unit tests for Video Normalizer.

Tests the VideoNormalizer class with various normalization scenarios.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from services.ffmpeg.input_manager import MediaFileInfo, StreamInfo
from services.ffmpeg.normalizer import (
    NormalizationResult,
    NormalizationSettings,
    VideoNormalizer,
    VideoNormalizerError,
)


class TestNormalizationSettings:
    """Test cases for NormalizationSettings."""

    def test_default_settings(self):
        """Test default normalization settings."""
        settings = NormalizationSettings()

        assert settings.target_width == 1280
        assert settings.target_height == 720
        assert settings.target_fps == 30.0
        assert settings.scale_mode == "fit"
        assert settings.preserve_aspect_ratio is True
        assert settings.pad_color == "black"

    def test_custom_settings(self):
        """Test custom normalization settings."""
        settings = NormalizationSettings(
            target_width=1920,
            target_height=1080,
            target_fps=60.0,
            scale_mode="fill",
            preserve_aspect_ratio=False,
        )

        assert settings.target_width == 1920
        assert settings.target_height == 1080
        assert settings.target_fps == 60.0
        assert settings.scale_mode == "fill"
        assert settings.preserve_aspect_ratio is False

    def test_resolution_property(self):
        """Test resolution property returns formatted string."""
        settings = NormalizationSettings(target_width=1920, target_height=1080)

        assert settings.resolution == "1920x1080"

    def test_invalid_dimensions(self):
        """Test validation of invalid dimensions."""
        with pytest.raises(ValueError, match="dimensions must be positive"):
            NormalizationSettings(target_width=0, target_height=720)

        with pytest.raises(ValueError, match="dimensions must be positive"):
            NormalizationSettings(target_width=1280, target_height=-100)

    def test_invalid_fps(self):
        """Test validation of invalid FPS."""
        with pytest.raises(ValueError, match="FPS must be positive"):
            NormalizationSettings(target_fps=0)

        with pytest.raises(ValueError, match="FPS must be positive"):
            NormalizationSettings(target_fps=-30)

    def test_invalid_scale_mode(self):
        """Test validation of invalid scale mode."""
        with pytest.raises(ValueError, match="Scale mode must be"):
            NormalizationSettings(scale_mode="invalid")


class TestVideoNormalizer:
    """Test cases for VideoNormalizer."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_video_info(self):
        """Create mock video info."""
        video_stream = StreamInfo(
            index=0,
            codec_type="video",
            codec_name="h264",
            width=1920,
            height=1080,
            fps=24.0,
            duration=10.0,
        )

        audio_stream = StreamInfo(
            index=1,
            codec_type="audio",
            codec_name="aac",
            sample_rate=48000,
            channels=2,
        )

        return MediaFileInfo(
            path=Path("/tmp/test_video.mp4"),
            format_name="mp4",
            duration=10.0,
            size=1024000,
            bit_rate=800000,
            streams=[video_stream, audio_stream],
        )

    def test_normalizer_initialization(self, temp_dir):
        """Test normalizer initializes correctly."""
        normalizer = VideoNormalizer(
            ffmpeg_path="/usr/bin/ffmpeg",
            ffprobe_path="/usr/bin/ffprobe",
            cache_dir=temp_dir,
            enable_cache=True,
        )

        assert normalizer.ffmpeg_path == "/usr/bin/ffmpeg"
        assert normalizer.cache_dir == temp_dir
        assert normalizer.enable_cache is True
        assert temp_dir.exists()

    def test_normalizer_without_cache(self):
        """Test normalizer without cache directory."""
        normalizer = VideoNormalizer(enable_cache=False)

        assert normalizer.cache_dir is None
        assert normalizer.enable_cache is False

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_build_normalization_command_fit_mode(self, mock_run, mock_video_info):
        """Test building normalization command with fit mode."""
        normalizer = VideoNormalizer()
        settings = NormalizationSettings(
            target_width=1280,
            target_height=720,
            target_fps=30.0,
            scale_mode="fit",
            preserve_aspect_ratio=True,
        )

        cmd = normalizer._build_normalization_command(
            input_path=Path("/tmp/input.mp4"),
            output_path=Path("/tmp/output.mp4"),
            settings=settings,
            media_info=mock_video_info,
        )

        # Verify command structure
        assert "ffmpeg" in cmd[0]
        assert "-y" in cmd
        assert "-i" in cmd
        assert "/tmp/input.mp4" in cmd
        assert "-vf" in cmd

        # Find filter string
        vf_index = cmd.index("-vf")
        filter_string = cmd[vf_index + 1]

        # Verify filter contains scale, pad, fps, and setsar
        assert "scale=" in filter_string
        assert "pad=" in filter_string
        assert "fps=" in filter_string
        assert "setsar=1" in filter_string

        # Verify codec settings
        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-preset" in cmd
        assert "-crf" in cmd

        # Verify audio codec (since mock has audio)
        assert "-c:a" in cmd
        assert "aac" in cmd

        # Verify output path
        assert "/tmp/output.mp4" in cmd

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_build_normalization_command_fill_mode(self, mock_run, mock_video_info):
        """Test building normalization command with fill mode."""
        normalizer = VideoNormalizer()
        settings = NormalizationSettings(
            target_width=1280,
            target_height=720,
            scale_mode="fill",
            preserve_aspect_ratio=True,
        )

        cmd = normalizer._build_normalization_command(
            input_path=Path("/tmp/input.mp4"),
            output_path=Path("/tmp/output.mp4"),
            settings=settings,
            media_info=mock_video_info,
        )

        # Find filter string
        vf_index = cmd.index("-vf")
        filter_string = cmd[vf_index + 1]

        # Verify filter contains scale and crop (not pad)
        assert "scale=" in filter_string
        assert "crop=" in filter_string
        assert "pad=" not in filter_string

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_build_normalization_command_force_mode(self, mock_run, mock_video_info):
        """Test building normalization command with force mode."""
        normalizer = VideoNormalizer()
        settings = NormalizationSettings(
            target_width=1280,
            target_height=720,
            scale_mode="force",
            preserve_aspect_ratio=False,
        )

        cmd = normalizer._build_normalization_command(
            input_path=Path("/tmp/input.mp4"),
            output_path=Path("/tmp/output.mp4"),
            settings=settings,
            media_info=mock_video_info,
        )

        # Find filter string
        vf_index = cmd.index("-vf")
        filter_string = cmd[vf_index + 1]

        # Verify filter contains simple scale (no pad or crop)
        assert "scale=1280:720" in filter_string
        assert "pad=" not in filter_string
        assert "crop=" not in filter_string

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_build_normalization_command_no_audio(self, mock_run):
        """Test building normalization command for video without audio."""
        # Create video-only media info
        video_stream = StreamInfo(
            index=0,
            codec_type="video",
            codec_name="h264",
            width=1920,
            height=1080,
            fps=24.0,
        )

        video_only_info = MediaFileInfo(
            path=Path("/tmp/video_only.mp4"),
            format_name="mp4",
            duration=10.0,
            streams=[video_stream],
        )

        normalizer = VideoNormalizer()
        settings = NormalizationSettings()

        cmd = normalizer._build_normalization_command(
            input_path=Path("/tmp/input.mp4"),
            output_path=Path("/tmp/output.mp4"),
            settings=settings,
            media_info=video_only_info,
        )

        # Verify no audio flag
        assert "-an" in cmd
        assert "-c:a" not in cmd

    @patch("services.ffmpeg.normalizer.subprocess.run")
    @patch.object(VideoNormalizer, "_get_cached_path")
    def test_normalize_video_uses_cache(self, mock_get_cached, mock_run, temp_dir, mock_video_info):
        """Test that normalization uses cache when available."""
        # Create a fake cached file
        cached_file = temp_dir / "normalized_abc123.mp4"
        cached_file.write_text("fake video")

        mock_get_cached.return_value = cached_file

        normalizer = VideoNormalizer(cache_dir=temp_dir, enable_cache=True)

        # Mock probe_file to return our mock video info
        with patch.object(normalizer.input_manager, "probe_file", return_value=mock_video_info):
            # Create a temporary input file
            input_file = temp_dir / "input.mp4"
            input_file.write_text("fake input")

            result = normalizer.normalize_video(input_path=input_file)

            # Verify it used cache
            assert result.was_cached is True
            assert result.output_path == cached_file
            assert mock_run.call_count == 0  # Should not run FFmpeg

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_normalize_video_file_not_found(self, mock_run, temp_dir):
        """Test normalization fails when input file doesn't exist."""
        normalizer = VideoNormalizer(cache_dir=temp_dir)

        with pytest.raises(FileNotFoundError, match="Input video not found"):
            normalizer.normalize_video(input_path="/nonexistent/file.mp4")

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_normalize_video_no_video_stream(self, mock_run, temp_dir):
        """Test normalization fails when input has no video stream."""
        # Create audio-only media info
        audio_stream = StreamInfo(
            index=0,
            codec_type="audio",
            codec_name="aac",
            sample_rate=48000,
            channels=2,
        )

        audio_only_info = MediaFileInfo(
            path=Path("/tmp/audio_only.mp3"),
            format_name="mp3",
            duration=10.0,
            streams=[audio_stream],
        )

        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create a temporary input file
        input_file = temp_dir / "audio.mp3"
        input_file.write_text("fake audio")

        # Mock probe_file to return audio-only info
        with patch.object(normalizer.input_manager, "probe_file", return_value=audio_only_info):
            with pytest.raises(VideoNormalizerError, match="no video stream"):
                normalizer.normalize_video(input_path=input_file)

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_normalize_video_ffmpeg_timeout(self, mock_run, temp_dir, mock_video_info):
        """Test normalization handles FFmpeg timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=10)

        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create a temporary input file
        input_file = temp_dir / "input.mp4"
        input_file.write_text("fake video")

        # Mock probe_file
        with patch.object(normalizer.input_manager, "probe_file", return_value=mock_video_info):
            with pytest.raises(VideoNormalizerError, match="timed out"):
                normalizer.normalize_video(input_path=input_file, output_path=temp_dir / "out.mp4")

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_normalize_video_ffmpeg_failure(self, mock_run, temp_dir, mock_video_info):
        """Test normalization handles FFmpeg failure."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["ffmpeg"],
            stderr="FFmpeg error message",
        )

        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create a temporary input file
        input_file = temp_dir / "input.mp4"
        input_file.write_text("fake video")

        # Mock probe_file
        with patch.object(normalizer.input_manager, "probe_file", return_value=mock_video_info):
            with pytest.raises(VideoNormalizerError, match="FFmpeg normalization failed"):
                normalizer.normalize_video(input_path=input_file, output_path=temp_dir / "out.mp4")

    def test_get_cached_path_generates_unique_hash(self, temp_dir):
        """Test that cached path generation creates unique hashes."""
        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create two different input files
        input1 = temp_dir / "input1.mp4"
        input2 = temp_dir / "input2.mp4"
        input1.write_text("video 1")
        input2.write_text("video 2")

        settings = NormalizationSettings()

        path1 = normalizer._get_cached_path(input1, settings)
        path2 = normalizer._get_cached_path(input2, settings)

        # Paths should be different
        assert path1 != path2
        assert path1.parent == temp_dir
        assert path2.parent == temp_dir
        assert path1.name.startswith("normalized_")
        assert path2.name.startswith("normalized_")

    def test_get_cached_path_same_for_same_input(self, temp_dir):
        """Test that same input generates same cached path."""
        normalizer = VideoNormalizer(cache_dir=temp_dir)

        input_file = temp_dir / "input.mp4"
        input_file.write_text("video content")

        settings = NormalizationSettings()

        path1 = normalizer._get_cached_path(input_file, settings)
        path2 = normalizer._get_cached_path(input_file, settings)

        # Paths should be identical
        assert path1 == path2

    def test_clear_cache_deletes_all_files(self, temp_dir):
        """Test cache clearing deletes all normalized files."""
        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create fake cached files
        (temp_dir / "normalized_abc123.mp4").write_text("fake")
        (temp_dir / "normalized_def456.mp4").write_text("fake")
        (temp_dir / "other_file.txt").write_text("fake")  # Should not be deleted

        deleted = normalizer.clear_cache()

        assert deleted == 2
        assert not (temp_dir / "normalized_abc123.mp4").exists()
        assert not (temp_dir / "normalized_def456.mp4").exists()
        assert (temp_dir / "other_file.txt").exists()  # Other files preserved

    def test_clear_cache_with_age_filter(self, temp_dir):
        """Test cache clearing with age filter."""
        import time

        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create an old cached file
        old_file = temp_dir / "normalized_old.mp4"
        old_file.write_text("old")

        # Wait a moment then create a new file
        time.sleep(0.1)

        new_file = temp_dir / "normalized_new.mp4"
        new_file.write_text("new")

        # Clear only files older than 0 days (should delete nothing since both are recent)
        deleted = normalizer.clear_cache(older_than_days=1)

        assert deleted == 0
        assert old_file.exists()
        assert new_file.exists()

    @patch("services.ffmpeg.normalizer.subprocess.run")
    def test_batch_normalize_multiple_videos(self, mock_run, temp_dir, mock_video_info):
        """Test batch normalization of multiple videos."""
        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create fake input files
        input1 = temp_dir / "input1.mp4"
        input2 = temp_dir / "input2.mp4"
        input1.write_text("video 1")
        input2.write_text("video 2")

        # Mock subprocess to create output files
        def create_output(*args, **kwargs):
            # Extract output path from command
            cmd = args[0]
            output_path = Path(cmd[-1])
            output_path.write_text("normalized video")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output

        # Mock probe_file
        with patch.object(normalizer.input_manager, "probe_file", return_value=mock_video_info):
            output_dir = temp_dir / "output"
            results = normalizer.batch_normalize(
                input_paths=[input1, input2],
                output_dir=output_dir,
            )

            assert len(results) == 2
            assert all(isinstance(r, NormalizationResult) for r in results)
            assert mock_run.call_count == 2

    def test_batch_normalize_continues_on_error(self, temp_dir):
        """Test batch normalization continues when one file fails."""
        normalizer = VideoNormalizer(cache_dir=temp_dir)

        # Create one valid and one invalid file path
        valid_input = temp_dir / "valid.mp4"
        valid_input.write_text("video")
        invalid_input = temp_dir / "nonexistent.mp4"  # Doesn't exist

        # This should process valid file and skip invalid one
        results = normalizer.batch_normalize(
            input_paths=[valid_input, invalid_input],
            output_dir=temp_dir / "output",
        )

        # Should have fewer results than inputs due to error
        assert len(results) < 2
