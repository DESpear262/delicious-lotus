"""
Folder models for hierarchical media organization.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import BaseModel

if TYPE_CHECKING:
    from db.models.media import MediaAsset


class Folder(BaseModel):
    """
    Model for hierarchical folder structure using materialized path pattern.

    Folders organize media assets in a tree structure. The materialized path
    pattern stores the full path from root to the current folder, enabling
    efficient tree queries and operations.

    Path format: /parent/child/grandchild
    Root folders have path: /foldername

    Attributes:
        id: UUID primary key
        name: Folder name (unique within parent)
        parent_id: Foreign key to parent folder (NULL for root folders)
        path: Materialized path from root (/parent/child format)
        owner_user_id: Foreign key to users table (owner)
        parent: Relationship to parent folder
        children: Relationship to child folders
        media_assets: Relationship to media assets in this folder
    """

    __tablename__ = "folders"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Folder name
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Self-referential parent relationship
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Materialized path for efficient tree queries
    # Format: /parent/child/grandchild
    path: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)

    # User ownership
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="folders",
        foreign_keys=[owner_user_id],
    )

    parent: Mapped["Folder | None"] = relationship(
        "Folder",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id],
    )

    children: Mapped[list["Folder"]] = relationship(
        "Folder",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )

    media_assets: Mapped[list["MediaAsset"]] = relationship(
        "MediaAsset",
        back_populates="folder",
        foreign_keys="MediaAsset.folder_id",
    )

    # Indexes and constraints
    __table_args__ = (
        # Composite index for user + name queries
        Index("ix_folders_owner_name", "owner_user_id", "name"),
        # Index for path prefix queries (tree traversal)
        Index(
            "ix_folders_path_prefix",
            "path",
            postgresql_ops={"path": "text_pattern_ops"},
        ),
        # Composite index for parent + name (sibling uniqueness)
        Index("ix_folders_parent_name", "parent_id", "name"),
        # Ensure folder names are not empty
        CheckConstraint("length(name) > 0", name="ck_folders_name_not_empty"),
        # Ensure paths start with /
        CheckConstraint("path ~ '^/.*'", name="ck_folders_path_format"),
    )

    def compute_path(self, parent_path: str | None = None) -> str:
        """
        Compute the materialized path for this folder.

        Args:
            parent_path: Path of parent folder (if any)

        Returns:
            Computed path in format /parent/child
        """
        if parent_path is None:
            # Root folder
            return f"/{self.name}"
        else:
            # Child folder
            return f"{parent_path}/{self.name}"

    def get_descendants_path_pattern(self) -> str:
        """
        Get SQL pattern for finding all descendants.

        Returns:
            SQL LIKE pattern to match all descendant paths
        """
        return f"{self.path}/%"

    def __repr__(self) -> str:
        """String representation of Folder."""
        return f"<Folder(id={self.id}, name={self.name!r}, path={self.path!r})>"
