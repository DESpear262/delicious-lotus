"""Pydantic schemas for project API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.api.schemas.composition import CompositionResponse


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    aspect_ratio: str = Field(
        default="16:9",
        pattern=r"^\d+:\d+$",
        description="Video aspect ratio (e.g., '16:9', '4:3', '1:1', '9:16')",
    )
    timebase_fps: int = Field(
        default=30, ge=1, le=120, description="Timeline frames per second (1-120)"
    )
    user_id: UUID = Field(..., description="UUID of the user creating this project")

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, value: str) -> str:
        """Validate aspect ratio format and common values."""
        # Common aspect ratios - for documentation/logging purposes
        common_ratios = {"16:9", "4:3", "1:1", "21:9", "9:16", "3:2", "2:3"}

        # Validate format (already done by regex, but we can add semantic validation)
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("Aspect ratio must be in format 'width:height' (e.g., '16:9')")

        try:
            width = int(parts[0])
            height = int(parts[1])
            if width <= 0 or height <= 0:
                raise ValueError("Aspect ratio values must be positive integers")
        except ValueError:
            raise ValueError("Aspect ratio must contain valid positive integers")

        return value


class ProjectUpdateRequest(BaseModel):
    """Request model for updating an existing project (autosave)."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Project name")
    thumbnail_url: str | None = Field(
        None, max_length=1024, description="URL to project thumbnail image"
    )
    composition: dict[str, Any] | None = Field(
        None,
        description="Full composition object with tracks/clips/transitions JSONB structure",
    )
    updated_at: datetime | None = Field(
        None,
        description="Last known updated_at timestamp for optimistic locking",
    )


class ProjectResponse(BaseModel):
    """Response model for project resource with full composition data."""

    id: UUID = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    user_id: UUID = Field(..., description="Owner user ID")
    thumbnail_url: str | None = Field(None, description="Project thumbnail URL")
    aspect_ratio: str = Field(..., description="Video aspect ratio")
    timebase_fps: int = Field(..., description="Timeline frames per second")
    composition_id: UUID = Field(..., description="Linked composition ID")
    is_deleted: bool = Field(..., description="Soft delete flag")
    created_at: datetime = Field(..., description="When project was created")
    updated_at: datetime = Field(..., description="When project was last updated")
    last_modified_at: datetime = Field(..., description="When project was last modified")
    composition: CompositionResponse | None = Field(None, description="Full composition data")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProjectListItemResponse(BaseModel):
    """Response model for lightweight project list items (without full composition data)."""

    id: UUID = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    user_id: UUID = Field(..., description="Owner user ID")
    thumbnail_url: str | None = Field(None, description="Project thumbnail URL")
    aspect_ratio: str = Field(..., description="Video aspect ratio")
    timebase_fps: int = Field(..., description="Timeline frames per second")
    composition_id: UUID = Field(..., description="Linked composition ID")
    created_at: datetime = Field(..., description="When project was created")
    updated_at: datetime = Field(..., description="When project was last updated")
    last_modified_at: datetime = Field(..., description="When project was last modified")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProjectListResponse(BaseModel):
    """Response model for project list endpoint with pagination."""

    items: list[ProjectListItemResponse] = Field(..., description="List of projects in current page")
    total: int = Field(..., ge=0, description="Total number of projects matching filters")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(..., ge=1, description="Number of items per page")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProjectDuplicateResponse(BaseModel):
    """Response model for project duplication."""

    id: UUID = Field(..., description="New duplicated project ID")
    name: str = Field(..., description="New project name (with 'Copy' suffix)")
    original_project_id: UUID = Field(..., description="Original project ID that was duplicated")
    composition_id: UUID = Field(..., description="New composition ID")
    created_at: datetime = Field(..., description="When duplicate was created")
    message: str = Field(..., description="Success message")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProjectDeleteResponse(BaseModel):
    """Response model for project soft delete."""

    id: UUID = Field(..., description="Deleted project ID")
    message: str = Field(..., description="Deletion confirmation message")
    deleted_at: datetime = Field(..., description="When project was deleted")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProjectVersionResponse(BaseModel):
    """Response model for project version history (future feature placeholder)."""

    project_id: UUID = Field(..., description="Project ID")
    versions: list[dict[str, Any]] = Field(
        default_factory=list, description="List of version history entries"
    )
    message: str = Field(
        default="Version history feature not yet implemented",
        description="Status message",
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class ProjectRestoreResponse(BaseModel):
    """Response model for project version restoration (future feature placeholder)."""

    project_id: UUID = Field(..., description="Project ID")
    version_id: UUID = Field(..., description="Version ID to restore")
    message: str = Field(
        default="Version restoration feature not yet implemented",
        description="Status message",
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True
