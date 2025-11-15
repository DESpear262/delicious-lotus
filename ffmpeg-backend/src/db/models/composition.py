"""
Composition model for video/media compositions.
"""

import enum
import uuid
from typing import Any

from sqlalchemy import Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import BaseModel


class CompositionStatus(str, enum.Enum):
    """Status enum for composition processing states."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Composition(BaseModel):
    """
    Composition model for storing video/media composition configurations and state.

    Attributes:
        id: UUID primary key
        title: Human-readable title for the composition
        description: Optional description
        status: Current processing status
        composition_config: JSONB field storing composition configuration (clips, effects, etc.)
        processing_progress: JSONB field storing current processing progress and metadata
        output_url: URL to the final rendered output (when completed)
        error_message: Error message if processing failed
    """

    __tablename__ = "compositions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic fields
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[CompositionStatus] = mapped_column(
        Enum(CompositionStatus, name="composition_status"),
        default=CompositionStatus.PENDING,
        nullable=False,
        index=True,
    )

    # JSONB fields for flexible configuration storage
    composition_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    processing_progress: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, default=None
    )

    # Output and error tracking
    output_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(  # type: ignore[name-defined]
        "ProcessingJob",
        back_populates="composition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    metrics: Mapped[list["JobMetric"]] = relationship(  # type: ignore[name-defined]
        "JobMetric",
        back_populates="composition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes for JSONB fields (GIN indexes for efficient querying)
    __table_args__ = (
        Index(
            "ix_compositions_composition_config",
            "composition_config",
            postgresql_using="gin",
        ),
        Index(
            "ix_compositions_processing_progress",
            "processing_progress",
            postgresql_using="gin",
        ),
        # Composite index for common queries
        Index("ix_compositions_status_created_at", "status", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation of Composition."""
        return f"<Composition(id={self.id}, title={self.title!r}, status={self.status})>"
