"""Worker for creating videos from images with Ken Burns effects."""

import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import List, Optional
import random

from workers.s3_manager import s3_manager
from workers.temp_file_manager import TempFileManager
from workers.video_processor import extract_video_metadata, generate_thumbnail

logger = logging.getLogger(__name__)

def generate_ken_burns_video(
    image_urls: List[str],
    duration: float,
    temp_dir: Path,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Path:
    """
    Generate a video from images with Ken Burns effect.

    Args:
        image_urls: List of image URLs.
        duration: Total duration of the video.
        temp_dir: Temporary directory to store intermediate files.
        width: Optional target video width.
        height: Optional target video height.

    Returns:
        Path: Path to the generated video file.
    """
    output_video_path = temp_dir / f"final_video_{uuid.uuid4().hex[:8]}.mp4"

    # 1. Download images
    assets_to_download = [{"url": url, "id": f"img_{i}"} for i, url in enumerate(image_urls)]
    downloaded_images = s3_manager.download_assets(assets_to_download, temp_dir)
    
    # Sort images by index to maintain order
    sorted_image_paths = []
    for i in range(len(image_urls)):
        path = downloaded_images.get(f"img_{i}")
        if not path:
            raise ValueError(f"Failed to download image {i}")
        sorted_image_paths.append(path)
    
    # 2. Determine dimensions if not provided
    target_width = width
    target_height = height
    
    if not target_width or not target_height:
        try:
            # Use the first image to determine dimensions
            first_image_path = sorted_image_paths[0]
            
            # We can use extract_video_metadata which uses ffprobe
            # It works for images too as long as they have a video stream (most image formats do in ffprobe)
            metadata = extract_video_metadata(first_image_path)
            
            if not target_width:
                target_width = metadata.get("width", 1920)
                # Make sure it's even for libx264
                if target_width % 2 != 0: target_width -= 1
                
            if not target_height:
                target_height = metadata.get("height", 1080)
                # Make sure it's even for libx264
                if target_height % 2 != 0: target_height -= 1
                
            logger.info(f"Auto-detected dimensions from first image: {target_width}x{target_height}")
            
        except Exception as e:
            logger.warning(f"Failed to extract dimensions from first image, using defaults: {e}")
            target_width = target_width or 1920
            target_height = target_height or 1080

    # Ensure even dimensions for h264
    if target_width % 2 != 0: target_width -= 1
    if target_height % 2 != 0: target_height -= 1
    
    logger.info(f"Target dimensions: {target_width}x{target_height}")

    # 3. Process each image into a video segment
    segment_duration = duration / len(sorted_image_paths)
    segment_paths = []
    
    for i, img_path in enumerate(sorted_image_paths):
        segment_path = temp_dir / f"segment_{i}.mp4"
        
        # Determine random start and end zoom/pan parameters
        # We want smooth transitions.
        # Zoom range: 1.0 to 1.25 (keep it subtle)
        z_min, z_max = 1.0, 1.25
        
        # Randomly decide if zooming in or out
        if random.random() < 0.5:
            z_start, z_end = z_min, z_max
        else:
            z_start, z_end = z_max, z_min
            
        # Determine start and end center points (normalized 0.0 to 1.0)
        # We need to ensure the crop stays within the image bounds.
        # The crop size at zoom Z is (1/Z) of the image size.
        # The center (cx, cy) must be within [0.5/Z, 1.0 - 0.5/Z].
        
        def get_valid_center(zoom):
            margin = 0.5 / zoom
            min_c = margin
            max_c = 1.0 - margin
            # If min_c > max_c (shouldn't happen for Z >= 1), clamp to 0.5
            if min_c > max_c: return 0.5
            return random.uniform(min_c, max_c)

        cx_start = get_valid_center(z_start)
        cy_start = get_valid_center(z_start)
        
        cx_end = get_valid_center(z_end)
        cy_end = get_valid_center(z_end)
        
        # Standardize to target dimensions
        # Scale, Pad, Zoompan, Format
        # We use 25 fps
        num_frames = int(segment_duration * 25)
        
        # FFmpeg zoompan filter expressions
        # on is current frame (0 to num_frames-1)
        # We interpolate linearly.
        
        # Calculate per-frame increments (in the expression itself using 'on')
        # z = z_start + (z_end - z_start) * on / num_frames
        # cx = cx_start + (cx_end - cx_start) * on / num_frames
        # cy = cy_start + (cy_end - cy_start) * on / num_frames
        
        # x (top-left) = (cx * iw) - (iw / zoom / 2)
        # y (top-left) = (cy * ih) - (ih / zoom / 2)
        
        # We construct the expression strings. 
        # Note: We use 'duration' variable in zoompan which is num_frames (or close to it).
        # But safer to hardcode num_frames in the expression divisor to be sure.
        
        z_expr = f"{z_start}+({z_end - z_start})*on/{num_frames}"
        cx_expr = f"{cx_start}+({cx_end - cx_start})*on/{num_frames}"
        cy_expr = f"{cy_start}+({cy_end - cy_start})*on/{num_frames}"
        
        x_expr = f"({cx_expr})*iw-(iw/zoom/2)"
        y_expr = f"({cy_expr})*ih-(ih/zoom/2)"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf",
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,"
            f"scale=4*iw:4*ih,"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={num_frames}:s={target_width}x{target_height}:fps=25,"
            f"framerate=25",
            "-c:v", "libx264",
            "-t", str(segment_duration),
            "-pix_fmt", "yuv420p",
            str(segment_path)
        ]
        
        logger.info(f"Generating segment {i}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        segment_paths.append(segment_path)

    # 4. Concatenate segments
    concat_list_path = temp_dir / "concat_list.txt"
    with open(concat_list_path, "w") as f:
        for path in segment_paths:
            f.write(f"file '{path.name}'\n")
    
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(output_video_path)
    ]
    
    logger.info(f"Concatenating segments")
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, cwd=str(temp_dir))

    return output_video_path


def create_video_from_images_job(
    image_urls: List[str],
    duration: float,
    user_id: str,
    job_id: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> dict:
    """
    Job to create a video from a list of images using Ken Burns effect.

    Args:
        image_urls: List of image URLs.
        duration: Total duration of the video.
        user_id: User ID.
        job_id: Job ID.
        width: Optional target video width.
        height: Optional target video height.

    Returns:
        dict: Result with video URL and metadata.
    """
    logger.info(f"Starting Ken Burns video generation job {job_id} for user {user_id}")
    
    # Use TempFileManager as context manager for automatic cleanup
    with TempFileManager(job_id=job_id) as temp_mgr:
        temp_dir = temp_mgr.temp_dir
        
        try:
            output_video_path = generate_ken_burns_video(
                image_urls=image_urls,
                duration=duration,
                temp_dir=temp_dir,
                width=width,
                height=height,
            )

            # 5. Generate thumbnail & Extract metadata
            metadata, thumbnail_path = extract_video_metadata(output_video_path), None
            try:
                thumbnail_path = generate_thumbnail(output_video_path, temp_dir / "thumbnail.jpg")
            except Exception as e:
                logger.warning(f"Thumbnail generation failed: {e}")

            # 6. Upload to S3
            asset_id = str(uuid.uuid4())
            s3_key_video = f"media/{user_id}/{asset_id}/video.mp4"
            video_url = s3_manager.upload_file(
                output_video_path, 
                s3_key_video, 
                extra_args={"ContentType": "video/mp4"}
            )
            
            thumbnail_url = None
            if thumbnail_path:
                s3_key_thumb = f"media/{user_id}/{asset_id}/thumbnail.jpg"
                thumbnail_url = s3_manager.upload_file(
                    thumbnail_path, 
                    s3_key_thumb, 
                    extra_args={"ContentType": "image/jpeg"}
                )

            # 7. Return result
            result = {
                "asset_id": asset_id,
                "video_url": video_url,
                "thumbnail_url": thumbnail_url,
                "metadata": metadata,
                "status": "completed"
            }
            
            logger.info(f"Job {job_id} completed successfully", extra=result)
            return result

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr.decode() if e.stderr else str(e)}")
            raise RuntimeError(f"Video processing failed: {e}")
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            raise