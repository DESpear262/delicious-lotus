"""Test endpoints for FFmpeg operations."""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["test"])


class ConcatRequest(BaseModel):
    """Request model for video concatenation."""

    video_urls: list[HttpUrl]


@router.post("/concat")
async def concat_videos(request: ConcatRequest) -> FileResponse:
    """Concatenate videos from URLs into a single MP4 file.

    Args:
        request: List of video URLs to concatenate

    Returns:
        FileResponse: Downloadable MP4 file

    Raises:
        HTTPException: If download or concatenation fails
    """
    if not request.video_urls:
        raise HTTPException(status_code=400, detail="At least one video URL is required")

    temp_dir = None
    output_file = None

    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="ffmpeg_concat_"))
        logger.info(f"Created temp directory: {temp_dir}")

        # Download all videos
        downloaded_files = []
        for i, url in enumerate(request.video_urls):
            video_path = temp_dir / f"video_{i}.mp4"
            logger.info(f"Downloading video {i + 1}/{len(request.video_urls)}: {url}")

            try:
                response = requests.get(str(url), stream=True, timeout=30)
                response.raise_for_status()

                with open(video_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                downloaded_files.append(video_path)
                logger.info(f"Downloaded: {video_path}")

            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")
                raise HTTPException(
                    status_code=400, detail=f"Failed to download video {i + 1}: {e!s}"
                )

        # Create concat file list for FFmpeg
        concat_list = temp_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for video_file in downloaded_files:
                f.write(f"file '{video_file.absolute()}'\n")

        # Output file
        output_file = temp_dir / "output.mp4"

        # Build FFmpeg command for concatenation
        # Using concat demuxer for fast concatenation without re-encoding
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",  # Copy streams without re-encoding (fast)
            str(output_file),
        ]

        logger.info(f"Running FFmpeg concat: {' '.join(cmd)}")

        # Execute FFmpeg with 1 minute timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Video concatenation failed: {result.stderr[:200]}",
            )

        if not output_file.exists():
            raise HTTPException(status_code=500, detail="Output file was not created")

        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        logger.info(f"Concatenation successful. Output: {output_file} ({file_size_mb:.2f} MB)")

        # Return file as downloadable response
        # We'll cleanup in the background after the file is sent
        async def cleanup_background():
            cleanup_temp_dir(temp_dir)

        return FileResponse(
            path=str(output_file),
            media_type="video/mp4",
            filename="concatenated.mp4",
            background=cleanup_background,
        )

    except subprocess.TimeoutExpired:
        logger.error("FFmpeg concatenation timed out after 60 seconds")
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=504, detail="Video concatenation timed out (60s limit)")

    except HTTPException:
        # Clean up on HTTP exceptions
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    except Exception as e:
        logger.exception(f"Unexpected error during concatenation: {e}")
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Concatenation failed: {e!s}")


def cleanup_temp_dir(temp_dir: Path) -> None:
    """Clean up temporary directory after file response is sent.

    Args:
        temp_dir: Path to temporary directory to remove
    """
    try:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to clean up temp directory {temp_dir}: {e}")
