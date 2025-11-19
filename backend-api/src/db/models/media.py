"""
Media asset models for storing uploaded files and metadata.
"""

import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ARRAY, BigInteger, Boolean, CheckConstraint, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import BaseModel

if TYPE_CHECKING:
    from db.models.folder import Folder


class MediaAssetType(str, enum.Enum):
    """Type of media asset."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class MediaAssetStatus(str, enum.Enum):
    """Status of media asset processing."""

    PENDING_UPLOAD = "pending_upload"
    UPLOADING = "uploading"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class MediaAsset(BaseModel):
    """
    Model for storing media assets (images, videos, audio files).

    Media assets go through a lifecycle:
    1. PENDING_UPLOAD: Presigned URL generated, awaiting upload
    2. UPLOADING: Upload in progress
    3. READY: Upload complete, metadata extracted
    4. FAILED: Upload or processing failed
    5. DELETED: Soft deleted, scheduled for cleanup

    Attributes:
        id: UUID primary key
        user_id: Foreign key to users table (owner)
        name: Original filename or custom name
        file_size: Size in bytes
        file_type: Type of media (IMAGE/VIDEO/AUDIO)
        s3_key: S3 object key for the main file
        thumbnail_s3_key: S3 object key for thumbnail (optional)
        status: Current processing status
        checksum: File checksum (e.g., MD5, SHA256) for integrity
        file_metadata: JSONB field storing technical metadata (duration, dimensions, codec, etc.)
        folder_id: Optional foreign key to folders table for organization
        tags: Array of string tags for categorization
        is_deleted: Soft delete flag
    """

    __tablename__ = "media_assets"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User ownership
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic file information
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    file_type: Mapped[MediaAssetType] = mapped_column(
        Enum(MediaAssetType, name="media_asset_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )

    # S3 storage
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    thumbnail_s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Status tracking
    status: Mapped[MediaAssetStatus] = mapped_column(
        Enum(
            MediaAssetStatus,
            name="media_asset_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=MediaAssetStatus.PENDING_UPLOAD,
        nullable=False,
        index=True,
    )

    # File integrity
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)

    # Technical metadata (duration, width, height, frame_rate, codec, bitrate, etc.)
    file_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Organization
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="media_assets",
        foreign_keys=[user_id],
    )
    folder: Mapped["Folder | None"] = relationship(
        "Folder",
        back_populates="media_assets",
        foreign_keys=[folder_id],
    )

    # Indexes and constraints
    __table_args__ = (
        # GIN index for JSONB metadata queries
        Index(
            "ix_media_assets_file_metadata",
            "file_metadata",
            postgresql_using="gin",
        ),
        # GIN index for array tags
        Index(
            "ix_media_assets_tags",
            "tags",
            postgresql_using="gin",
        ),
        # Composite indexes for common queries
        Index("ix_media_assets_user_type", "user_id", "file_type"),
        Index("ix_media_assets_user_status", "user_id", "status"),
        Index("ix_media_assets_user_deleted", "user_id", "is_deleted"),
        Index("ix_media_assets_folder_deleted", "folder_id", "is_deleted"),
        Index("ix_media_assets_status_created", "status", "created_at"),
        # Constraint for positive file size
        CheckConstraint("file_size > 0", name="ck_media_assets_file_size_positive"),
    )

    def __repr__(self) -> str:
        """String representation of MediaAsset."""
        return (
            f"<MediaAsset(id={self.id}, name={self.name!r}, "
            f"type={self.file_type}, status={self.status})>"
        )
