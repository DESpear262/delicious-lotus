"""Log archiving utility for backing up logs to S3."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ..config import get_settings

logger = logging.getLogger(__name__)


class LogArchiver:
    """Handles archiving old log files to S3 for long-term storage."""

    def __init__(self) -> None:
        """Initialize log archiver with S3 client."""
        self.settings = get_settings()
        self.enabled = self.settings.log_s3_archive_enabled

        if self.enabled:
            self.s3_client = boto3.client(
                "s3",
                region_name=self.settings.s3_region,
                aws_access_key_id=self.settings.s3_access_key_id,
                aws_secret_access_key=self.settings.s3_secret_access_key,
                endpoint_url=self.settings.s3_endpoint_url,
            )
            self.bucket_name = self.settings.s3_bucket_name

    def archive_old_logs(
        self, log_dir: Path, archive_days: int = 7, delete_after_archive: bool = True
    ) -> int:
        """Archive log files older than specified days to S3.

        Args:
            log_dir: Directory containing log files
            archive_days: Archive logs older than this many days
            delete_after_archive: Delete local files after successful archive

        Returns:
            int: Number of files archived
        """
        if not self.enabled:
            logger.info("S3 log archiving is disabled")
            return 0

        if not log_dir.exists():
            logger.warning(f"Log directory does not exist: {log_dir}")
            return 0

        archived_count = 0
        cutoff_date = datetime.now() - timedelta(days=archive_days)

        try:
            # Find compressed log files to archive
            for log_file in log_dir.glob("*.log.*.gz"):
                # Skip if file is too recent
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime >= cutoff_date:
                    continue

                # Generate S3 key with date prefix for organization
                date_prefix = file_mtime.strftime("%Y/%m/%d")
                s3_key = f"logs/{date_prefix}/{log_file.name}"

                # Upload to S3
                try:
                    self.s3_client.upload_file(
                        str(log_file),
                        self.bucket_name,
                        s3_key,
                        ExtraArgs={
                            "StorageClass": "STANDARD_IA",  # Use infrequent access for cost savings
                            "ServerSideEncryption": "AES256",
                        },
                    )

                    logger.info(
                        "Archived log file to S3",
                        extra={
                            "file": str(log_file),
                            "s3_key": s3_key,
                            "bucket": self.bucket_name,
                        },
                    )

                    # Delete local file if requested
                    if delete_after_archive:
                        log_file.unlink()
                        logger.debug(f"Deleted local log file: {log_file}")

                    archived_count += 1

                except (BotoCoreError, ClientError) as e:
                    logger.error(
                        f"Failed to archive log file {log_file} to S3: {e}",
                        exc_info=True,
                    )
                    continue

        except Exception as e:
            logger.error(f"Error during log archiving: {e}", exc_info=True)

        if archived_count > 0:
            logger.info(f"Successfully archived {archived_count} log files to S3")

        return archived_count

    def retrieve_archived_log(self, s3_key: str, destination: Path) -> bool:
        """Retrieve an archived log file from S3.

        Args:
            s3_key: S3 key of the archived log file
            destination: Local path to save the file

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.error("S3 log archiving is disabled")
            return False

        try:
            self.s3_client.download_file(self.bucket_name, s3_key, str(destination))
            logger.info(
                "Retrieved archived log from S3",
                extra={"s3_key": s3_key, "destination": str(destination)},
            )
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to retrieve log from S3: {e}", exc_info=True)
            return False

    def list_archived_logs(self, prefix: str = "logs/") -> list[str]:
        """List archived log files in S3.

        Args:
            prefix: S3 prefix to filter logs

        Returns:
            list[str]: List of S3 keys for archived logs
        """
        if not self.enabled:
            logger.error("S3 log archiving is disabled")
            return []

        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            if "Contents" not in response:
                return []

            return [obj["Key"] for obj in response["Contents"]]
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to list archived logs from S3: {e}", exc_info=True)
            return []


def archive_logs_task() -> None:
    """Background task to archive old logs to S3.

    This can be called from a cron job or scheduled task.
    """
    settings = get_settings()

    if not settings.log_s3_archive_enabled:
        logger.info("S3 log archiving is disabled, skipping")
        return

    archiver = LogArchiver()
    log_dir = Path("./logs")

    # Archive logs older than 7 days
    archived_count = archiver.archive_old_logs(
        log_dir=log_dir, archive_days=7, delete_after_archive=True
    )

    logger.info(f"Log archiving task completed, archived {archived_count} files")
