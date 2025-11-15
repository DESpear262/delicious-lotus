"""
Tests for Input File Manager and FFprobe validation.

Tests media file probing, stream detection, validation, and error handling.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from services.ffmpeg.input_manager import (
    InputFileManager,
    MediaFileInfo,
    StreamInfo,
)


class TestStreamInfo:
    """Tests for StreamInfo dataclass."""

    def test_video_stream_creation(self):
        """Test creating a video stream."""
        stream = StreamInfo(
            index=0,
            codec_type="video",
            codec_name="h264",
            width=1920,
            height=1080,
            fps=30.0,
            duration=120.5,
            bit_rate=5000000,
        )

        assert stream.index == 0
        assert stream.codec_type == "video"
        assert stream.codec_name == "h264"
        assert stream.width == 1920
        assert stream.height == 1080
        assert stream.fps == 30.0
        assert stream.duration == 120.5
        assert stream.bit_rate == 5000000

    def test_audio_stream_creation(self):
        """Test creating an audio stream."""
        stream = StreamInfo(
            index=1,
            codec_type="audio",
            codec_name="aac",
            sample_rate=48000,
            channels=2,
            duration=120.5,
            bit_rate=128000,
        )

        assert stream.index == 1
        assert stream.codec_type == "audio"
        assert stream.codec_name == "aac"
        assert stream.sample_rate == 48000
        assert stream.channels == 2

    def test_is_video_property(self):
        """Test is_video property."""
        video_stream = StreamInfo(index=0, codec_type="video")
        audio_stream = StreamInfo(index=1, codec_type="audio")

        assert video_stream.is_video is True
        assert audio_stream.is_video is False

    def test_is_audio_property(self):
        """Test is_audio property."""
        video_stream = StreamInfo(index=0, codec_type="video")
        audio_stream = StreamInfo(index=1, codec_type="audio")

        assert video_stream.is_audio is False
        assert audio_stream.is_audio is True

    def test_is_subtitle_property(self):
        """Test is_subtitle property."""
        subtitle_stream = StreamInfo(index=2, codec_type="subtitle")
        video_stream = StreamInfo(index=0, codec_type="video")

        assert subtitle_stream.is_subtitle is True
        assert video_stream.is_subtitle is False

    def test_resolution_property(self):
        """Test resolution property."""
        stream = StreamInfo(
            index=0,
            codec_type="video",
            width=1920,
            height=1080,
        )

        assert stream.resolution == "1920x1080"

    def test_resolution_property_without_dimensions(self):
        """Test resolution property with missing dimensions."""
        stream = StreamInfo(index=0, codec_type="video")

        assert stream.resolution is None

    def test_video_stream_repr(self):
        """Test video stream string representation."""
        stream = StreamInfo(
            index=0,
            codec_type="video",
            codec_name="h264",
            width=1920,
            height=1080,
            fps=30.0,
        )

        repr_str = repr(stream)
        assert "VideoStream[0]" in repr_str
        assert "h264" in repr_str
        assert "1920x1080" in repr_str
        assert "30.0fps" in repr_str

    def test_audio_stream_repr(self):
        """Test audio stream string representation."""
        stream = StreamInfo(
            index=1,
            codec_type="audio",
            codec_name="aac",
            sample_rate=48000,
            channels=2,
        )

        repr_str = repr(stream)
        assert "AudioStream[1]" in repr_str
        assert "aac" in repr_str
        assert "48000Hz" in repr_str
        assert "2ch" in repr_str


class TestMediaFileInfo:
    """Tests for MediaFileInfo dataclass."""

    def test_media_file_creation(self):
        """Test creating a MediaFileInfo object."""
        streams = [
            StreamInfo(index=0, codec_type="video", codec_name="h264"),
            StreamInfo(index=1, codec_type="audio", codec_name="aac"),
        ]

        info = MediaFileInfo(
            path=Path("test.mp4"),
            format_name="mp4",
            duration=120.5,
            size=10485760,
            bit_rate=700000,
            streams=streams,
        )

        assert info.path == Path("test.mp4")
        assert info.format_name == "mp4"
        assert info.duration == 120.5
        assert info.size == 10485760
        assert info.bit_rate == 700000
        assert len(info.streams) == 2

    def test_media_file_post_init(self):
        """Test post_init initializes empty streams list."""
        info = MediaFileInfo(path=Path("test.mp4"))

        assert info.streams == []

    def test_video_streams_property(self):
        """Test video_streams property."""
        streams = [
            StreamInfo(index=0, codec_type="video", codec_name="h264"),
            StreamInfo(index=1, codec_type="audio", codec_name="aac"),
            StreamInfo(index=2, codec_type="video", codec_name="h264"),
        ]

        info = MediaFileInfo(path=Path("test.mp4"), streams=streams)
        video_streams = info.video_streams

        assert len(video_streams) == 2
        assert all(s.is_video for s in video_streams)

    def test_audio_streams_property(self):
        """Test audio_streams property."""
        streams = [
            StreamInfo(index=0, codec_type="video", codec_name="h264"),
            StreamInfo(index=1, codec_type="audio", codec_name="aac"),
            StreamInfo(index=2, codec_type="audio", codec_name="mp3"),
        ]

        info = MediaFileInfo(path=Path("test.mp4"), streams=streams)
        audio_streams = info.audio_streams

        assert len(audio_streams) == 2
        assert all(s.is_audio for s in audio_streams)

    def test_has_video_property(self):
        """Test has_video property."""
        video_only = MediaFileInfo(
            path=Path("test.mp4"),
            streams=[StreamInfo(index=0, codec_type="video")],
        )
        audio_only = MediaFileInfo(
            path=Path("test.mp3"),
            streams=[StreamInfo(index=0, codec_type="audio")],
        )

        assert video_only.has_video is True
        assert audio_only.has_video is False

    def test_has_audio_property(self):
        """Test has_audio property."""
        video_only = MediaFileInfo(
            path=Path("test.mp4"),
            streams=[StreamInfo(index=0, codec_type="video")],
        )
        audio_only = MediaFileInfo(
            path=Path("test.mp3"),
            streams=[StreamInfo(index=0, codec_type="audio")],
        )

        assert video_only.has_audio is False
        assert audio_only.has_audio is True

    def test_primary_video_stream(self):
        """Test primary_video_stream property."""
        streams = [
            StreamInfo(index=0, codec_type="video", codec_name="h264"),
            StreamInfo(index=1, codec_type="audio", codec_name="aac"),
            StreamInfo(index=2, codec_type="video", codec_name="h265"),
        ]

        info = MediaFileInfo(path=Path("test.mp4"), streams=streams)
        primary = info.primary_video_stream

        assert primary is not None
        assert primary.index == 0
        assert primary.codec_name == "h264"

    def test_primary_audio_stream(self):
        """Test primary_audio_stream property."""
        streams = [
            StreamInfo(index=0, codec_type="video", codec_name="h264"),
            StreamInfo(index=1, codec_type="audio", codec_name="aac"),
            StreamInfo(index=2, codec_type="audio", codec_name="mp3"),
        ]

        info = MediaFileInfo(path=Path("test.mp4"), streams=streams)
        primary = info.primary_audio_stream

        assert primary is not None
        assert primary.index == 1
        assert primary.codec_name == "aac"

    def test_primary_video_stream_none(self):
        """Test primary_video_stream returns None when no video."""
        info = MediaFileInfo(
            path=Path("test.mp3"),
            streams=[StreamInfo(index=0, codec_type="audio")],
        )

        assert info.primary_video_stream is None

    def test_primary_audio_stream_none(self):
        """Test primary_audio_stream returns None when no audio."""
        info = MediaFileInfo(
            path=Path("test.mp4"),
            streams=[StreamInfo(index=0, codec_type="video")],
        )

        assert info.primary_audio_stream is None

    def test_media_file_repr(self):
        """Test MediaFileInfo string representation."""
        streams = [
            StreamInfo(index=0, codec_type="video"),
            StreamInfo(index=1, codec_type="audio"),
        ]

        info = MediaFileInfo(
            path=Path("test.mp4"),
            format_name="mp4",
            duration=120.5,
            streams=streams,
        )

        repr_str = repr(info)
        assert "test.mp4" in repr_str
        assert "mp4" in repr_str
        assert "120.50s" in repr_str
        assert "1V" in repr_str
        assert "1A" in repr_str


class TestInputFileManager:
    """Tests for InputFileManager."""

    @pytest.fixture
    def manager(self) -> InputFileManager:
        """Create input file manager instance."""
        return InputFileManager(ffprobe_path="ffprobe")

    @pytest.fixture
    def mock_ffprobe_output(self) -> dict:
        """Create mock ffprobe JSON output."""
        return {
            "format": {
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "duration": "120.500000",
                "size": "10485760",
                "bit_rate": "698000",
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "duration": "120.500000",
                    "bit_rate": "600000",
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                    "duration": "120.500000",
                    "bit_rate": "98000",
                },
            ],
        }

    def test_initialization(self, manager):
        """Test InputFileManager initialization."""
        assert manager.ffprobe_path == "ffprobe"

    def test_initialization_custom_path(self):
        """Test initialization with custom ffprobe path."""
        manager = InputFileManager(ffprobe_path="/usr/local/bin/ffprobe")
        assert manager.ffprobe_path == "/usr/local/bin/ffprobe"

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_probe_file_success(self, mock_exists, mock_run, manager, mock_ffprobe_output):
        """Test successful file probing."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(
            stdout=json.dumps(mock_ffprobe_output),
            stderr="",
            returncode=0,
        )

        info = manager.probe_file("test.mp4")

        assert info.path == Path("test.mp4")
        assert info.format_name == "mov,mp4,m4a,3gp,3g2,mj2"
        assert info.duration == 120.5
        assert info.size == 10485760
        assert info.bit_rate == 698000
        assert len(info.streams) == 2
        assert info.has_video is True
        assert info.has_audio is True

    @patch("pathlib.Path.exists")
    def test_probe_file_not_found(self, mock_exists, manager):
        """Test probing non-existent file."""
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError, match="Media file not found"):
            manager.probe_file("nonexistent.mp4")

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_probe_file_ffprobe_error(self, mock_exists, mock_run, manager):
        """Test handling ffprobe execution error."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd="ffprobe",
            stderr="Error processing file",
        )

        with pytest.raises(ValueError, match="ffprobe failed"):
            manager.probe_file("test.mp4")

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_probe_file_timeout(self, mock_exists, mock_run, manager):
        """Test handling ffprobe timeout."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=30)

        with pytest.raises(ValueError, match="ffprobe timed out"):
            manager.probe_file("test.mp4")

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_probe_file_invalid_json(self, mock_exists, mock_run, manager):
        """Test handling invalid JSON output."""
        mock_exists.return_value = True
        mock_run.return_value = Mock(
            stdout="invalid json{{{",
            stderr="",
            returncode=0,
        )

        with pytest.raises(ValueError, match="Invalid ffprobe output"):
            manager.probe_file("test.mp4")

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_probe_file_video_only(self, mock_exists, mock_run, manager):
        """Test probing video-only file."""
        output = {
            "format": {"format_name": "mp4", "duration": "60.0"},
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1280,
                    "height": 720,
                    "r_frame_rate": "30/1",
                }
            ],
        }

        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout=json.dumps(output), returncode=0)

        info = manager.probe_file("test.mp4")

        assert info.has_video is True
        assert info.has_audio is False
        assert len(info.video_streams) == 1
        assert len(info.audio_streams) == 0

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_probe_file_audio_only(self, mock_exists, mock_run, manager):
        """Test probing audio-only file."""
        output = {
            "format": {"format_name": "mp3", "duration": "180.0"},
            "streams": [
                {
                    "index": 0,
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2,
                }
            ],
        }

        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout=json.dumps(output), returncode=0)

        info = manager.probe_file("test.mp3")

        assert info.has_video is False
        assert info.has_audio is True
        assert len(info.video_streams) == 0
        assert len(info.audio_streams) == 1

    def test_parse_stream_info_video(self, manager):
        """Test parsing video stream info."""
        stream_data = {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "r_frame_rate": "30/1",
            "duration": "120.5",
            "bit_rate": "5000000",
        }

        stream = manager._parse_stream_info(stream_data)

        assert stream is not None
        assert stream.index == 0
        assert stream.codec_type == "video"
        assert stream.codec_name == "h264"
        assert stream.width == 1920
        assert stream.height == 1080
        assert stream.fps == 30.0
        assert stream.duration == 120.5
        assert stream.bit_rate == 5000000

    def test_parse_stream_info_audio(self, manager):
        """Test parsing audio stream info."""
        stream_data = {
            "index": 1,
            "codec_type": "audio",
            "codec_name": "aac",
            "sample_rate": "48000",
            "channels": 2,
            "duration": "120.5",
            "bit_rate": "128000",
        }

        stream = manager._parse_stream_info(stream_data)

        assert stream is not None
        assert stream.index == 1
        assert stream.codec_type == "audio"
        assert stream.codec_name == "aac"
        assert stream.sample_rate == 48000
        assert stream.channels == 2

    def test_parse_stream_info_fractional_fps(self, manager):
        """Test parsing stream with fractional frame rate."""
        stream_data = {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "r_frame_rate": "30000/1001",  # 29.97 fps
        }

        stream = manager._parse_stream_info(stream_data)

        assert stream is not None
        assert stream.fps is not None
        assert 29.9 < stream.fps < 30.0

    def test_parse_stream_info_invalid_fps(self, manager):
        """Test parsing stream with invalid frame rate."""
        stream_data = {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "r_frame_rate": "0/0",  # Invalid
        }

        stream = manager._parse_stream_info(stream_data)

        assert stream is not None
        assert stream.fps is None

    def test_parse_stream_info_missing_fields(self, manager):
        """Test parsing stream with missing fields."""
        stream_data = {
            "index": 0,
            "codec_type": "video",
            # Missing many fields
        }

        stream = manager._parse_stream_info(stream_data)

        assert stream is not None
        assert stream.index == 0
        assert stream.codec_type == "video"
        assert stream.codec_name is None
        assert stream.width is None

    @patch.object(InputFileManager, "probe_file")
    def test_validate_file_success(self, mock_probe, manager):
        """Test successful file validation."""
        mock_probe.return_value = MediaFileInfo(
            path=Path("test.mp4"),
            format_name="mp4",
            duration=120.0,
            streams=[
                StreamInfo(index=0, codec_type="video"),
                StreamInfo(index=1, codec_type="audio"),
            ],
        )

        is_valid, error = manager.validate_file("test.mp4")

        assert is_valid is True
        assert error is None

    @patch.object(InputFileManager, "probe_file")
    def test_validate_file_require_video(self, mock_probe, manager):
        """Test validation requiring video."""
        mock_probe.return_value = MediaFileInfo(
            path=Path("test.mp3"),
            streams=[StreamInfo(index=0, codec_type="audio")],
        )

        is_valid, error = manager.validate_file("test.mp3", require_video=True)

        assert is_valid is False
        assert "video stream" in error.lower()

    @patch.object(InputFileManager, "probe_file")
    def test_validate_file_require_audio(self, mock_probe, manager):
        """Test validation requiring audio."""
        mock_probe.return_value = MediaFileInfo(
            path=Path("test.mp4"),
            streams=[StreamInfo(index=0, codec_type="video")],
        )

        is_valid, error = manager.validate_file("test.mp4", require_audio=True)

        assert is_valid is False
        assert "audio stream" in error.lower()

    @patch.object(InputFileManager, "probe_file")
    def test_validate_file_max_duration(self, mock_probe, manager):
        """Test validation with max duration limit."""
        mock_probe.return_value = MediaFileInfo(
            path=Path("test.mp4"),
            duration=180.0,
            streams=[StreamInfo(index=0, codec_type="video")],
        )

        is_valid, error = manager.validate_file("test.mp4", max_duration=120.0)

        assert is_valid is False
        assert "duration" in error.lower()
        assert "exceeds" in error.lower()

    @patch.object(InputFileManager, "probe_file")
    def test_validate_file_allowed_formats(self, mock_probe, manager):
        """Test validation with allowed formats."""
        mock_probe.return_value = MediaFileInfo(
            path=Path("test.avi"),
            format_name="avi",
            streams=[StreamInfo(index=0, codec_type="video")],
        )

        is_valid, error = manager.validate_file("test.avi", allowed_formats=["mp4", "mov"])

        assert is_valid is False
        assert "format" in error.lower()

    @patch.object(InputFileManager, "probe_file")
    def test_validate_file_allowed_formats_success(self, mock_probe, manager):
        """Test validation passes with matching format."""
        mock_probe.return_value = MediaFileInfo(
            path=Path("test.mp4"),
            format_name="mov,mp4,m4a",
            streams=[StreamInfo(index=0, codec_type="video")],
        )

        is_valid, error = manager.validate_file("test.mp4", allowed_formats=["mp4", "mov"])

        assert is_valid is True
        assert error is None

    @patch.object(InputFileManager, "probe_file")
    def test_validate_file_probe_failure(self, mock_probe, manager):
        """Test validation handles probe failures."""
        mock_probe.side_effect = Exception("Probe failed")

        is_valid, error = manager.validate_file("test.mp4")

        assert is_valid is False
        assert "failed to probe" in error.lower()

    def test_get_stream_specifier_video(self, manager):
        """Test generating video stream specifier."""
        specifier = manager.get_stream_specifier(0, "v", 0)
        assert specifier == "[0:v]"

    def test_get_stream_specifier_audio(self, manager):
        """Test generating audio stream specifier."""
        specifier = manager.get_stream_specifier(1, "a", 0)
        assert specifier == "[1:a]"

    def test_get_stream_specifier_with_index(self, manager):
        """Test generating stream specifier with index."""
        specifier = manager.get_stream_specifier(2, "v", 1)
        assert specifier == "[2:v:1]"

    def test_get_stream_specifier_all_streams(self, manager):
        """Test generating specifier for all streams."""
        specifier = manager.get_stream_specifier(3, None, 0)
        assert specifier == "[3]"

    def test_get_stream_specifier_second_file(self, manager):
        """Test stream specifier for second input file."""
        specifier = manager.get_stream_specifier(1, "a")
        assert specifier == "[1:a]"


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    @pytest.fixture
    def manager(self) -> InputFileManager:
        """Create input file manager instance."""
        return InputFileManager()

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_validate_video_composition_inputs(self, mock_exists, mock_run, manager):
        """Test validating all inputs for video composition."""
        # Mock multiple valid video files
        mock_exists.return_value = True

        video_output = {
            "format": {"format_name": "mp4", "duration": "30.0"},
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1280,
                    "height": 720,
                    "r_frame_rate": "30/1",
                }
            ],
        }

        mock_run.return_value = Mock(stdout=json.dumps(video_output), returncode=0)

        # Validate multiple files
        files = ["clip1.mp4", "clip2.mp4", "clip3.mp4"]
        for file_path in files:
            is_valid, error = manager.validate_file(
                file_path,
                require_video=True,
                max_duration=60.0,
                allowed_formats=["mp4", "mov"],
            )
            assert is_valid is True
            assert error is None

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_detect_multiple_audio_tracks(self, mock_exists, mock_run, manager):
        """Test detecting file with multiple audio tracks."""
        output = {
            "format": {"format_name": "mp4", "duration": "120.0"},
            "streams": [
                {"index": 0, "codec_type": "video", "codec_name": "h264"},
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                },
                {
                    "index": 2,
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2,
                },
            ],
        }

        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout=json.dumps(output), returncode=0)

        info = manager.probe_file("multi_audio.mp4")

        assert len(info.audio_streams) == 2
        assert info.audio_streams[0].codec_name == "aac"
        assert info.audio_streams[1].codec_name == "mp3"

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_handle_high_fps_video(self, mock_exists, mock_run, manager):
        """Test handling high frame rate video."""
        output = {
            "format": {"format_name": "mp4"},
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "r_frame_rate": "120/1",
                }
            ],
        }

        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout=json.dumps(output), returncode=0)

        info = manager.probe_file("high_fps.mp4")
        video_stream = info.primary_video_stream

        assert video_stream is not None
        assert video_stream.fps == 120.0

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_handle_4k_video(self, mock_exists, mock_run, manager):
        """Test handling 4K resolution video."""
        output = {
            "format": {"format_name": "mp4"},
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 3840,
                    "height": 2160,
                }
            ],
        }

        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout=json.dumps(output), returncode=0)

        info = manager.probe_file("4k.mp4")
        video_stream = info.primary_video_stream

        assert video_stream is not None
        assert video_stream.width == 3840
        assert video_stream.height == 2160
        assert video_stream.resolution == "3840x2160"

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_validate_complete_composition_pipeline(self, mock_exists, mock_run, manager):
        """Test complete validation workflow for composition pipeline."""
        mock_exists.return_value = True

        # Mock video clip
        video_output = {
            "format": {"format_name": "mp4", "duration": "45.0"},
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                },
            ],
        }

        # Mock music track
        audio_output = {
            "format": {"format_name": "mp3", "duration": "180.0"},
            "streams": [
                {
                    "index": 0,
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2,
                }
            ],
        }

        # Validate video clips
        mock_run.return_value = Mock(stdout=json.dumps(video_output), returncode=0)
        for i in range(3):
            info = manager.probe_file(f"clip{i}.mp4")
            assert info.has_video is True
            assert info.has_audio is True
            assert info.primary_video_stream.fps == 30.0

        # Validate music track
        mock_run.return_value = Mock(stdout=json.dumps(audio_output), returncode=0)
        music_info = manager.probe_file("background_music.mp3")
        assert music_info.has_audio is True
        assert music_info.has_video is False
