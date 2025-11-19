"""
End-to-end tests for FFmpeg integration and video output validation.

These tests verify FFmpeg processing and validate the output video files.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest


class TestFFmpegOutputValidation:
    """E2E tests for validating FFmpeg output videos."""

    @pytest.fixture
    def create_test_video(self, tmp_path: Path) -> Path:
        """Create a test video file using FFmpeg.

        Creates a simple 5-second test video with color bars.
        """
        output_file = tmp_path / "test_video.mp4"

        # Create test video with FFmpeg (color test pattern)
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=5:size=1280x720:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=5",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-y",
            str(output_file),
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=30,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            pytest.skip(f"FFmpeg not available or failed to create test video: {e}")

        return output_file

    def test_ffmpeg_installed(self):
        """Verify FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            assert result.returncode == 0
            assert "ffmpeg version" in result.stdout.lower()

        except FileNotFoundError:
            pytest.skip("FFmpeg not installed")

    def test_ffprobe_installed(self):
        """Verify ffprobe is installed and accessible."""
        try:
            result = subprocess.run(
                ["ffprobe", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            assert result.returncode == 0
            assert "ffprobe version" in result.stdout.lower()

        except FileNotFoundError:
            pytest.skip("ffprobe not installed")

    def test_create_and_validate_test_video(self, create_test_video: Path):
        """Test creating and validating a test video file."""
        assert create_test_video.exists()
        assert create_test_video.stat().st_size > 0

        # Validate with ffprobe
        video_info = self._get_video_info(create_test_video)

        assert video_info is not None
        assert "streams" in video_info
        assert len(video_info["streams"]) >= 1  # At least video stream

        # Find video stream
        video_stream = None
        for stream in video_info["streams"]:
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        assert video_stream is not None
        assert video_stream["codec_name"] == "h264"
        assert video_stream["width"] == 1280
        assert video_stream["height"] == 720

    def test_concatenate_videos(self, tmp_path: Path):
        """Test concatenating multiple videos with FFmpeg."""
        # Create two test videos
        video1 = self._create_test_video(
            tmp_path / "video1.mp4",
            duration=3,
            color="red",
        )
        video2 = self._create_test_video(
            tmp_path / "video2.mp4",
            duration=3,
            color="blue",
        )

        # Create concat file
        concat_file = tmp_path / "concat.txt"
        concat_file.write_text(f"file '{video1}'\nfile '{video2}'\n")

        # Concatenate videos
        output = tmp_path / "concatenated.mp4"
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-y",
            str(output),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        except FileNotFoundError:
            pytest.skip("FFmpeg not available")

        # Validate output
        assert output.exists()

        video_info = self._get_video_info(output)
        video_stream = self._get_video_stream(video_info)

        # Duration should be approximately 6 seconds (3 + 3)
        duration = float(video_stream.get("duration", 0))
        assert 5.5 <= duration <= 6.5

    def test_add_text_overlay(self, tmp_path: Path):
        """Test adding text overlay to video."""
        # Create test video
        input_video = self._create_test_video(
            tmp_path / "input.mp4",
            duration=5,
        )

        # Add text overlay
        output = tmp_path / "with_overlay.mp4"
        cmd = [
            "ffmpeg",
            "-i",
            str(input_video),
            "-vf",
            "drawtext=text='Test Overlay':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:a",
            "copy",
            "-y",
            str(output),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        except FileNotFoundError:
            pytest.skip("FFmpeg not available")

        # Validate output
        assert output.exists()

        video_info = self._get_video_info(output)
        assert video_info is not None

    def test_mix_audio_tracks(self, tmp_path: Path):
        """Test mixing multiple audio tracks."""
        # Create video with audio
        video = self._create_test_video(
            tmp_path / "video.mp4",
            duration=5,
            audio_frequency=440,
        )

        # Create separate audio track
        audio = tmp_path / "music.mp3"
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:duration=5",
            "-c:a",
            "libmp3lame",
            "-y",
            str(audio),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        except FileNotFoundError:
            pytest.skip("FFmpeg not available")

        # Mix audio tracks
        output = tmp_path / "mixed.mp4"
        mix_cmd = [
            "ffmpeg",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=first[aout]",
            "-map",
            "0:v",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-y",
            str(output),
        ]

        subprocess.run(mix_cmd, check=True, capture_output=True, timeout=30)

        # Validate output has audio
        video_info = self._get_video_info(output)
        audio_stream = self._get_audio_stream(video_info)

        assert audio_stream is not None
        assert audio_stream["codec_type"] == "audio"

    def test_change_resolution(self, tmp_path: Path):
        """Test changing video resolution."""
        # Create 1280x720 video
        input_video = self._create_test_video(
            tmp_path / "hd.mp4",
            duration=3,
            width=1280,
            height=720,
        )

        # Scale to 640x360
        output = tmp_path / "sd.mp4"
        cmd = [
            "ffmpeg",
            "-i",
            str(input_video),
            "-vf",
            "scale=640:360",
            "-c:a",
            "copy",
            "-y",
            str(output),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        except FileNotFoundError:
            pytest.skip("FFmpeg not available")

        # Validate resolution changed
        video_info = self._get_video_info(output)
        video_stream = self._get_video_stream(video_info)

        assert video_stream["width"] == 640
        assert video_stream["height"] == 360

    def test_change_framerate(self, tmp_path: Path):
        """Test changing video frame rate."""
        # Create 30fps video
        input_video = self._create_test_video(
            tmp_path / "30fps.mp4",
            duration=3,
            fps=30,
        )

        # Change to 60fps
        output = tmp_path / "60fps.mp4"
        cmd = [
            "ffmpeg",
            "-i",
            str(input_video),
            "-r",
            "60",
            "-y",
            str(output),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        except FileNotFoundError:
            pytest.skip("FFmpeg not available")

        # Validate frame rate changed
        video_info = self._get_video_info(output)
        video_stream = self._get_video_stream(video_info)

        # Frame rate should be close to 60
        fps_str = video_stream.get("r_frame_rate", "0/1")
        numerator, denominator = map(int, fps_str.split("/"))
        fps = numerator / denominator if denominator != 0 else 0

        assert 59 <= fps <= 61

    # Helper methods

    def _create_test_video(
        self,
        output_path: Path,
        duration: int = 5,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        color: str = "testsrc",
        audio_frequency: int = 1000,
    ) -> Path:
        """Create a test video with specified parameters."""
        # Use color generator or test pattern
        if color in ["red", "blue", "green", "yellow"]:
            video_input = f"color=c={color}:s={width}x{height}:d={duration}:r={fps}"
        else:
            video_input = f"testsrc=duration={duration}:size={width}x{height}:rate={fps}"

        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            video_input,
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={audio_frequency}:duration={duration}",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            "-y",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        return output_path

    def _get_video_info(self, video_path: Path) -> dict[str, Any] | None:
        """Get video information using ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            return json.loads(result.stdout)

        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return None

    def _get_video_stream(self, video_info: dict[str, Any]) -> dict[str, Any] | None:
        """Extract video stream from ffprobe output."""
        if not video_info or "streams" not in video_info:
            return None

        for stream in video_info["streams"]:
            if stream.get("codec_type") == "video":
                return stream

        return None

    def _get_audio_stream(self, video_info: dict[str, Any]) -> dict[str, Any] | None:
        """Extract audio stream from ffprobe output."""
        if not video_info or "streams" not in video_info:
            return None

        for stream in video_info["streams"]:
            if stream.get("codec_type") == "audio":
                return stream

        return None


class TestRealWorkflowWithFFmpeg:
    """E2E tests using real FFmpeg for complete workflow."""

    @pytest.fixture
    def test_videos(self, tmp_path: Path) -> dict[str, Path]:
        """Create multiple test videos for composition testing."""
        videos = {}

        # Create 3 different test videos
        for i, color in enumerate(["red", "blue", "green"]):
            video_path = tmp_path / f"video_{color}.mp4"

            cmd = [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=1280x720:d=3:r=30",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={440 * (i + 1)}:duration=3",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-c:a",
                "aac",
                "-y",
                str(video_path),
            ]

            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                videos[color] = video_path
            except FileNotFoundError:
                pytest.skip("FFmpeg not available")

        return videos

    def test_complete_composition_workflow(
        self,
        test_videos: dict[str, Path],
        tmp_path: Path,
    ):
        """Test complete composition workflow with real FFmpeg.

        Steps:
        1. Create test input videos
        2. Concatenate them
        3. Add text overlay
        4. Add background music
        5. Validate output
        """
        # Step 1: Create concat file
        concat_file = tmp_path / "concat.txt"
        concat_lines = [f"file '{video}'\n" for video in test_videos.values()]
        concat_file.write_text("".join(concat_lines))

        # Step 2: Concatenate videos
        concatenated = tmp_path / "concatenated.mp4"
        concat_cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            "-y",
            str(concatenated),
        ]

        subprocess.run(concat_cmd, check=True, capture_output=True, timeout=30)

        # Step 3: Add text overlay
        with_overlay = tmp_path / "with_overlay.mp4"
        overlay_cmd = [
            "ffmpeg",
            "-i",
            str(concatenated),
            "-vf",
            "drawtext=text='Test Composition':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=50",
            "-c:a",
            "copy",
            "-y",
            str(with_overlay),
        ]

        subprocess.run(overlay_cmd, check=True, capture_output=True, timeout=30)

        # Step 4: Validate final output
        assert with_overlay.exists()
        assert with_overlay.stat().st_size > 0

        # Use ffprobe to verify
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            str(with_overlay),
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )

        video_info = json.loads(result.stdout)

        # Verify video has correct properties
        video_stream = None
        for stream in video_info["streams"]:
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        assert video_stream is not None
        assert video_stream["codec_name"] == "h264"
        assert video_stream["width"] == 1280
        assert video_stream["height"] == 720

        # Verify duration is approximately 9 seconds (3 videos × 3 seconds)
        duration = float(video_stream.get("duration", 0))
        assert 8.5 <= duration <= 9.5
