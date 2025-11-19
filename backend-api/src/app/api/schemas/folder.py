"""Pydantic schemas for folder API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FolderBase(BaseModel):
    """Base schema for folder with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Folder name",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate folder name doesn't contain path separators."""
        if "/" in name or "\\" in name:
            raise ValueError("Folder name cannot contain path separators (/ or \\)")
        if name.strip() != name:
            raise ValueError("Folder name cannot have leading or trailing whitespace")
        return name


class FolderCreate(FolderBase):
    """Request schema for creating a new folder."""

    parent_id: UUID | None = Field(
        None,
        description="Parent folder ID (None for root folder)",
    )


class FolderUpdate(BaseModel):
    """Request schema for updating an existing folder."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="New folder name (for rename operation)",
    )
    parent_id: UUID | None = Field(
        None,
        description="New parent folder ID (for move operation, None to move to root)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str | None) -> str | None:
        """Validate folder name if provided."""
        if name is not None:
            if "/" in name or "\\" in name:
                raise ValueError("Folder name cannot contain path separators (/ or \\)")
            if name.strip() != name:
                raise ValueError("Folder name cannot have leading or trailing whitespace")
        return name


class FolderResponse(BaseModel):
    """Response schema for folder resource."""

    id: UUID = Field(..., description="Unique folder identifier")
    name: str = Field(..., description="Folder name")
    path: str = Field(..., description="Materialized path (/parent/child format)")
    parent_id: UUID | None = Field(None, description="Parent folder ID")
    owner_user_id: UUID = Field(..., description="Owner user ID")
    asset_count: int = Field(0, ge=0, description="Number of media assets in this folder")
    created_at: datetime = Field(..., description="When folder was created")
    updated_at: datetime = Field(..., description="When folder was last updated")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FolderTreeNode(BaseModel):
    """Response schema for folder tree structure with recursive children."""

    id: UUID = Field(..., description="Unique folder identifier")
    name: str = Field(..., description="Folder name")
    path: str = Field(..., description="Materialized path")
    parent_id: UUID | None = Field(None, description="Parent folder ID")
    asset_count: int = Field(0, ge=0, description="Number of media assets in this folder")
    children: list["FolderTreeNode"] = Field(
        default_factory=list,
        description="Child folders in tree structure",
    )
    created_at: datetime = Field(..., description="When folder was created")
    updated_at: datetime = Field(..., description="When folder was last updated")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# Enable forward references for recursive model
FolderTreeNode.model_rebuild()


class FolderListResponse(BaseModel):
    """Response schema for folder list endpoint with tree structure."""

    folders: list[FolderTreeNode] = Field(
        ...,
        description="List of folders in tree structure",
    )
    total: int = Field(..., ge=0, description="Total number of folders")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FolderLightResponse(BaseModel):
    """Lightweight folder response for content listings."""

    id: UUID = Field(..., description="Unique folder identifier")
    name: str = Field(..., description="Folder name")
    path: str = Field(..., description="Materialized path")
    asset_count: int = Field(0, ge=0, description="Number of media assets in this folder")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class MediaAssetLight(BaseModel):
    """Lightweight media asset response for folder contents."""

    id: UUID = Field(..., description="Unique media asset identifier")
    name: str = Field(..., description="Asset name")
    file_type: str = Field(..., description="Type of media asset")
    file_size: int = Field(..., description="File size in bytes")
    thumbnail_s3_key: str | None = Field(None, description="Thumbnail S3 object key")
    created_at: datetime = Field(..., description="When asset was created")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FolderContentsResponse(BaseModel):
    """Response schema for folder contents with pagination."""

    folder_id: UUID = Field(..., description="Folder ID")
    folder_path: str = Field(..., description="Folder path")
    subfolders: list[FolderLightResponse] = Field(
        default_factory=list,
        description="Subfolders in this folder",
    )
    assets: list[MediaAssetLight] = Field(
        default_factory=list,
        description="Media assets in this folder",
    )
    total_assets: int = Field(..., ge=0, description="Total number of assets")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FolderDeleteResponse(BaseModel):
    """Response schema for folder deletion."""

    deleted: bool = Field(..., description="Whether deletion was successful")
    folder_id: UUID = Field(..., description="Deleted folder ID")
    affected_subfolders: int = Field(0, ge=0, description="Number of subfolders deleted")
    affected_assets: int = Field(0, ge=0, description="Number of assets affected")
    message: str = Field(..., description="Summary message")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
