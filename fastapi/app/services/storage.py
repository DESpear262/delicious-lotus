"""
Storage Service - Handles S3 and local filesystem storage
Supports both production (S3) and development (local filesystem) environments
"""

import os
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import timedelta

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available - S3 storage will not work")


class StorageService:
    """
    Service for storing files in S3 (production) or local filesystem (development)
    
    Automatically switches between storage backends based on USE_LOCAL_STORAGE env var.
    Supports presigned URL generation for S3 and local file serving.
    """
    
    def __init__(
        self,
        use_local: Optional[bool] = None,
        local_storage_path: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        aws_region: Optional[str] = None
    ):
        """
        Initialize storage service
        
        Args:
            use_local: If True, use local filesystem; if False, use S3. 
                      If None, reads from USE_LOCAL_STORAGE env var
            local_storage_path: Path for local storage (default: ./storage)
            s3_bucket: S3 bucket name (default: from S3_BUCKET env var)
            aws_region: AWS region (default: from AWS_REGION env var)
        """
        # Determine storage backend
        if use_local is None:
            use_local = os.getenv('USE_LOCAL_STORAGE', 'true').lower() == 'true'
        
        self.use_local = use_local
        
        # Get storage path and convert to absolute path
        storage_path = local_storage_path or os.getenv('LOCAL_STORAGE_PATH', './storage')
        self.local_storage_path = Path(storage_path)
        
        # Convert relative paths to absolute paths
        if not self.local_storage_path.is_absolute():
            # Resolve relative to current working directory, or use APP_HOME in containers
            if os.getenv('APP_HOME'):
                # In Docker container, resolve relative to APP_HOME (e.g., /app)
                # Handle both './storage' and 'storage' formats
                base_path = Path(os.getenv('APP_HOME'))
                # If path starts with './', remove it before joining
                path_str = str(self.local_storage_path)
                if path_str.startswith('./'):
                    path_str = path_str[2:]
                self.local_storage_path = (base_path / path_str).resolve()
            else:
                # Resolve relative to current working directory
                self.local_storage_path = self.local_storage_path.resolve()
        
        if not self.use_local:
            if not BOTO3_AVAILABLE:
                raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
            
            self.s3_bucket = s3_bucket or os.getenv('S3_BUCKET')
            if not self.s3_bucket:
                raise ValueError("S3_BUCKET environment variable must be set when USE_LOCAL_STORAGE=false")
            
            aws_region = aws_region or os.getenv('AWS_REGION', 'us-east-2')
            
            # Initialize S3 client
            # Use IAM role in production (no credentials needed), access keys for local dev
            self.s3_client = boto3.client(
                's3',
                region_name=aws_region,
                config=Config(signature_version='s3v4')
            )
            
            logger.info(f"StorageService initialized with S3 bucket: {self.s3_bucket}")
        else:
            # Ensure local storage directory exists with proper error handling
            try:
                self.local_storage_path.mkdir(parents=True, exist_ok=True)
                # Verify we can write to the directory
                test_file = self.local_storage_path / '.test_write'
                try:
                    test_file.touch()
                    test_file.unlink()
                except (PermissionError, OSError) as e:
                    raise PermissionError(
                        f"Cannot write to storage directory {self.local_storage_path}: {e}. "
                        f"Please check directory permissions."
                    )
                logger.info(f"StorageService initialized with local storage: {self.local_storage_path}")
            except PermissionError as e:
                logger.error(f"Permission denied creating storage directory: {e}")
                raise
            except OSError as e:
                logger.error(f"Failed to create storage directory {self.local_storage_path}: {e}")
                raise
    
    def upload_file(
        self,
        file_path: str,
        object_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file to storage (S3 or local filesystem)
        
        Args:
            file_path: Path to local file to upload
            object_key: Storage key/path (e.g., "generations/gen_123/clips/clip_001.mp4")
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the file
        
        Returns:
            URL or path to the uploaded file
        """
        if self.use_local:
            return self._upload_local(file_path, object_key)
        else:
            return self._upload_s3(file_path, object_key, content_type, metadata)
    
    def _upload_local(self, file_path: str, object_key: str) -> str:
        """Upload file to local filesystem"""
        dest_path = self.local_storage_path / object_key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, dest_path)
        logger.info(f"Uploaded file to local storage: {object_key}")
        
        # Return relative path for local serving
        return f"/storage/{object_key}"
    
    def _upload_s3(
        self,
        file_path: str,
        object_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Upload file to S3"""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = {str(k): str(v) for k, v in metadata.items()}
            
            self.s3_client.upload_file(
                file_path,
                self.s3_bucket,
                object_key,
                ExtraArgs=extra_args if extra_args else None
            )
            
            logger.info(f"Uploaded file to S3: s3://{self.s3_bucket}/{object_key}")
            return f"s3://{self.s3_bucket}/{object_key}"
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            raise
    
    def upload_from_url(
        self,
        url: str,
        object_key: str,
        content_type: Optional[str] = None,
        timeout: int = 60
    ) -> str:
        """
        Download a file from a URL and upload it to storage
        
        Args:
            url: URL to download from
            object_key: Storage key/path for the uploaded file
            content_type: MIME type of the file
            timeout: Download timeout in seconds
        
        Returns:
            URL or path to the uploaded file
        """
        import requests
        
        # Download to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_path = tmp_file.name
            
            try:
                response = requests.get(url, timeout=timeout, stream=True)
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                
                tmp_file.flush()
                
                # Upload to storage
                return self.upload_file(tmp_path, object_key, content_type)
                
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def generate_download_url(
        self,
        object_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate a presigned URL for downloading a file
        
        Args:
            object_key: Storage key/path
            expiration: URL expiration in seconds (default: 1 hour)
        
        Returns:
            Presigned URL (S3) or local file URL (local storage)
        """
        if self.use_local:
            # For local storage, return a path that can be served by FastAPI
            return f"/storage/{object_key}"
        else:
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.s3_bucket,
                        'Key': object_key
                    },
                    ExpiresIn=expiration
                )
                return url
            except (ClientError, BotoCoreError) as e:
                logger.error(f"Failed to generate presigned URL: {str(e)}")
                raise
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            object_key: Storage key/path to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        if self.use_local:
            file_path = self.local_storage_path / object_key
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file from local storage: {object_key}")
                return True
            return False
        else:
            try:
                self.s3_client.delete_object(
                    Bucket=self.s3_bucket,
                    Key=object_key
                )
                logger.info(f"Deleted file from S3: {object_key}")
                return True
            except (ClientError, BotoCoreError) as e:
                logger.error(f"Failed to delete file from S3: {str(e)}")
                return False
    
    def file_exists(self, object_key: str) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            object_key: Storage key/path to check
        
        Returns:
            True if file exists, False otherwise
        """
        if self.use_local:
            return (self.local_storage_path / object_key).exists()
        else:
            try:
                self.s3_client.head_object(
                    Bucket=self.s3_bucket,
                    Key=object_key
                )
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    return False
                raise

