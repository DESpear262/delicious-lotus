"""
Thumbnail Generation Service for video clips.

This module provides functionality to extract thumbnail images from video clips
using FFmpeg with support for multiple sizes and formats.
"""

import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.config import get_settings

from services.ffmpeg.input_manager import InputFileManager

logger = logging.getLogger(__name__)


class ThumbnailSize(str, Enum):
    """Standard thumbnail sizes."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ThumbnailFormat(str, Enum):
    """Supported thumbnail formats."""

    WEBP = "webp"
    JPEG = "jpeg"
    PNG = "png"


# Size mappings for thumbnails
THUMBNAIL_DIMENSIONS = {
    ThumbnailSize.SMALL: (320, 180),
    ThumbnailSize.MEDIUM: (640, 360),
    ThumbnailSize.LARGE: (1280, 720),
}


@dataclass
class ThumbnailMetadata:
    """Metadata for a generated thumbnail.

    Attributes:
        size: Thumbnail size name (small, medium, large)
        width: Width in pixels
        height: Height in pixels
        format: Image format
        file_size: File size in bytes
        timestamp: Video timestamp where frame was extracted (seconds)
        video_duration: Total video duration (seconds)
    """

    size: str
    width: int
    height: int
    format: str
    file_size: int
    timestamp: float
    video_duration: float | None = None


@dataclass
class ThumbnailResult:
    """Result of thumbnail generation.

    Attributes:
        path: Path to generated thumbnail
        metadata: Thumbnail metadata
        was_fallback: Whether fallback format was used
    """

    path: Path
    metadata: ThumbnailMetadata
    was_fallback: bool = False


class ThumbnailGeneratorError(Exception):
    """Exception raised for thumbnail generation errors."""

    pass


class ThumbnailGenerator:
    """
    Service for generating thumbnail images from video clips.

    Supports multiple thumbnail sizes, formats (WebP with JPEG fallback),
    and smart frame selection to avoid poor quality frames.
    """

    def __init__(
        self,
        ffmpeg_path: str | None = None,
        ffprobe_path: str | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        """Initialize thumbnail generator.

        Args:
            ffmpeg_path: Path to ffmpeg executable
            ffprobe_path: Path to ffprobe executable
            output_dir: Directory for thumbnail output
        """
        settings = get_settings()

        self.ffmpeg_path = ffmpeg_path or settings.ffmpeg_path
        self.ffprobe_path = ffprobe_path or settings.ffprobe_path
        self.input_manager = InputFileManager(ffprobe_path=self.ffprobe_path)

        # Setup output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(settings.temp_dir) / "thumbnails"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Initialized ThumbnailGenerator",
            extra={
                "ffmpeg_path": self.ffmpeg_path,
                "output_dir": str(self.output_dir),
            },
        )

    def generate_thumbnail(
        self,
        video_path: str | Path,
        output_path: str | Path | None = None,
        timestamp: float = 1.0,
        size: ThumbnailSize = ThumbnailSize.MEDIUM,
        format: ThumbnailFormat = ThumbnailFormat.WEBP,
        use_fallback: bool = True,
        timeout: int = 30,
    ) -> ThumbnailResult:
        """Generate a single thumbnail from video.

        Args:
            video_path: Path to video file
            output_path: Path for output thumbnail (optional)
            timestamp: Timestamp in seconds for frame extraction
            size: Thumbnail size
            format: Output format
            use_fallback: Whether to fallback to JPEG if WebP fails
            timeout: FFmpeg timeout in seconds

        Returns:
            ThumbnailResult with thumbnail details

        Raises:
            ThumbnailGeneratorError: If generation fails
            FileNotFoundError: If video file doesn't exist
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(
            "Generating thumbnail",
            extra={
                "video": str(video_path),
                "timestamp": timestamp,
                "size": size.value,
                "format": format.value,
            },
        )

        # Probe video to get duration
        try:
            media_info = self.input_manager.probe_file(video_path)
            video_duration = media_info.duration
        except Exception as e:
            logger.warning(f"Failed to probe video duration: {e}")
            video_duration = None

        # Validate timestamp
        if video_duration and timestamp > video_duration:
            logger.warning(
                f"Timestamp {timestamp}s exceeds video duration {video_duration}s, "
                f"using 1 second instead"
            )
            timestamp = min(1.0, video_duration - 0.1)

        # Adjust timestamp for smart frame selection
        adjusted_timestamp = self._select_smart_timestamp(video_path, timestamp, video_duration)

        # Get dimensions for size
        width, height = THUMBNAIL_DIMENSIONS[size]

        # Determine output path
        if output_path:
            output_path = Path(output_path)
        else:
            suffix = f".{format.value}"
            filename = f"{video_path.stem}_{size.value}_{int(timestamp)}s{suffix}"
            output_path = self.output_dir / filename

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to generate with requested format
        try:
            self._extract_frame(
                video_path=video_path,
                output_path=output_path,
                timestamp=adjusted_timestamp,
                width=width,
                height=height,
                format=format,
                timeout=timeout,
            )
            was_fallback = False

        except ThumbnailGeneratorError as e:
            if format == ThumbnailFormat.WEBP and use_fallback:
                logger.warning(
                    f"WebP generation failed, falling back to JPEG: {e}",
                    extra={"video": str(video_path)},
                )

                # Change output path to JPEG
                output_path = output_path.with_suffix(".jpeg")

                # Retry with JPEG
                self._extract_frame(
                    video_path=video_path,
                    output_path=output_path,
                    timestamp=adjusted_timestamp,
                    width=width,
                    height=height,
                    format=ThumbnailFormat.JPEG,
                    timeout=timeout,
                )
                was_fallback = True
                format = ThumbnailFormat.JPEG
            else:
                raise

        # Verify output file exists
        if not output_path.exists():
            raise ThumbnailGeneratorError(
                f"Thumbnail generation completed but file not found: {output_path}"
            )

        # Get file size
        file_size = output_path.stat().st_size

        metadata = ThumbnailMetadata(
            size=size.value,
            width=width,
            height=height,
            format=format.value,
            file_size=file_size,
            timestamp=adjusted_timestamp,
            video_duration=video_duration,
        )

        logger.info(
            "Thumbnail generated successfully",
            extra={
                "output": str(output_path),
                "size_kb": round(file_size / 1024, 2),
                "was_fallback": was_fallback,
            },
        )

        return ThumbnailResult(
            path=output_path,
            metadata=metadata,
            was_fallback=was_fallback,
        )

    def generate_multiple_thumbnails(
        self,
        video_path: str | Path,
        sizes: list[ThumbnailSize] | None = None,
        timestamp: float = 1.0,
        format: ThumbnailFormat = ThumbnailFormat.WEBP,
    ) -> dict[str, ThumbnailResult]:
        """Generate multiple thumbnail sizes from same video.

        Args:
            video_path: Path to video file
            sizes: List of thumbnail sizes (defaults to all)
            timestamp: Timestamp for frame extraction
            format: Output format

        Returns:
            dict: Map of size name to ThumbnailResult

        Raises:
            ThumbnailGeneratorError: If generation fails
        """
        if sizes is None:
            sizes = [ThumbnailSize.SMALL, ThumbnailSize.MEDIUM, ThumbnailSize.LARGE]

        results = {}

        for size in sizes:
            try:
                result = self.generate_thumbnail(
                    video_path=video_path,
                    timestamp=timestamp,
                    size=size,
                    format=format,
                )
                results[size.value] = result

            except Exception as e:
                logger.error(
                    f"Failed to generate {size.value} thumbnail",
                    extra={"video": str(video_path), "error": str(e)},
                )
                # Continue with other sizes

        logger.info(
            f"Generated {len(results)} thumbnails",
            extra={"video": str(video_path), "sizes": list(results.keys())},
        )

        return results

    def _extract_frame(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: float,
        width: int,
        height: int,
        format: ThumbnailFormat,
        timeout: int = 30,
    ) -> None:
        """Extract a single frame from video using FFmpeg.

        Args:
            video_path: Path to video file
            output_path: Path for output thumbnail
            timestamp: Timestamp in seconds
            width: Output width
            height: Output height
            format: Output format
            timeout: FFmpeg timeout

        Raises:
            ThumbnailGeneratorError: If extraction fails
        """
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-ss",
            str(timestamp),  # Seek to timestamp
            "-i",
            str(video_path),
            "-vframes",
            "1",  # Extract 1 frame
            "-vf",
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black",
        ]

        # Format-specific settings
        if format == ThumbnailFormat.WEBP:
            cmd.extend(
                [
                    "-c:v",
                    "libwebp",
                    "-quality",
                    "80",  # WebP quality
                    "-compression_level",
                    "6",  # Compression level (0-6)
                ]
            )
        elif format == ThumbnailFormat.JPEG:
            cmd.extend(
                [
                    "-q:v",
                    "2",  # JPEG quality (2-31, lower is better)
                ]
            )
        elif format == ThumbnailFormat.PNG:
            cmd.extend(
                [
                    "-compression_level",
                    "6",  # PNG compression
                ]
            )

        cmd.append(str(output_path))

        # Execute FFmpeg
        try:
            logger.debug(
                "Executing FFmpeg for thumbnail",
                extra={"command": " ".join(cmd[:10]) + " ..."},
            )

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
            )

            logger.debug("FFmpeg thumbnail extraction completed")

        except subprocess.TimeoutExpired as e:
            raise ThumbnailGeneratorError(
                f"Thumbnail extraction timed out after {timeout} seconds"
            ) from e

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr[:500] if e.stderr else "Unknown error"
            raise ThumbnailGeneratorError(f"FFmpeg failed: {error_msg}") from e

    def _select_smart_timestamp(
        self,
        video_path: Path,
        requested_timestamp: float,
        video_duration: float | None,
    ) -> float:
        """Select a smart timestamp to avoid black frames or transitions.

        This is a basic implementation. More advanced implementations could:
        - Analyze frame brightness to avoid black frames
        - Detect scene changes and avoid transitions
        - Use content-aware frame selection

        Args:
            video_path: Path to video file
            requested_timestamp: User-requested timestamp
            video_duration: Video duration in seconds

        Returns:
            float: Adjusted timestamp
        """
        # For now, just ensure timestamp is within valid range
        # and avoid the very first and last frames

        if video_duration is None:
            return requested_timestamp

        # Ensure timestamp is at least 0.5s into video
        min_timestamp = 0.5

        # Ensure timestamp is at least 0.5s before end
        max_timestamp = video_duration - 0.5

        adjusted = max(min_timestamp, min(requested_timestamp, max_timestamp))

        if adjusted != requested_timestamp:
            logger.debug(
                f"Adjusted timestamp from {requested_timestamp}s to {adjusted}s",
                extra={"video": str(video_path)},
            )

        return adjusted

    def cleanup_thumbnails(self, older_than_hours: int = 24) -> int:
        """Clean up old thumbnail files.

        Args:
            older_than_hours: Delete thumbnails older than this many hours

        Returns:
            int: Number of files deleted
        """
        import time

        deleted_count = 0
        cutoff_time = time.time() - (older_than_hours * 3600)

        try:
            for thumbnail_file in self.output_dir.glob("*"):
                if thumbnail_file.is_file() and thumbnail_file.stat().st_mtime < cutoff_time:
                    thumbnail_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted thumbnail: {thumbnail_file}")

            logger.info(
                "Thumbnail cleanup completed",
                extra={
                    "deleted_count": deleted_count,
                    "older_than_hours": older_than_hours,
                },
            )

        except Exception as e:
            logger.warning(f"Failed to clean up thumbnails: {e}")

        return deleted_count
