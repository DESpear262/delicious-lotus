"""Video processing utilities using FFmpeg and FFprobe for metadata extraction and thumbnail generation."""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Exception raised when video processing fails."""

    pass


def extract_video_metadata(video_path: str | Path) -> dict[str, Any]:
    """Extract video metadata using FFprobe.

    Args:
        video_path: Path to video file

    Returns:
        dict: Video metadata including:
            - duration (float): Video duration in seconds
            - width (int): Video width in pixels
            - height (int): Video height in pixels
            - frame_rate (float): Frame rate (fps)
            - codec (str): Video codec name
            - bitrate (int): Bitrate in bits per second
            - format (str): Container format

    Raises:
        VideoProcessingError: If FFprobe fails or video is invalid
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise VideoProcessingError(f"Video file not found: {video_path}")

    try:
        # Use FFprobe to extract metadata in JSON format
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]

        logger.debug(f"Running FFprobe: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        probe_data = json.loads(result.stdout)

        # Find video stream
        video_stream = None
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if not video_stream:
            raise VideoProcessingError("No video stream found in file")

        # Extract format info
        format_info = probe_data.get("format", {})

        # Parse frame rate (can be in format "30/1" or "29.97")
        frame_rate_str = video_stream.get("r_frame_rate", "0/1")
        if "/" in frame_rate_str:
            num, denom = frame_rate_str.split("/")
            frame_rate = float(num) / float(denom) if float(denom) != 0 else 0
        else:
            frame_rate = float(frame_rate_str)

        # Build metadata dict
        metadata = {
            "duration": float(format_info.get("duration", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "frame_rate": round(frame_rate, 2),
            "codec": video_stream.get("codec_name", "unknown"),
            "bitrate": int(format_info.get("bit_rate", 0)),
            "format": format_info.get("format_name", "unknown"),
        }

        logger.info(
            f"Extracted video metadata from {video_path.name}",
            extra={
                "duration": metadata["duration"],
                "resolution": f"{metadata['width']}x{metadata['height']}",
                "codec": metadata["codec"],
            },
        )

        return metadata

    except subprocess.TimeoutExpired as e:
        logger.error(f"FFprobe timeout for {video_path}")
        raise VideoProcessingError(f"FFprobe timeout: {e}") from e
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe failed for {video_path}: {e.stderr}")
        raise VideoProcessingError(f"FFprobe failed: {e.stderr}") from e
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to parse FFprobe output: {e}")
        raise VideoProcessingError(f"Failed to parse video metadata: {e}") from e
    except Exception as e:
        logger.exception(f"Unexpected error extracting video metadata: {e}")
        raise VideoProcessingError(f"Unexpected error: {e}") from e


def generate_thumbnail(
    video_path: str | Path,
    output_path: str | Path,
    timestamp: float = 0.0,
    width: int = 320,
) -> Path:
    """Generate a thumbnail image from a video using FFmpeg.

    Args:
        video_path: Path to video file
        output_path: Path to save thumbnail image (should end in .jpg or .png)
        timestamp: Time in seconds to extract frame from (default: 0.0 for first frame)
        width: Thumbnail width in pixels (default: 320, height maintains aspect ratio)

    Returns:
        Path: Path to generated thumbnail

    Raises:
        VideoProcessingError: If FFmpeg fails or video is invalid
    """
    video_path = Path(video_path)
    output_path = Path(output_path)

    if not video_path.exists():
        raise VideoProcessingError(f"Video file not found: {video_path}")

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use FFmpeg to extract thumbnail frame
        # -ss: seek to timestamp
        # -i: input file
        # -vf: video filter (scale width, maintain aspect ratio)
        # -vframes 1: extract only 1 frame
        # -q:v 2: high quality JPEG (scale 2-31, lower is better)
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vf", f"scale={width}:-1",  # -1 maintains aspect ratio
            "-vframes", "1",
            "-q:v", "2",
            str(output_path),
        ]

        logger.debug(f"Running FFmpeg: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )

        if not output_path.exists():
            raise VideoProcessingError("FFmpeg did not generate thumbnail file")

        thumbnail_size = output_path.stat().st_size
        logger.info(
            f"Generated thumbnail for {video_path.name}",
            extra={
                "output_path": str(output_path),
                "size_bytes": thumbnail_size,
                "timestamp": timestamp,
                "width": width,
            },
        )

        return output_path

    except subprocess.TimeoutExpired as e:
        logger.error(f"FFmpeg timeout for {video_path}")
        raise VideoProcessingError(f"FFmpeg timeout: {e}") from e
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed for {video_path}: {e.stderr}")
        raise VideoProcessingError(f"FFmpeg failed: {e.stderr}") from e
    except Exception as e:
        logger.exception(f"Unexpected error generating thumbnail: {e}")
        raise VideoProcessingError(f"Unexpected error: {e}") from e


def process_video_file(
    video_path: str | Path,
    thumbnail_output_path: str | Path | None = None,
    thumbnail_width: int = 320,
) -> tuple[dict[str, Any], Path | None]:
    """Process video file: extract metadata and generate thumbnail.

    Convenience function that combines metadata extraction and thumbnail generation.

    Args:
        video_path: Path to video file
        thumbnail_output_path: Optional path to save thumbnail (auto-generated if None)
        thumbnail_width: Thumbnail width in pixels (default: 320)

    Returns:
        tuple: (metadata dict, thumbnail path or None)

    Raises:
        VideoProcessingError: If processing fails
    """
    video_path = Path(video_path)

    # Extract metadata
    metadata = extract_video_metadata(video_path)

    # Generate thumbnail
    thumbnail_path = None
    if thumbnail_output_path:
        thumbnail_output_path = Path(thumbnail_output_path)
    else:
        # Auto-generate thumbnail path in same directory
        thumbnail_output_path = video_path.parent / f"{video_path.stem}_thumb.jpg"

    try:
        thumbnail_path = generate_thumbnail(
            video_path=video_path,
            output_path=thumbnail_output_path,
            timestamp=0.0,  # First frame
            width=thumbnail_width,
        )
    except VideoProcessingError as e:
        logger.warning(f"Failed to generate thumbnail: {e}")
        # Continue without thumbnail - metadata is still valid

    return metadata, thumbnail_path


def check_ffmpeg_installed() -> tuple[bool, str]:
    """Check if FFmpeg and FFprobe are installed and accessible.

    Returns:
        tuple: (is_installed: bool, version_info: str)
    """
    try:
        # Check FFmpeg
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        ffmpeg_version = result.stdout.split("\n")[0]

        # Check FFprobe
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        ffprobe_version = result.stdout.split("\n")[0]

        version_info = f"FFmpeg: {ffmpeg_version}, FFprobe: {ffprobe_version}"
        logger.info("FFmpeg tools are available", extra={"version": version_info})

        return True, version_info

    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        error_msg = f"FFmpeg tools not found: {e}"
        logger.error(error_msg)
        return False, error_msg
