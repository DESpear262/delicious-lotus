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
    ) -> list[str]:
        """Build a simple FFmpeg command for concatenating videos.

        Args:
            input_files: List of input video file paths
            output_file: Output video file path
            resolution: Output resolution (WxH)
            fps: Output frame rate

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

        # Build filter complex for concatenation
        if len(input_files) > 1:
            # Scale and concatenate inputs
            filter_parts = []
            for i in range(len(input_files)):
                filter_parts.append(f"[{i}:v]scale={resolution},setsar=1,fps={fps}[v{i}]")

            concat_inputs = "".join([f"[v{i}][{i}:a]" for i in range(len(input_files))])
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
            # Single file - just scale
            cmd.extend(
                [
                    "-vf",
                    f"scale={resolution},setsar=1,fps={fps}",
                ]
            )

        # Output settings
        cmd.extend(
            [
                "-c:v",
                "libx264",  # H.264 codec
                "-preset",
                "medium",  # Encoding preset
                "-crf",
                "23",  # Constant Rate Factor (quality)
                "-c:a",
                "aac",  # AAC audio codec
                "-b:a",
                "192k",  # Audio bitrate
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
        # For now, use simple composition
        # TODO: Implement complex filter graphs based on composition_config
        logger.info(
            "Building complex composition (using simple mode for now)",
            extra={"config": composition_config, "input_count": len(input_files)},
        )

        return self.build_simple_composition(
            input_files=list(input_files.values()),
            output_file=output_file,
            resolution=resolution,
            fps=fps,
        )


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
