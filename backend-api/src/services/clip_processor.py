"""
Clip Processing Service for internal API.

This module provides clip processing functionality including normalization,
codec conversion, and format validation for clips submitted via internal API.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from app.config import get_settings

from services.ffmpeg.normalizer import NormalizationSettings, VideoNormalizer
from services.thumbnail_generator import ThumbnailGenerator

logger = logging.getLogger(__name__)


class ClipFormat(str, Enum):
    """Supported clip formats."""

    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"
    MKV = "mkv"
    WEBM = "webm"


class ProcessingStatus(str, Enum):
    """Status of clip processing."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ClipProcessingOptions:
    """Options for clip processing.

    Attributes:
        target_resolution: Target resolution (e.g., "720p", "1080p")
        target_fps: Target frame rate
        video_codec: Target video codec
        audio_codec: Target audio codec
        crf: Constant rate factor for video quality (0-51)
        video_bitrate: Video bitrate (e.g., "2M")
        audio_bitrate: Audio bitrate (e.g., "128k")
        maintain_aspect_ratio: Whether to maintain aspect ratio
    """

    target_resolution: str = "720p"
    target_fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 23
    video_bitrate: str | None = None
    audio_bitrate: str = "128k"
    maintain_aspect_ratio: bool = True

    def to_normalization_settings(self) -> NormalizationSettings:
        """Convert to NormalizationSettings for VideoNormalizer.

        Returns:
            NormalizationSettings compatible with VideoNormalizer
        """
        # Parse resolution
        resolution_map = {
            "480p": (854, 480),
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
        }

        width, height = resolution_map.get(self.target_resolution, (1280, 720))

        return NormalizationSettings(
            target_width=width,
            target_height=height,
            target_fps=float(self.target_fps),
            scale_mode="fit" if self.maintain_aspect_ratio else "force",
            preserve_aspect_ratio=self.maintain_aspect_ratio,
        )


@dataclass
class ClipProcessingResult:
    """Result of clip processing.

    Attributes:
        success: Whether processing succeeded
        output_path: Path to processed clip
        original_resolution: Original clip resolution
        original_fps: Original frame rate
        processing_time: Time taken to process (seconds)
        file_size: Size of processed file (bytes)
        thumbnails: Map of thumbnail size to path
        error: Error message if failed
    """

    success: bool
    output_path: Path | None = None
    original_resolution: str | None = None
    original_fps: float | None = None
    processing_time: float | None = None
    file_size: int | None = None
    thumbnails: dict[str, Path] | None = None
    error: str | None = None


class ClipProcessorError(Exception):
    """Exception raised for clip processing errors."""

    pass


class UnsupportedFormatError(ClipProcessorError):
    """Exception raised for unsupported clip formats."""

    pass


class ClipProcessor:
    """
    Service for processing video clips from internal API.

    Handles clip normalization, format conversion, and validation.
    """

    def __init__(
        self,
        temp_dir: str | Path | None = None,
        cache_dir: str | Path | None = None,
    ) -> None:
        """Initialize clip processor.

        Args:
            temp_dir: Temporary directory for processing
            cache_dir: Cache directory for normalized clips
        """
        settings = get_settings()

        self.temp_dir = Path(temp_dir or settings.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.cache_dir = Path(cache_dir or (self.temp_dir / "cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize video normalizer
        self.normalizer = VideoNormalizer(
            ffmpeg_path=settings.ffmpeg_path,
            ffprobe_path=settings.ffprobe_path,
            cache_dir=self.cache_dir,
            enable_cache=True,
        )

        # Initialize thumbnail generator
        self.thumbnail_generator = ThumbnailGenerator(
            ffmpeg_path=settings.ffmpeg_path,
            ffprobe_path=settings.ffprobe_path,
            output_dir=self.temp_dir / "thumbnails",
        )

        logger.info(
            "Initialized ClipProcessor",
            extra={
                "temp_dir": str(self.temp_dir),
                "cache_dir": str(self.cache_dir),
            },
        )

    def validate_format(self, file_path: Path) -> bool:
        """Validate that clip format is supported.

        Args:
            file_path: Path to clip file

        Returns:
            bool: True if format is supported

        Raises:
            UnsupportedFormatError: If format is not supported
        """
        extension = file_path.suffix.lstrip(".").lower()

        # Check against supported formats
        supported_formats = [fmt.value for fmt in ClipFormat]
        if extension not in supported_formats:
            raise UnsupportedFormatError(
                f"Unsupported format: {extension}. "
                f"Supported formats: {', '.join(supported_formats)}"
            )

        return True

    def process_clip(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        options: ClipProcessingOptions | None = None,
        progress_callback: Any = None,
    ) -> ClipProcessingResult:
        """Process a single clip with normalization and format conversion.

        Args:
            input_path: Path to input clip
            output_path: Path for output clip (optional)
            options: Processing options
            progress_callback: Callback function for progress updates

        Returns:
            ClipProcessingResult with processing details

        Raises:
            ClipProcessorError: If processing fails
            UnsupportedFormatError: If format is unsupported
        """
        import time

        start_time = time.time()
        input_path = Path(input_path)
        options = options or ClipProcessingOptions()

        logger.info(
            "Processing clip",
            extra={
                "input": str(input_path),
                "options": options,
            },
        )

        try:
            # Validate format
            self.validate_format(input_path)

            # Report progress if callback provided
            if progress_callback:
                progress_callback(status=ProcessingStatus.PROCESSING, progress=0)

            # Convert options to normalization settings
            settings = options.to_normalization_settings()

            # Process with VideoNormalizer
            result = self.normalizer.normalize_video(
                input_path=input_path,
                output_path=output_path,
                settings=settings,
                timeout=600,  # 10 minute timeout
            )

            # Generate thumbnails if requested
            thumbnails = {}
            if options and hasattr(options, "generate_thumbnails"):
                # Check if generate_thumbnails is set in options (from ProcessingOptions in internal.py)
                # For now, we'll generate thumbnails by default
                pass

            # Generate thumbnails from processed video
            try:
                thumbnail_results = self.thumbnail_generator.generate_multiple_thumbnails(
                    video_path=result.output_path,
                    timestamp=1.0,  # Default 1 second
                )

                # Map size names to paths
                thumbnails = {
                    size: thumb_result.path for size, thumb_result in thumbnail_results.items()
                }

                logger.info(
                    f"Generated {len(thumbnails)} thumbnails",
                    extra={"clip": str(result.output_path), "sizes": list(thumbnails.keys())},
                )

            except Exception as e:
                logger.warning(
                    f"Failed to generate thumbnails: {e}",
                    extra={"clip": str(result.output_path)},
                )
                # Continue without thumbnails

            processing_time = time.time() - start_time

            # Report completion
            if progress_callback:
                progress_callback(status=ProcessingStatus.COMPLETED, progress=100)

            logger.info(
                "Clip processing completed",
                extra={
                    "input": str(input_path),
                    "output": str(result.output_path),
                    "processing_time": round(processing_time, 2),
                },
            )

            return ClipProcessingResult(
                success=True,
                output_path=result.output_path,
                original_resolution=result.original_resolution,
                original_fps=result.original_fps,
                processing_time=processing_time,
                file_size=result.file_size,
                thumbnails=thumbnails if thumbnails else None,
            )

        except UnsupportedFormatError as e:
            logger.error(
                "Unsupported clip format",
                extra={"input": str(input_path), "error": str(e)},
            )
            if progress_callback:
                progress_callback(status=ProcessingStatus.FAILED, progress=0)

            return ClipProcessingResult(
                success=False,
                error=str(e),
            )

        except Exception as e:
            logger.exception(
                "Clip processing failed",
                extra={"input": str(input_path), "error": str(e)},
            )
            if progress_callback:
                progress_callback(status=ProcessingStatus.FAILED, progress=0)

            return ClipProcessingResult(
                success=False,
                error=f"Processing failed: {e!s}",
            )

    def process_from_url(
        self,
        clip_url: str,
        clip_id: str,
        options: ClipProcessingOptions | None = None,
        progress_callback: Any = None,
    ) -> ClipProcessingResult:
        """Download and process a clip from URL.

        Args:
            clip_url: URL of clip to download
            clip_id: Unique identifier for clip
            options: Processing options
            progress_callback: Callback for progress updates

        Returns:
            ClipProcessingResult with processing details

        Raises:
            ClipProcessorError: If download or processing fails
        """
        logger.info(
            "Processing clip from URL",
            extra={"clip_url": clip_url, "clip_id": clip_id},
        )

        try:
            # Report download progress
            if progress_callback:
                progress_callback(status=ProcessingStatus.DOWNLOADING, progress=0)

            # Download clip to temp directory
            # TODO: Implement actual download logic
            # For now, assume clip_url is a local path
            input_path = Path(clip_url)

            if not input_path.exists():
                raise ClipProcessorError(f"Clip file not found: {clip_url}")

            # Generate output path in temp directory
            output_filename = f"processed_{clip_id}.mp4"
            output_path = self.temp_dir / output_filename

            # Process the clip
            return self.process_clip(
                input_path=input_path,
                output_path=output_path,
                options=options,
                progress_callback=progress_callback,
            )

        except Exception as e:
            logger.exception(
                "Failed to process clip from URL",
                extra={"clip_url": clip_url, "clip_id": clip_id, "error": str(e)},
            )
            return ClipProcessingResult(
                success=False,
                error=f"Failed to download/process: {e!s}",
            )

    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Clean up temporary processing files.

        Args:
            older_than_hours: Delete files older than this many hours

        Returns:
            int: Number of files deleted
        """
        import time

        deleted_count = 0
        cutoff_time = time.time() - (older_than_hours * 3600)

        try:
            for temp_file in self.temp_dir.glob("processed_*"):
                if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_time:
                    temp_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted temp file: {temp_file}")

            logger.info(
                "Temp file cleanup completed",
                extra={"deleted_count": deleted_count, "older_than_hours": older_than_hours},
            )

        except Exception as e:
            logger.warning(f"Failed to clean up temp files: {e}")

        return deleted_count
