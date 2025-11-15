"""
Video Normalization Service for FFmpeg operations.

This module provides functionality to normalize input video clips to consistent
resolution (1280x720) and framerate (30fps) using FFmpeg filters.
"""

from __future__ import annotations

import hashlib
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from services.ffmpeg.input_manager import InputFileManager, MediaFileInfo
from services.ffmpeg.validator import FilterChainValidator

logger = logging.getLogger(__name__)


@dataclass
class NormalizationSettings:
    """Settings for video normalization.

    Attributes:
        target_width: Target video width in pixels
        target_height: Target video height in pixels
        target_fps: Target frame rate
        scale_mode: Scaling mode (force, fit, fill)
        preserve_aspect_ratio: Whether to preserve aspect ratio
        pad_color: Color for padding when preserving aspect ratio
    """

    target_width: int = 1280
    target_height: int = 720
    target_fps: float = 30.0
    scale_mode: str = "fit"  # force, fit, fill
    preserve_aspect_ratio: bool = True
    pad_color: str = "black"

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.target_width <= 0 or self.target_height <= 0:
            raise ValueError("Target dimensions must be positive")
        if self.target_fps <= 0:
            raise ValueError("Target FPS must be positive")
        if self.scale_mode not in {"force", "fit", "fill"}:
            raise ValueError("Scale mode must be 'force', 'fit', or 'fill'")

    @property
    def resolution(self) -> str:
        """Get resolution as WIDTHxHEIGHT string."""
        return f"{self.target_width}x{self.target_height}"


@dataclass
class NormalizationResult:
    """Result of video normalization operation.

    Attributes:
        output_path: Path to normalized video file
        was_cached: Whether result was retrieved from cache
        original_resolution: Original video resolution (WxH)
        original_fps: Original frame rate
        processing_time: Time taken to normalize (seconds)
        file_size: Size of normalized file in bytes
    """

    output_path: Path
    was_cached: bool = False
    original_resolution: str | None = None
    original_fps: float | None = None
    processing_time: float | None = None
    file_size: int | None = None


class VideoNormalizerError(Exception):
    """Exception raised for video normalization errors."""

    pass


class VideoNormalizer:
    """
    Service for normalizing video files to consistent resolution and framerate.

    This class provides video normalization functionality with caching support
    to avoid redundant processing of the same files.

    Example:
        >>> normalizer = VideoNormalizer(cache_dir="/tmp/normalized")
        >>> result = normalizer.normalize_video(
        ...     input_path="input.mp4",
        ...     output_path="output.mp4"
        ... )
        >>> print(f"Normalized to {result.output_path}")
    """

    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
        cache_dir: str | Path | None = None,
        enable_cache: bool = True,
    ) -> None:
        """
        Initialize the video normalizer.

        Args:
            ffmpeg_path: Path to ffmpeg executable
            ffprobe_path: Path to ffprobe executable
            cache_dir: Directory for caching normalized videos
            enable_cache: Whether to enable caching
        """
        self.ffmpeg_path = ffmpeg_path
        self.input_manager = InputFileManager(ffprobe_path=ffprobe_path)
        self.validator = FilterChainValidator()
        self.enable_cache = enable_cache

        # Setup cache directory
        self.cache_dir: Path | None
        if cache_dir:
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None

        logger.info(
            "Initialized VideoNormalizer",
            extra={
                "ffmpeg_path": ffmpeg_path,
                "cache_enabled": enable_cache,
                "cache_dir": str(self.cache_dir) if self.cache_dir else None,
            },
        )

    def normalize_video(  # noqa: C901
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        settings: NormalizationSettings | None = None,
        timeout: int = 600,
    ) -> NormalizationResult:
        """
        Normalize a video file to target resolution and framerate.

        Args:
            input_path: Path to input video file
            output_path: Path for output file (optional, will use cache if not provided)
            settings: Normalization settings (uses defaults if not provided)
            timeout: FFmpeg execution timeout in seconds

        Returns:
            NormalizationResult with normalization details

        Raises:
            VideoNormalizerError: If normalization fails
            FileNotFoundError: If input file doesn't exist
        """
        import time

        start_time = time.time()
        input_path = Path(input_path)
        settings = settings or NormalizationSettings()

        # Validate input file
        if not input_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")

        # Probe input file
        try:
            media_info = self.input_manager.probe_file(input_path)
        except Exception as e:
            raise VideoNormalizerError(f"Failed to probe input video: {e}") from e

        # Validate it has video
        if not media_info.has_video:
            raise VideoNormalizerError(f"Input file has no video stream: {input_path}")

        # Get original video properties
        video_stream = media_info.primary_video_stream
        if not video_stream:
            raise VideoNormalizerError(f"No video stream found in {input_path}")

        original_resolution = video_stream.resolution
        original_fps = video_stream.fps

        logger.info(
            "Normalizing video",
            extra={
                "input": str(input_path),
                "original_resolution": original_resolution,
                "original_fps": original_fps,
                "target_resolution": settings.resolution,
                "target_fps": settings.target_fps,
            },
        )

        # Check cache if enabled
        if self.enable_cache and self.cache_dir and not output_path:
            cached_path = self._get_cached_path(input_path, settings)
            if cached_path and cached_path.exists():
                logger.info(
                    "Using cached normalized video",
                    extra={"input": str(input_path), "cached": str(cached_path)},
                )
                return NormalizationResult(
                    output_path=cached_path,
                    was_cached=True,
                    original_resolution=original_resolution,
                    original_fps=original_fps,
                    file_size=cached_path.stat().st_size,
                )

        # Determine output path
        if output_path:
            output_path = Path(output_path)
        elif self.cache_dir:
            output_path = self._get_cached_path(input_path, settings)
        else:
            raise ValueError("Either output_path or cache_dir must be provided")

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build FFmpeg command
        cmd = self._build_normalization_command(
            input_path=input_path,
            output_path=output_path,
            settings=settings,
            media_info=media_info,
        )

        # Execute FFmpeg
        try:
            logger.debug(
                "Executing FFmpeg normalization",
                extra={"command": " ".join(cmd[:10]) + " ..."},
            )

            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
            )

            logger.debug("FFmpeg normalization completed", extra={"stderr": result.stderr[:500]})

        except subprocess.TimeoutExpired as e:
            logger.error(
                "FFmpeg normalization timed out",
                extra={"timeout": timeout, "input": str(input_path)},
            )
            raise VideoNormalizerError(f"Normalization timed out after {timeout} seconds") from e

        except subprocess.CalledProcessError as e:
            logger.error(
                "FFmpeg normalization failed",
                extra={
                    "return_code": e.returncode,
                    "stderr": e.stderr[:500] if e.stderr else None,
                },
            )
            raise VideoNormalizerError(f"FFmpeg normalization failed: {e.stderr}") from e

        # Verify output file exists
        if not output_path.exists():
            raise VideoNormalizerError(f"FFmpeg completed but output file not found: {output_path}")

        processing_time = time.time() - start_time
        file_size = output_path.stat().st_size

        logger.info(
            "Video normalization completed",
            extra={
                "input": str(input_path),
                "output": str(output_path),
                "processing_time": round(processing_time, 2),
                "file_size_mb": round(file_size / (1024 * 1024), 2),
            },
        )

        return NormalizationResult(
            output_path=output_path,
            was_cached=False,
            original_resolution=original_resolution,
            original_fps=original_fps,
            processing_time=processing_time,
            file_size=file_size,
        )

    def _build_normalization_command(
        self,
        input_path: Path,
        output_path: Path,
        settings: NormalizationSettings,
        media_info: MediaFileInfo,
    ) -> list[str]:
        """
        Build FFmpeg command for video normalization.

        Args:
            input_path: Input video path
            output_path: Output video path
            settings: Normalization settings
            media_info: Media file information from probe

        Returns:
            List of command arguments for FFmpeg
        """
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-i",
            str(input_path),
        ]

        # Build filter chain for video normalization
        filters = []

        # Scale filter with aspect ratio handling
        if settings.preserve_aspect_ratio and settings.scale_mode == "fit":
            # Scale to fit within bounds while preserving aspect ratio, then pad
            scale_filter = (
                f"scale=w={settings.target_width}:h={settings.target_height}:"
                f"force_original_aspect_ratio=decrease"
            )
            pad_filter = (
                f"pad={settings.target_width}:{settings.target_height}:"
                f"(ow-iw)/2:(oh-ih)/2:color={settings.pad_color}"
            )
            filters.append(scale_filter)
            filters.append(pad_filter)

        elif settings.preserve_aspect_ratio and settings.scale_mode == "fill":
            # Scale to fill bounds while preserving aspect ratio (may crop)
            scale_filter = (
                f"scale=w={settings.target_width}:h={settings.target_height}:"
                f"force_original_aspect_ratio=increase"
            )
            crop_filter = f"crop={settings.target_width}:{settings.target_height}"
            filters.append(scale_filter)
            filters.append(crop_filter)

        else:
            # Force exact dimensions (may distort)
            scale_filter = f"scale={settings.target_width}:{settings.target_height}"
            filters.append(scale_filter)

        # FPS filter
        fps_filter = f"fps={settings.target_fps}"
        filters.append(fps_filter)

        # Set SAR to 1:1 (square pixels)
        filters.append("setsar=1")

        # Combine filters
        filter_string = ",".join(filters)

        cmd.extend(["-vf", filter_string])

        # Video codec settings - use libx264 with fast preset for normalization
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "fast",  # Fast encoding for normalization
                "-crf",
                "23",  # Reasonable quality
            ]
        )

        # Audio handling - copy if exists, otherwise handle gracefully
        if media_info.has_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
        else:
            cmd.extend(["-an"])  # No audio

        # Output file
        cmd.append(str(output_path))

        logger.debug(
            "Built normalization command",
            extra={"filter_string": filter_string, "output": str(output_path)},
        )

        return cmd

    def _get_cached_path(
        self,
        input_path: Path,
        settings: NormalizationSettings,
    ) -> Path:
        """
        Generate cache path for normalized video.

        Uses content hash + settings hash to create unique cache key.

        Args:
            input_path: Input video path
            settings: Normalization settings

        Returns:
            Path to cached file
        """
        if not self.cache_dir:
            raise ValueError("Cache directory not configured")

        # Create hash from file path, size, and modification time
        # This is faster than hashing the entire file content
        file_stat = input_path.stat()
        file_key = f"{input_path}_{file_stat.st_size}_{file_stat.st_mtime}"

        # Add settings to hash
        settings_key = (
            f"{settings.target_width}x{settings.target_height}_"
            f"{settings.target_fps}fps_{settings.scale_mode}_"
            f"{settings.preserve_aspect_ratio}_{settings.pad_color}"
        )

        # Combine and hash
        cache_key = hashlib.sha256(f"{file_key}_{settings_key}".encode()).hexdigest()

        # Use first 16 chars of hash + original extension
        cache_filename = f"normalized_{cache_key[:16]}{input_path.suffix}"
        cache_path = self.cache_dir / cache_filename

        return cache_path

    def clear_cache(self, older_than_days: int | None = None) -> int:
        """
        Clear cached normalized videos.

        Args:
            older_than_days: Only delete files older than this many days
                           If None, delete all cache files

        Returns:
            Number of files deleted
        """
        if not self.cache_dir or not self.cache_dir.exists():
            return 0

        import time

        deleted_count = 0
        cutoff_time = None

        if older_than_days is not None:
            cutoff_time = time.time() - (older_than_days * 86400)

        for cache_file in self.cache_dir.glob("normalized_*"):
            try:
                if cache_file.is_file():
                    # Check age if specified
                    if cutoff_time is not None and cache_file.stat().st_mtime > cutoff_time:
                        continue

                    cache_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted cached file: {cache_file}")

            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

        logger.info(
            "Cache cleanup completed",
            extra={
                "deleted_count": deleted_count,
                "older_than_days": older_than_days,
            },
        )

        return deleted_count

    def batch_normalize(
        self,
        input_paths: list[str | Path],
        output_dir: str | Path | None = None,
        settings: NormalizationSettings | None = None,
        max_workers: int = 1,
    ) -> list[NormalizationResult]:
        """
        Normalize multiple videos in batch.

        Args:
            input_paths: List of input video paths
            output_dir: Directory for output files (uses cache if not provided)
            settings: Normalization settings
            max_workers: Number of parallel workers (currently only supports 1)

        Returns:
            List of NormalizationResult objects
        """
        results: list[NormalizationResult] = []
        settings = settings or NormalizationSettings()

        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        for input_path in input_paths:
            input_path = Path(input_path)

            try:
                # Determine output path
                output_path = None
                if output_dir:
                    output_path = Path(output_dir) / f"normalized_{input_path.name}"

                result = self.normalize_video(
                    input_path=input_path,
                    output_path=output_path,
                    settings=settings,
                )
                results.append(result)

            except Exception as e:
                logger.error(
                    "Failed to normalize video in batch",
                    extra={"input": str(input_path), "error": str(e)},
                )
                # Continue with other files
                continue

        logger.info(
            "Batch normalization completed",
            extra={
                "total": len(input_paths),
                "successful": len(results),
                "failed": len(input_paths) - len(results),
            },
        )

        return results
