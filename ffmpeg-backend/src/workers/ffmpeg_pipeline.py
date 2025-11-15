"""FFmpeg pipeline for video composition and processing."""

import logging
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FFmpegProgress:
    """FFmpeg progress information."""

    frame: int = 0
    fps: float = 0.0
    total_size_kb: int = 0
    time_seconds: float = 0.0
    bitrate_kbps: float = 0.0
    speed: float = 0.0
    progress_percent: float = 0.0


class FFmpegCommandBuilder:
    """Builds FFmpeg commands for video composition."""

    def __init__(self, output_format: str = "mp4") -> None:
        """Initialize FFmpeg command builder.

        Args:
            output_format: Output video format (mp4, mov, etc.)
        """
        self.output_format = output_format
        self.ffmpeg_path = settings.ffmpeg_path
        self.threads = settings.ffmpeg_threads

    def build_simple_composition(
        self,
        input_files: list[Path],
        output_file: Path,
        resolution: str = "1920x1080",
        fps: int = 30,
        composition_config: dict[str, Any] | None = None,
    ) -> list[str]:
        """Build a simple FFmpeg command for concatenating videos.

        Args:
            input_files: List of input video file paths
            output_file: Output video file path
            resolution: Output resolution (WxH)
            fps: Output frame rate
            composition_config: Optional composition configuration for trimming

        Returns:
            list[str]: FFmpeg command arguments
        """
        if not input_files:
            raise ValueError("No input files provided")

        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output file
            "-progress",
            "pipe:1",  # Progress output to stdout
            "-loglevel",
            "warning",  # Only show warnings/errors
        ]

        # Add input files
        for input_file in input_files:
            cmd.extend(["-i", str(input_file)])

        # Get asset timing information for trimming
        assets = composition_config.get("assets", []) if composition_config else []

        # Track whether output will have audio
        output_has_audio = False

        # Build filter complex for concatenation
        if len(input_files) > 1:
            # For multi-file, assume all have audio (current behavior)
            # TODO: Enhance this to check each file and handle mixed audio/no-audio
            output_has_audio = True

            # Scale, trim, and concatenate inputs
            filter_parts = []
            for i, asset in enumerate(assets[: len(input_files)]):
                start_time = asset.get("start_time", 0)
                end_time = asset.get("end_time")

                if start_time or end_time:
                    # Apply trim filter for video
                    trim_filter = f"[{i}:v]trim=start={start_time}"
                    if end_time:
                        duration = end_time - start_time
                        trim_filter += f":duration={duration}"
                    trim_filter += (
                        f",setpts=PTS-STARTPTS,scale={resolution},setsar=1,fps={fps}[v{i}]"
                    )
                    filter_parts.append(trim_filter)

                    # Apply trim filter for audio
                    audio_trim = f"[{i}:a]atrim=start={start_time}"
                    if end_time:
                        audio_trim += f":duration={duration}"
                    audio_trim += f",asetpts=PTS-STARTPTS[a{i}]"
                    filter_parts.append(audio_trim)
                else:
                    filter_parts.append(f"[{i}:v]scale={resolution},setsar=1,fps={fps}[v{i}]")
                    filter_parts.append(f"[{i}:a]acopy[a{i}]")

            concat_inputs = "".join([f"[v{i}][a{i}]" for i in range(len(input_files))])
            filter_parts.append(f"{concat_inputs}concat=n={len(input_files)}:v=1:a=1[outv][outa]")

            filter_complex = ";".join(filter_parts)

            cmd.extend(
                [
                    "-filter_complex",
                    filter_complex,
                    "-map",
                    "[outv]",
                    "-map",
                    "[outa]",
                ]
            )
        else:
            # Single file - scale and optionally trim
            asset = assets[0] if assets else {}
            start_time = asset.get("start_time", 0)
            end_time = asset.get("end_time")

            # Check if the input file has audio
            has_audio = self.has_audio_stream(input_files[0])
            output_has_audio = has_audio

            if start_time or end_time:
                # Apply trim filter for single file
                duration = end_time - start_time if end_time else None

                video_trim = f"[0:v]trim=start={start_time}"
                if duration:
                    video_trim += f":duration={duration}"
                video_trim += f",setpts=PTS-STARTPTS,scale={resolution},setsar=1,fps={fps}[v]"

                if has_audio:
                    # Video has audio - apply audio trim as well
                    audio_trim = f"[0:a]atrim=start={start_time}"
                    if duration:
                        audio_trim += f":duration={duration}"
                    audio_trim += ",asetpts=PTS-STARTPTS[a]"

                    filter_complex = f"{video_trim};{audio_trim}"

                    cmd.extend(
                        [
                            "-filter_complex",
                            filter_complex,
                            "-map",
                            "[v]",
                            "-map",
                            "[a]",
                        ]
                    )
                else:
                    # Video has no audio - only trim video
                    cmd.extend(
                        [
                            "-filter_complex",
                            video_trim,
                            "-map",
                            "[v]",
                        ]
                    )
            else:
                # Just scale
                cmd.extend(["-vf", f"scale={resolution},setsar=1,fps={fps}"])

        # Output settings
        cmd.extend(
            [
                "-c:v",
                "libx264",  # H.264 codec
                "-preset",
                "medium",  # Encoding preset
                "-crf",
                "23",  # Constant Rate Factor (quality)
            ]
        )

        # Only add audio codec settings if output has audio
        if output_has_audio:
            cmd.extend(
                [
                    "-c:a",
                    "aac",  # AAC audio codec
                    "-b:a",
                    "192k",  # Audio bitrate
                ]
            )

        cmd.extend(
            [
                "-movflags",
                "+faststart",  # Enable fast start for MP4
                "-threads",
                str(self.threads),
                str(output_file),
            ]
        )

        logger.info(
            "Built FFmpeg command",
            extra={
                "input_count": len(input_files),
                "output": str(output_file),
                "resolution": resolution,
                "fps": fps,
            },
        )

        return cmd

    def build_complex_composition(
        self,
        composition_config: dict[str, Any],
        input_files: dict[str, Path],
        output_file: Path,
        resolution: str = "1920x1080",
        fps: int = 30,
    ) -> list[str]:
        """Build a complex FFmpeg command based on composition configuration.

        Args:
            composition_config: Composition configuration with layout, effects, etc.
            input_files: Mapping of asset ID to file path
            output_file: Output video file path
            resolution: Output resolution (WxH)
            fps: Output frame rate

        Returns:
            list[str]: FFmpeg command arguments
        """
        # Separate video and audio-only assets
        assets = composition_config.get("assets", [])
        video_files = []
        audio_files = []

        for asset in assets:
            asset_id = asset.get("id")
            asset_type = asset.get("type", "video")

            if asset_id in input_files:
                if asset_type == "audio":
                    audio_files.append(input_files[asset_id])
                else:
                    video_files.append(input_files[asset_id])

        logger.info(
            "Building composition with separated assets",
            extra={
                "video_count": len(video_files),
                "audio_count": len(audio_files),
                "total_inputs": len(input_files),
            },
        )

        # If we have video files, process them
        if video_files:
            # If we have background audio, we'll mix it in
            if audio_files:
                return self._build_video_with_audio(
                    video_files=video_files,
                    audio_files=audio_files,
                    output_file=output_file,
                    resolution=resolution,
                    fps=fps,
                    composition_config=composition_config,
                )
            else:
                # Just video, no background audio
                return self.build_simple_composition(
                    input_files=video_files,
                    output_file=output_file,
                    resolution=resolution,
                    fps=fps,
                    composition_config=composition_config,
                )
        else:
            raise ValueError("No video assets found in composition")

    def _build_video_with_audio(
        self,
        video_files: list[Path],
        audio_files: list[Path],
        output_file: Path,
        resolution: str,
        fps: int,
        composition_config: dict[str, Any],
    ) -> list[str]:
        """Build FFmpeg command for video with background audio mixing.

        Args:
            video_files: List of video file paths
            audio_files: List of audio file paths (background music, etc.)
            output_file: Output file path
            resolution: Output resolution (WxH)
            fps: Output frame rate
            composition_config: Composition configuration with audio settings

        Returns:
            list[str]: FFmpeg command arguments
        """
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-progress",
            "pipe:1",  # Progress to stdout
            "-loglevel",
            "warning",  # Only show warnings/errors
        ]

        # Add all inputs (video files first, then audio files)
        all_inputs = video_files + audio_files
        for input_file in all_inputs:
            cmd.extend(["-i", str(input_file)])

        # Get audio settings
        audio_config = composition_config.get("audio", {})
        music_volume = audio_config.get("music_volume", 0.3)
        original_audio_volume = audio_config.get("original_audio_volume", 0.7)

        video_input_count = len(video_files)

        # Build filter complex
        filter_parts = []

        # Process video clips (concatenate if multiple)
        if video_input_count > 1:
            # Scale each video
            for i in range(video_input_count):
                filter_parts.append(f"[{i}:v]scale={resolution},setsar=1,fps={fps}[v{i}]")

            # Concatenate videos with their audio
            concat_inputs = "".join([f"[v{i}][{i}:a]" for i in range(video_input_count)])
            filter_parts.append(
                f"{concat_inputs}concat=n={video_input_count}:v=1:a=1[video_out][video_audio]"
            )
        else:
            # Single video - just scale
            filter_parts.append(f"[0:v]scale={resolution},setsar=1,fps={fps}[video_out]")
            filter_parts.append("[0:a]acopy[video_audio]")

        # Mix background audio with video audio
        # Adjust volumes and mix
        if audio_files:
            bg_audio_index = video_input_count  # First audio file after videos
            filter_parts.append(
                f"[video_audio]volume={original_audio_volume}[video_audio_adjusted]"
            )
            filter_parts.append(f"[{bg_audio_index}:a]volume={music_volume}[bg_audio_adjusted]")
            filter_parts.append(
                "[video_audio_adjusted][bg_audio_adjusted]amix=inputs=2:duration=first[audio_out]"
            )
        else:
            filter_parts.append(f"[video_audio]volume={original_audio_volume}[audio_out]")

        filter_complex = ";".join(filter_parts)

        cmd.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[video_out]",
                "-map",
                "[audio_out]",
            ]
        )

        # Output settings
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                "-threads",
                str(self.threads),
                str(output_file),
            ]
        )

        logger.info(
            "Built video+audio mixing command",
            extra={
                "video_count": len(video_files),
                "audio_count": len(audio_files),
                "music_volume": music_volume,
                "original_volume": original_audio_volume,
            },
        )

        return cmd

    def has_audio_stream(self, video_path: Path) -> bool:
        """Check if video file has an audio stream.

        Args:
            video_path: Path to video file

        Returns:
            bool: True if video has audio stream, False otherwise
        """
        try:
            cmd = [
                settings.ffprobe_path,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit
            )

            # If there's output and it contains "audio", the file has audio
            return "audio" in result.stdout.strip().lower()

        except Exception as e:
            logger.warning(f"Failed to check audio stream: {e}")
            return False  # Assume no audio on error


class FFmpegProgressParser:
    """Parses FFmpeg progress output."""

    # Regex patterns for FFmpeg progress output
    FRAME_PATTERN = re.compile(r"frame=\s*(\d+)")
    FPS_PATTERN = re.compile(r"fps=\s*([\d.]+)")
    SIZE_PATTERN = re.compile(r"size=\s*(\d+)kB")
    TIME_PATTERN = re.compile(r"time=\s*([\d:.]+)")
    BITRATE_PATTERN = re.compile(r"bitrate=\s*([\d.]+)kbits/s")
    SPEED_PATTERN = re.compile(r"speed=\s*([\d.]+)x")

    def __init__(self, duration_seconds: float = 0.0) -> None:
        """Initialize progress parser.

        Args:
            duration_seconds: Expected output duration for progress calculation
        """
        self.duration_seconds = duration_seconds

    def parse_line(self, line: str, current_progress: FFmpegProgress) -> FFmpegProgress:
        """Parse a line of FFmpeg output and update progress.

        Args:
            line: Line of FFmpeg output
            current_progress: Current progress state

        Returns:
            FFmpegProgress: Updated progress
        """
        # Extract frame number
        frame_match = self.FRAME_PATTERN.search(line)
        if frame_match:
            current_progress.frame = int(frame_match.group(1))

        # Extract FPS
        fps_match = self.FPS_PATTERN.search(line)
        if fps_match:
            current_progress.fps = float(fps_match.group(1))

        # Extract size
        size_match = self.SIZE_PATTERN.search(line)
        if size_match:
            current_progress.total_size_kb = int(size_match.group(1))

        # Extract time
        time_match = self.TIME_PATTERN.search(line)
        if time_match:
            time_str = time_match.group(1)
            current_progress.time_seconds = self._parse_time(time_str)

        # Extract bitrate
        bitrate_match = self.BITRATE_PATTERN.search(line)
        if bitrate_match:
            current_progress.bitrate_kbps = float(bitrate_match.group(1))

        # Extract speed
        speed_match = self.SPEED_PATTERN.search(line)
        if speed_match:
            current_progress.speed = float(speed_match.group(1))

        # Calculate progress percentage
        if self.duration_seconds > 0 and current_progress.time_seconds > 0:
            current_progress.progress_percent = min(
                100.0,
                (current_progress.time_seconds / self.duration_seconds) * 100.0,
            )

        return current_progress

    @staticmethod
    def _parse_time(time_str: str) -> float:
        """Parse FFmpeg time string (HH:MM:SS.ms) to seconds.

        Args:
            time_str: Time string in HH:MM:SS.ms format

        Returns:
            float: Time in seconds
        """
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            return float(time_str)
        except Exception:
            return 0.0


class FFmpegPipeline:
    """Manages FFmpeg pipeline execution."""

    def __init__(self, temp_dir: str | Path | None = None) -> None:
        """Initialize FFmpeg pipeline.

        Args:
            temp_dir: Temporary directory for processing files
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path(settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.process: subprocess.Popen | None = None
        self.command_builder = FFmpegCommandBuilder()

        logger.info(
            "Initialized FFmpegPipeline",
            extra={"temp_dir": str(self.temp_dir)},
        )

    def execute_composition(
        self,
        input_files: dict[str, Path],
        output_filename: str,
        composition_config: dict[str, Any],
        resolution: str = "1920x1080",
        fps: int = 30,
        progress_callback: Callable[[FFmpegProgress], None] | None = None,
        timeout: int | None = None,
    ) -> Path:
        """Execute FFmpeg composition pipeline with timeout support.

        Args:
            input_files: Mapping of asset ID to file path
            output_filename: Output filename
            composition_config: Composition configuration
            resolution: Output resolution
            fps: Output frame rate
            progress_callback: Optional callback for progress updates
            timeout: Optional timeout in seconds (default: settings.rq_default_timeout)

        Returns:
            Path: Path to output file

        Raises:
            RuntimeError: If FFmpeg execution fails
            TimeoutError: If FFmpeg execution exceeds timeout
        """
        from workers.retry_logic import JobTimeoutError

        output_file = self.temp_dir / output_filename
        timeout = timeout or settings.rq_default_timeout
        start_time = time.time()

        try:
            # Build FFmpeg command
            cmd = self.command_builder.build_complex_composition(
                composition_config=composition_config,
                input_files=input_files,
                output_file=output_file,
                resolution=resolution,
                fps=fps,
            )

            logger.info(
                "Starting FFmpeg execution",
                extra={
                    "command": " ".join(cmd[:5]) + " ...",  # Log first few args
                    "input_count": len(input_files),
                    "output": str(output_file),
                    "timeout": timeout,
                },
            )

            # Execute FFmpeg process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
            )

            # Monitor progress
            parser = FFmpegProgressParser()
            current_progress = FFmpegProgress()

            # Read stdout for progress with timeout checking
            if self.process.stdout:
                for line in self.process.stdout:
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        logger.error(
                            f"FFmpeg execution exceeded timeout of {timeout}s",
                            extra={"timeout": timeout, "elapsed": elapsed},
                        )

                        # Kill the process
                        self.process.kill()
                        self.process.wait(timeout=5)

                        raise JobTimeoutError(
                            f"FFmpeg execution exceeded timeout of {timeout} seconds"
                        )

                    line = line.strip()
                    if not line:
                        continue

                    # Parse progress
                    current_progress = parser.parse_line(line, current_progress)

                    # Call progress callback
                    if progress_callback:
                        progress_callback(current_progress)

            # Wait for completion with timeout
            elapsed = time.time() - start_time
            try:
                return_code = self.process.wait(timeout=max(10, timeout - elapsed))
            except subprocess.TimeoutExpired as timeout_err:
                logger.error("FFmpeg process timeout during wait")
                self.process.kill()
                self.process.wait(timeout=5)
                raise JobTimeoutError(
                    f"FFmpeg execution exceeded timeout of {timeout} seconds"
                ) from timeout_err

            if return_code != 0:
                # Read stderr for error messages
                stderr = self.process.stderr.read() if self.process.stderr else ""
                error_msg = f"FFmpeg failed with code {return_code}: {stderr}"

                logger.error(
                    "FFmpeg execution failed",
                    extra={
                        "return_code": return_code,
                        "stderr": stderr[:500],  # Truncate long errors
                    },
                )

                raise RuntimeError(error_msg)

            if not output_file.exists():
                raise RuntimeError(f"FFmpeg completed but output file not found: {output_file}")

            output_size = output_file.stat().st_size
            execution_time = time.time() - start_time

            logger.info(
                "FFmpeg execution completed successfully",
                extra={
                    "output": str(output_file),
                    "size_bytes": output_size,
                    "size_mb": round(output_size / (1024 * 1024), 2),
                    "execution_time": round(execution_time, 2),
                },
            )

            return output_file

        except Exception as e:
            logger.exception(
                "FFmpeg pipeline execution failed",
                extra={"error": str(e)},
            )
            raise

        finally:
            # Cleanup process
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except Exception as e:
                    logger.warning(f"Error terminating FFmpeg process: {e}")
                    try:
                        self.process.kill()
                    except Exception as kill_err:
                        logger.debug(f"Error killing process: {kill_err}")

    def cleanup_temp_files(self, preserve_output: bool = True) -> None:
        """Clean up temporary files created during processing.

        Args:
            preserve_output: Whether to preserve output files
        """
        try:
            if self.temp_dir.exists():
                for file in self.temp_dir.iterdir():
                    try:
                        if file.is_file():
                            # Skip output files if preserving
                            if preserve_output and file.suffix in {".mp4", ".mov", ".avi"}:
                                continue

                            file.unlink()
                            logger.debug(f"Deleted temp file: {file}")

                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file}: {e}")

                logger.info(f"Cleaned up temp directory: {self.temp_dir}")

        except Exception as e:
            logger.exception(f"Error cleaning temp files: {e}")

    def get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            float: Duration in seconds

        Raises:
            RuntimeError: If ffprobe fails
        """
        try:
            cmd = [
                settings.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            duration = float(result.stdout.strip())
            return duration

        except Exception as e:
            logger.exception(f"Failed to get video duration: {e}")
            raise RuntimeError(f"Failed to get video duration: {e}") from e
