"""S3 asset download and upload management with retry logic."""

import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import boto3
from app.config import settings
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class S3Manager:
    """Manages S3 operations with retry logic and progress tracking."""

    def __init__(self) -> None:
        """Initialize S3 manager with configured client."""
        self.bucket_name = settings.s3_bucket_name

        # Configure boto3 client with retry logic
        config = Config(
            region_name=settings.s3_region,
            retries={
                "max_attempts": 3,
                "mode": "adaptive",
            },
            max_pool_connections=50,
        )

        # Create S3 client
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            endpoint_url=settings.s3_endpoint_url,
            config=config,
        )

        logger.info(
            "Initialized S3Manager",
            extra={
                "bucket": self.bucket_name,
                "region": settings.s3_region,
                "endpoint": settings.s3_endpoint_url or "default",
            },
        )

    @retry(
        retry=retry_if_exception_type((ClientError, BotoCoreError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def download_file(
        self,
        s3_key: str,
        local_path: str | Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """Download a file from S3 with retry logic and progress tracking.

        Args:
            s3_key: S3 object key
            local_path: Local file path to save to
            progress_callback: Optional callback for progress updates (bytes_downloaded, total_bytes)

        Returns:
            Path: Path to downloaded file

        Raises:
            ClientError: If S3 download fails
            FileNotFoundError: If S3 object doesn't exist
        """
        local_path = Path(local_path)

        try:
            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Get object metadata for size info
            try:
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                total_size = response.get("ContentLength", 0)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    raise FileNotFoundError(
                        f"S3 object not found: s3://{self.bucket_name}/{s3_key}"
                    ) from e
                raise

            logger.info(
                f"Starting download: s3://{self.bucket_name}/{s3_key}",
                extra={
                    "s3_key": s3_key,
                    "local_path": str(local_path),
                    "size_bytes": total_size,
                },
            )

            # Download with progress tracking
            bytes_downloaded = 0

            def progress_hook(bytes_amount: int) -> None:
                nonlocal bytes_downloaded
                bytes_downloaded += bytes_amount
                if progress_callback:
                    progress_callback(bytes_downloaded, total_size)

            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=s3_key,
                Filename=str(local_path),
                Callback=progress_hook if progress_callback else None,
            )

            logger.info(
                f"Download completed: {s3_key}",
                extra={
                    "s3_key": s3_key,
                    "local_path": str(local_path),
                    "size_bytes": total_size,
                },
            )

            return local_path

        except Exception as e:
            logger.exception(
                f"Failed to download from S3: {s3_key}",
                extra={"s3_key": s3_key, "error": str(e)},
            )
            raise

    @retry(
        retry=retry_if_exception_type((ClientError, BotoCoreError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def upload_file(
        self,
        local_path: str | Path,
        s3_key: str,
        progress_callback: Callable[[int, int], None] | None = None,
        extra_args: dict[str, Any] | None = None,
    ) -> str:
        """Upload a file to S3 with retry logic and multipart support.

        Args:
            local_path: Local file path to upload
            s3_key: S3 object key
            progress_callback: Optional callback for progress updates (bytes_uploaded, total_bytes)
            extra_args: Extra arguments for upload (ContentType, Metadata, etc.)

        Returns:
            str: S3 URL of uploaded file

        Raises:
            ClientError: If S3 upload fails
            FileNotFoundError: If local file doesn't exist
        """
        local_path = Path(local_path)

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            file_size = local_path.stat().st_size

            logger.info(
                f"Starting upload: {local_path} -> s3://{self.bucket_name}/{s3_key}",
                extra={
                    "local_path": str(local_path),
                    "s3_key": s3_key,
                    "size_bytes": file_size,
                },
            )

            # Use multipart upload for files larger than 100MB
            use_multipart = file_size > 100 * 1024 * 1024

            if use_multipart:
                logger.debug(f"Using multipart upload for large file: {file_size} bytes")
                transfer_config = boto3.s3.transfer.TransferConfig(
                    multipart_threshold=100 * 1024 * 1024,  # 100MB
                    max_concurrency=10,
                    multipart_chunksize=10 * 1024 * 1024,  # 10MB chunks
                )
            else:
                transfer_config = None

            # Track upload progress
            bytes_uploaded = 0

            def progress_hook(bytes_amount: int) -> None:
                nonlocal bytes_uploaded
                bytes_uploaded += bytes_amount
                if progress_callback:
                    progress_callback(bytes_uploaded, file_size)

            # Perform upload
            self.s3_client.upload_file(
                Filename=str(local_path),
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args or {},
                Config=transfer_config,
                Callback=progress_hook if progress_callback else None,
            )

            # Generate S3 URL
            if settings.s3_endpoint_url:
                s3_url = f"{settings.s3_endpoint_url}/{self.bucket_name}/{s3_key}"
            else:
                s3_url = (
                    f"https://{self.bucket_name}.s3.{settings.s3_region}.amazonaws.com/{s3_key}"
                )

            logger.info(
                f"Upload completed: {s3_key}",
                extra={
                    "local_path": str(local_path),
                    "s3_key": s3_key,
                    "s3_url": s3_url,
                    "size_bytes": file_size,
                },
            )

            return s3_url

        except Exception as e:
            logger.exception(
                f"Failed to upload to S3: {s3_key}",
                extra={"s3_key": s3_key, "local_path": str(local_path), "error": str(e)},
            )
            raise

    def download_assets(
        self,
        assets: list[dict[str, str]],
        temp_dir: str | Path,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, Path]:
        """Download multiple assets from S3.

        Args:
            assets: List of asset dictionaries with 's3_key' and optional 'id'
            temp_dir: Temporary directory to download assets to
            progress_callback: Optional callback (asset_id, bytes_downloaded, total_bytes)

        Returns:
            dict: Mapping of asset ID to local path

        Raises:
            Exception: If any download fails
        """
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        downloaded_files = {}

        logger.info(
            f"Downloading {len(assets)} assets",
            extra={"asset_count": len(assets), "temp_dir": str(temp_dir)},
        )

        for i, asset in enumerate(assets):
            s3_key = asset.get("s3_key")
            asset_id = asset.get("id", f"asset_{i}")

            if not s3_key:
                logger.warning(f"Asset {asset_id} missing s3_key, skipping")
                continue

            # Generate local filename from S3 key
            filename = os.path.basename(s3_key)
            local_path = temp_dir / f"{asset_id}_{filename}"

            # Create progress callback for this asset
            def asset_progress(bytes_down: int, total_bytes: int, aid: str = asset_id) -> None:
                if progress_callback:
                    progress_callback(aid, bytes_down, total_bytes)

            try:
                downloaded_path = self.download_file(
                    s3_key=s3_key,
                    local_path=local_path,
                    progress_callback=asset_progress,
                )
                downloaded_files[asset_id] = downloaded_path

                logger.debug(
                    f"Downloaded asset {asset_id}",
                    extra={"asset_id": asset_id, "path": str(downloaded_path)},
                )

            except Exception as e:
                logger.exception(
                    f"Failed to download asset {asset_id}",
                    extra={"asset_id": asset_id, "s3_key": s3_key, "error": str(e)},
                )
                raise

        logger.info(
            f"Downloaded all {len(downloaded_files)} assets successfully",
            extra={"downloaded_count": len(downloaded_files)},
        )

        return downloaded_files

    def delete_file(self, s3_key: str) -> None:
        """Delete a file from S3.

        Args:
            s3_key: S3 object key to delete
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted S3 object: {s3_key}")

        except Exception as e:
            logger.exception(
                f"Failed to delete S3 object: {s3_key}",
                extra={"s3_key": s3_key, "error": str(e)},
            )
            raise

    def object_exists(self, s3_key: str) -> bool:
        """Check if an S3 object exists.

        Args:
            s3_key: S3 object key to check

        Returns:
            bool: True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise


# Global S3 manager instance
s3_manager = S3Manager()
