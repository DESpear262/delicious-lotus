"""Pydantic schemas for media asset API endpoints."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MediaType(str, Enum):
    """Types of media assets."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class MediaStatus(str, Enum):
    """Status of media asset processing."""

    PENDING_UPLOAD = "pending_upload"
    UPLOADING = "uploading"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class TagOperation(str, Enum):
    """Operations for batch tagging."""

    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"


# File size limits in bytes
MAX_IMAGE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_VIDEO_SIZE = 1024 * 1024 * 1024  # 1 GB
MAX_AUDIO_SIZE = 500 * 1024 * 1024  # 500 MB


class MediaUploadRequest(BaseModel):
    """Request model for initiating a media asset upload."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Original filename or custom name for the asset",
    )
    size: int = Field(..., gt=0, description="File size in bytes")
    type: MediaType = Field(..., description="Type of media asset (image/video/audio)")
    checksum: str = Field(
        ...,
        min_length=32,
        max_length=128,
        pattern=r"^[a-fA-F0-9]+$",
        description="File checksum (MD5 or SHA256) for integrity verification",
    )

    @field_validator("size")
    @classmethod
    def validate_file_size(cls, size: int, info) -> int:
        """Validate file size based on media type."""
        if "type" not in info.data:
            return size

        media_type = info.data["type"]
        if media_type == MediaType.IMAGE and size > MAX_IMAGE_SIZE:
            raise ValueError(f"Image file size exceeds maximum allowed ({MAX_IMAGE_SIZE // (1024 * 1024)} MB)")
        elif media_type == MediaType.VIDEO and size > MAX_VIDEO_SIZE:
            raise ValueError(f"Video file size exceeds maximum allowed ({MAX_VIDEO_SIZE // (1024 * 1024)} MB)")
        elif media_type == MediaType.AUDIO and size > MAX_AUDIO_SIZE:
            raise ValueError(f"Audio file size exceeds maximum allowed ({MAX_AUDIO_SIZE // (1024 * 1024)} MB)")

        return size


class UploadParams(BaseModel):
    """Upload parameters for S3 presigned URL."""

    method: str = Field(..., description="HTTP method for upload (e.g., PUT, POST)")
    headers: dict[str, str] = Field(default_factory=dict, description="Required headers for upload")
    fields: dict[str, str] = Field(default_factory=dict, description="Form fields for multipart upload")


class MediaUploadResponse(BaseModel):
    """Response model for media upload initiation."""

    id: UUID = Field(..., description="Unique media asset identifier")
    presigned_url: str = Field(..., description="Presigned S3 URL for uploading the file")
    upload_params: UploadParams = Field(..., description="Parameters for completing the upload")
    expires_in: int = Field(..., description="Seconds until presigned URL expires")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MediaMetadata(BaseModel):
    """Technical metadata for media assets."""

    duration: float | None = Field(None, ge=0, description="Duration in seconds (video/audio)")
    width: int | None = Field(None, gt=0, description="Width in pixels (image/video)")
    height: int | None = Field(None, gt=0, description="Height in pixels (image/video)")
    frame_rate: float | None = Field(None, gt=0, description="Frame rate (video)")
    codec: str | None = Field(None, description="Codec used (video/audio)")
    bitrate: int | None = Field(None, gt=0, description="Bitrate in bits per second")
    sample_rate: int | None = Field(None, gt=0, description="Audio sample rate in Hz")
    channels: int | None = Field(None, gt=0, description="Number of audio channels")


class MediaAssetResponse(BaseModel):
    """Response model for media asset resource."""

    id: UUID = Field(..., description="Unique media asset identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    name: str = Field(..., description="Asset name")
    file_size: int = Field(..., description="File size in bytes")
    file_type: MediaType = Field(..., description="Type of media asset")
    s3_key: str = Field(..., description="S3 object key")
    url: str | None = Field(None, description="Presigned URL or S3 URL for accessing the asset")
    thumbnail_s3_key: str | None = Field(None, description="Thumbnail S3 object key")
    thumbnail_url: str | None = Field(None, description="Presigned URL for thumbnail")
    status: MediaStatus = Field(..., description="Current processing status")
    checksum: str = Field(..., description="File checksum")
    file_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Technical metadata",
        serialization_alias="metadata",
    )
    folder_id: UUID | None = Field(None, description="Parent folder ID")
    tags: list[str] = Field(default_factory=list, description="Asset tags")
    is_deleted: bool = Field(..., description="Soft delete flag")
    created_at: datetime = Field(..., description="When asset was created")
    updated_at: datetime = Field(..., description="When asset was last updated")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        populate_by_name = True


class MediaAssetLightResponse(BaseModel):
    """Lightweight response model for media asset list."""

    id: UUID = Field(..., description="Unique media asset identifier")
    name: str = Field(..., description="Asset name")
    file_type: MediaType = Field(..., description="Type of media asset")
    file_size: int = Field(..., description="File size in bytes")
    status: MediaStatus = Field(..., description="Current processing status")
    s3_key: str = Field(..., description="S3 object key for the main file")
    url: str | None = Field(None, description="Presigned URL or S3 URL for accessing the asset")
    thumbnail_s3_key: str | None = Field(None, description="Thumbnail S3 object key")
    thumbnail_url: str | None = Field(None, description="Presigned URL for thumbnail")
    tags: list[str] = Field(default_factory=list, description="Asset tags")
    created_at: datetime = Field(..., description="When asset was created")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MediaListResponse(BaseModel):
    """Response model for media asset list with pagination."""

    assets: list[MediaAssetLightResponse] = Field(
        ..., description="List of media assets in current page"
    )
    total: int = Field(..., ge=0, description="Total number of assets matching filters")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MediaMetadataUpdate(BaseModel):
    """Update model for media asset metadata after FFprobe extraction."""

    metadata: MediaMetadata = Field(..., description="Extracted technical metadata")
    status: MediaStatus = Field(
        default=MediaStatus.READY, description="Updated status after processing"
    )


class MediaBatchDeleteRequest(BaseModel):
    """Request model for batch deleting media assets."""

    asset_ids: list[UUID] = Field(
        ..., min_items=1, max_items=100, description="List of asset IDs to delete"
    )


class MediaBatchDeleteResponse(BaseModel):
    """Response model for batch delete operation."""

    deleted_count: int = Field(..., ge=0, description="Number of assets successfully deleted")
    failed_count: int = Field(..., ge=0, description="Number of assets that failed to delete")
    deleted_ids: list[UUID] = Field(default_factory=list, description="Successfully deleted asset IDs")
    failed_ids: list[UUID] = Field(default_factory=list, description="Failed asset IDs")
    message: str = Field(..., description="Summary message")


class MediaBatchTagRequest(BaseModel):
    """Request model for batch tagging media assets."""

    asset_ids: list[UUID] = Field(
        ..., min_items=1, max_items=100, description="List of asset IDs to tag"
    )
    tags: list[str] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="Tags to add, remove, or replace",
    )
    operation: TagOperation = Field(
        default=TagOperation.ADD, description="Tag operation to perform"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        """Validate tag format and length."""
        for tag in tags:
            if not tag or len(tag) > 50:
                raise ValueError("Tags must be between 1 and 50 characters")
            if not tag.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Tags can only contain alphanumeric characters, hyphens, and underscores")
        return tags


class MediaBatchTagResponse(BaseModel):
    """Response model for batch tag operation."""

    updated_count: int = Field(..., ge=0, description="Number of assets successfully updated")
    failed_count: int = Field(..., ge=0, description="Number of assets that failed to update")
    updated_ids: list[UUID] = Field(default_factory=list, description="Successfully updated asset IDs")
    failed_ids: list[UUID] = Field(default_factory=list, description="Failed asset IDs")
    message: str = Field(..., description="Summary message")


class MediaBatchMoveRequest(BaseModel):
    """Request model for batch moving media assets to a folder."""

    asset_ids: list[UUID] = Field(
        ..., min_items=1, max_items=100, description="List of asset IDs to move"
    )
    folder_id: UUID | None = Field(
        None, description="Target folder ID (None to move to root)"
    )


class MediaBatchMoveResponse(BaseModel):
    """Response model for batch move operation."""

    moved_count: int = Field(..., ge=0, description="Number of assets successfully moved")
    failed_count: int = Field(..., ge=0, description="Number of assets that failed to move")
    moved_ids: list[UUID] = Field(default_factory=list, description="Successfully moved asset IDs")
    failed_ids: list[UUID] = Field(default_factory=list, description="Failed asset IDs")
    message: str = Field(..., description="Summary message")


class ThumbnailGenerationRequest(BaseModel):
    """Request model for regenerating thumbnail."""

    timestamp: float | None = Field(
        None,
        ge=0,
        description="Timestamp in seconds for thumbnail frame (video only, default is 0)",
    )


class ThumbnailGenerationResponse(BaseModel):
    """Response model for thumbnail generation job."""

    asset_id: UUID = Field(..., description="Media asset ID")
    job_id: str = Field(..., description="Worker job ID for tracking")
    message: str = Field(..., description="Status message")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MediaImportFromUrlRequest(BaseModel):
    """Request model for importing media from external URL."""

    url: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="URL to download media from (e.g., Replicate CDN)",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Filename for the imported asset",
    )
    type: MediaType = Field(..., description="Type of media asset (image/video/audio)")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (AI generation info, prompt, etc.)",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: str) -> str:
        """Validate URL format."""
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return url


class MediaImportFromUrlResponse(BaseModel):
    """Response model for media import from URL."""

    id: UUID = Field(..., description="Created media asset ID")
    name: str = Field(..., description="Asset name")
    type: MediaType = Field(..., description="Type of media asset")
    url: str = Field(..., description="S3 URL for the imported asset")
    thumbnail_url: str | None = Field(None, description="Thumbnail URL if available")
    size: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="When asset was created")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Asset metadata including AI generation info"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True
