"""Background job for importing videos from external URLs with metadata extraction and thumbnail generation."""

import hashlib
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from db.models.media import MediaAsset, MediaAssetStatus, MediaAssetType
from db.session import SessionLocal
from workers.s3_manager import s3_manager
from workers.video_processor import VideoProcessingError, process_video_file

logger = logging.getLogger(__name__)


def import_video_from_url_job(
    url: str,
    name: str,
    user_id: str,
    asset_id: str,
    metadata: dict | None = None,
) -> dict:
    """Background job to import video from URL with processing.

    This job:
    1. Downloads video from URL
    2. Extracts video metadata (duration, dimensions, codec, etc.)
    3. Generates thumbnail (first frame at 320px width)
    4. Uploads both video and thumbnail to S3
    5. Creates/updates MediaAsset in database

    Args:
        url: External URL to download video from
        name: Filename for the video
        user_id: User UUID string
        asset_id: MediaAsset UUID string
        metadata: Optional additional metadata dict

    Returns:
        dict: Result with asset_id, s3_url, thumbnail_url, status

    Raises:
        Exception: If processing fails
    """
    user_id_uuid = uuid.UUID(user_id)
    asset_id_uuid = uuid.UUID(asset_id)
    metadata = metadata or {}

    logger.info(
        "Starting video import job",
        extra={
            "asset_id": asset_id,
            "url": url,
            "video_name": name,
        },
    )

    temp_video_path = None
    temp_thumbnail_path = None
    db = None

    try:
        # Create database session
        db = SessionLocal()

        # Check if asset already exists (edge case - shouldn't happen but handle it)
        existing_asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id_uuid).first()

        if existing_asset:
            logger.warning(
                f"Asset {asset_id} already exists, will update after processing",
                extra={"asset_id": asset_id, "current_status": existing_asset.status}
            )

        # Step 1: Download video from URL
        logger.info(f"Downloading video from {url}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as temp_file:
            temp_video_path = Path(temp_file.name)

        # Download with httpx (sync client for worker job)
        with httpx.Client(timeout=300.0) as client:
            response = client.get(url)
            response.raise_for_status()

            # Calculate checksum while downloading
            hasher = hashlib.sha256()
            total_size = 0

            with open(temp_video_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    hasher.update(chunk)
                    total_size += len(chunk)

            checksum = hasher.hexdigest()

        logger.info(
            f"Downloaded video: {total_size} bytes",
            extra={"asset_id": asset_id, "size": total_size},
        )

        # Step 2: Extract video metadata and generate thumbnail
        logger.info("Processing video: extracting metadata and generating thumbnail")

        temp_thumbnail_path = temp_video_path.parent / f"{temp_video_path.stem}_thumb.jpg"

        try:
            video_metadata, thumbnail_path = process_video_file(
                video_path=temp_video_path,
                thumbnail_output_path=temp_thumbnail_path,
                thumbnail_width=320,
            )

            logger.info(
                "Video processing complete",
                extra={
                    "asset_id": asset_id,
                    "duration": video_metadata.get("duration"),
                    "resolution": f"{video_metadata.get('width')}x{video_metadata.get('height')}",
                    "has_thumbnail": thumbnail_path is not None,
                },
            )
        except VideoProcessingError as e:
            logger.error(f"Video processing failed: {e}")
            # Continue without metadata/thumbnail - still upload video
            video_metadata = {}
            thumbnail_path = None

        # Step 3: Upload video to S3
        logger.info("Uploading video to S3")

        s3_key = f"media/{user_id}/{asset_id}/{name}"
        s3_url = s3_manager.upload_file(
            local_path=temp_video_path,
            s3_key=s3_key,
            extra_args={"ContentType": "video/mp4", "ContentDisposition": "inline"},
        )

        logger.info(f"Video uploaded to S3: {s3_key}")

        # Step 4: Upload thumbnail to S3 (if generated)
        thumbnail_s3_key = None
        thumbnail_url = None

        if thumbnail_path and thumbnail_path.exists():
            logger.info("Uploading thumbnail to S3")

            thumbnail_s3_key = f"media/{user_id}/{asset_id}/thumbnail.jpg"
            thumbnail_url = s3_manager.upload_file(
                local_path=thumbnail_path,
                s3_key=thumbnail_s3_key,
                extra_args={"ContentType": "image/jpeg"},
            )

            logger.info(f"Thumbnail uploaded to S3: {thumbnail_s3_key}")

        # Step 5: Create or update MediaAsset record with ALL final data
        logger.info("Creating/updating MediaAsset record with complete data")

        # Merge video metadata with existing metadata
        final_metadata = {
            **metadata,
            **video_metadata,
            "source": "ai_generation",
            "source_url": url,
            "imported_at": datetime.utcnow().isoformat(),
        }

        # Prepare tags
        tags = metadata.get("tags", [])
        if "ai-generated" not in tags and (metadata.get("aiGenerated") or metadata.get("prompt")):
            tags.append("ai-generated")

        # Create or update asset with complete data in single transaction
        if existing_asset:
            # Update existing asset (edge case)
            logger.info(f"Updating existing asset {asset_id}")
            existing_asset.file_size = total_size
            existing_asset.s3_key = s3_key
            existing_asset.thumbnail_s3_key = thumbnail_s3_key
            existing_asset.checksum = checksum
            existing_asset.file_metadata = final_metadata
            existing_asset.status = MediaAssetStatus.READY
            existing_asset.updated_at = datetime.utcnow()
            if "ai-generated" not in existing_asset.tags:
                existing_asset.tags.extend(tags)
        else:
            # Create new asset with all final data (normal path)
            logger.info(f"Creating new asset {asset_id} with complete data")
            asset = MediaAsset(
                id=asset_id_uuid,
                user_id=user_id_uuid,
                name=name,
                file_size=total_size,  # ACTUAL size
                file_type=MediaAssetType.VIDEO,
                s3_key=s3_key,  # FINAL s3_key
                thumbnail_s3_key=thumbnail_s3_key,
                status=MediaAssetStatus.READY,  # Ready immediately!
                checksum=checksum,
                file_metadata=final_metadata,
                tags=tags,
                is_deleted=False,
            )
            db.add(asset)

        db.commit()

        logger.info(
            "Video import job completed successfully",
            extra={
                "asset_id": asset_id,
                "s3_url": s3_url,
                "thumbnail_url": thumbnail_url,
            },
        )

        return {
            "success": True,
            "asset_id": asset_id,
            "s3_url": s3_url,
            "thumbnail_url": thumbnail_url,
            "status": "ready",
            "metadata": final_metadata,
        }

    except Exception as e:
        logger.exception(
            f"Video import job failed: {e}",
            extra={"asset_id": asset_id, "url": url},
        )

        # Create asset with FAILED status if processing failed
        if db:
            try:
                failed_asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id_uuid).first()
                if failed_asset:
                    # Asset exists, update to FAILED
                    failed_asset.status = MediaAssetStatus.FAILED
                    failed_asset.file_metadata = {
                        **(failed_asset.file_metadata or {}),
                        "error": str(e),
                        "failed_at": datetime.utcnow().isoformat(),
                    }
                    failed_asset.updated_at = datetime.utcnow()
                    db.commit()
                else:
                    # Asset doesn't exist yet, create with FAILED status
                    # (This helps with debugging - we can see what failed)
                    failed_asset = MediaAsset(
                        id=asset_id_uuid,
                        user_id=user_id_uuid,
                        name=name,
                        file_size=0,
                        file_type=MediaAssetType.VIDEO,
                        s3_key="",
                        status=MediaAssetStatus.FAILED,
                        checksum="",
                        file_metadata={
                            **metadata,
                            "error": str(e),
                            "failed_at": datetime.utcnow().isoformat(),
                        },
                        tags=[],
                        is_deleted=False,
                    )
                    db.add(failed_asset)
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update asset status: {db_error}")

        raise

    finally:
        # Cleanup temporary files
        if temp_video_path and temp_video_path.exists():
            try:
                temp_video_path.unlink()
                logger.debug(f"Cleaned up temp video: {temp_video_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp video: {e}")

        if temp_thumbnail_path and temp_thumbnail_path.exists():
            try:
                temp_thumbnail_path.unlink()
                logger.debug(f"Cleaned up temp thumbnail: {temp_thumbnail_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp thumbnail: {e}")

        # Close database session
        if db:
            db.close()


def import_image_from_url_job(
    url: str,
    name: str,
    user_id: str,
    asset_id: str,
    metadata: dict | None = None,
) -> dict:
    """Background job to import image from URL (no processing needed).

    This job:
    1. Downloads image from URL
    2. Uploads to S3
    3. Creates/updates MediaAsset in database

    Args:
        url: External URL to download image from
        name: Filename for the image
        user_id: User UUID string
        asset_id: MediaAsset UUID string
        metadata: Optional additional metadata dict

    Returns:
        dict: Result with asset_id, s3_url, status

    Raises:
        Exception: If processing fails
    """
    user_id_uuid = uuid.UUID(user_id)
    asset_id_uuid = uuid.UUID(asset_id)
    metadata = metadata or {}

    logger.info(
        "Starting image import job",
        extra={
            "asset_id": asset_id,
            "url": url,
            "image_name": name,
        },
    )

    temp_image_path = None
    db = None

    try:
        # Download image first
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as temp_file:
            temp_image_path = Path(temp_file.name)

        logger.info("Downloading image from URL", extra={"url": url})

        with httpx.Client(timeout=120.0) as client:
            response = client.get(url)
            response.raise_for_status()

            hasher = hashlib.sha256()
            total_size = 0

            with open(temp_image_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    hasher.update(chunk)
                    total_size += len(chunk)

            checksum = hasher.hexdigest()

        logger.info("Image downloaded", extra={"size_bytes": total_size})

        # Upload to S3
        s3_key = f"media/{user_id}/{asset_id}/{name}"
        s3_url = s3_manager.upload_file(
            local_path=temp_image_path,
            s3_key=s3_key,
            extra_args={"ContentType": "image/jpeg"},
        )

        logger.info("Image uploaded to S3", extra={"s3_key": s3_key})

        # Create database session and asset record with complete data
        db = SessionLocal()

        # Check if asset already exists
        asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id_uuid).first()

        final_metadata = {
            **metadata,
            "source": "ai_generation",
            "source_url": url,
            "imported_at": datetime.utcnow().isoformat(),
        }

        tags = metadata.get("tags", [])
        if "ai-generated" not in tags and (metadata.get("aiGenerated") or metadata.get("prompt")):
            tags.append("ai-generated")

        if not asset:
            logger.info("Creating new MediaAsset", extra={"asset_id": asset_id})
            asset = MediaAsset(
                id=asset_id_uuid,
                user_id=user_id_uuid,
                name=name,
                file_size=total_size,
                file_type=MediaAssetType.IMAGE,
                s3_key=s3_key,
                status=MediaAssetStatus.READY,
                checksum=checksum,
                file_metadata=final_metadata,
                tags=tags,
                is_deleted=False,
            )
            db.add(asset)
        else:
            logger.info("Updating existing MediaAsset", extra={"asset_id": asset_id})
            asset.file_size = total_size
            asset.s3_key = s3_key
            asset.checksum = checksum
            asset.file_metadata = final_metadata
            asset.status = MediaAssetStatus.READY
            asset.tags = tags
            asset.updated_at = datetime.utcnow()

        db.commit()

        logger.info("Image import job completed", extra={"asset_id": asset_id})

        return {
            "success": True,
            "asset_id": asset_id,
            "s3_url": s3_url,
            "status": "ready",
            "metadata": final_metadata,
        }

    except Exception as e:
        logger.exception(f"Image import job failed: {e}")

        if db:
            try:
                asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id_uuid).first()
                if asset:
                    asset.status = MediaAssetStatus.FAILED
                    asset.file_metadata = {
                        **(asset.file_metadata or {}),
                        "error": str(e),
                        "failed_at": datetime.utcnow().isoformat(),
                    }
                    asset.updated_at = datetime.utcnow()
                    db.commit()
            except Exception:
                pass

        raise

    finally:
        if temp_image_path and temp_image_path.exists():
            try:
                temp_image_path.unlink()
            except Exception:
                pass

        if db:
            db.close()
