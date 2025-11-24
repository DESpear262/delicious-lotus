"""
Project model for video projects.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import BaseModel


class ProjectType(str, enum.Enum):
    """Enum for different project types."""
    AD_CREATIVE = "ad-creative"
    MUSIC_VIDEO = "music-video"
    EDUCATIONAL_VIDEO = "educational-video"
    CUSTOM = "custom"


class Project(BaseModel):
    """
    Project model for storing video project metadata and settings.

    A Project has a one-to-one relationship with a Composition that contains
    the actual timeline data (tracks, clips, transitions, effects).

    Attributes:
        id: UUID primary key
        name: Human-readable project name
        user_id: UUID of the user who owns this project
        project_type: Type of the project (e.g. ad-creative, custom)
        thumbnail_url: Optional URL to project thumbnail image
        aspect_ratio: Video aspect ratio (e.g., '16:9', '4:3', '1:1')
        timebase_fps: Timeline frames per second (default: 30)
        composition_id: Foreign key to the linked Composition
        is_deleted: Soft delete flag to preserve data for recovery
        last_modified_at: Timestamp of last modification (for autosave tracking)
        composition: Relationship to the linked Composition
    """

    __tablename__ = "projects"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project settings
    project_type: Mapped[str] = mapped_column(String(50), nullable=False, default=ProjectType.CUSTOM, server_default="custom")
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    aspect_ratio: Mapped[str] = mapped_column(String(20), nullable=False, default="16:9")
    timebase_fps: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # One-to-one relationship with Composition
    composition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compositions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Additional timestamp for tracking modifications (for autosave)
    last_modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
        foreign_keys=[user_id],
    )

    composition: Mapped["Composition"] = relationship(  # type: ignore[name-defined]
        "Composition",
        back_populates="project",
        lazy="selectin",
        uselist=False,
    )

    # Indexes for common queries
    __table_args__ = (
        # Composite index for user's active projects sorted by modification time
        Index("ix_projects_user_deleted_modified", "user_id", "is_deleted", "last_modified_at"),
        # Composite index for user's projects sorted by creation time
        Index("ix_projects_user_deleted_created", "user_id", "is_deleted", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of Project."""
        return f"<Project(id={self.id}, name={self.name!r}, user_id={self.user_id})>"
