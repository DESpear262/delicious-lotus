"""initial schema with compositions jobs and metrics

Revision ID: 001
Revises:
Create Date: 2025-11-14

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables and triggers."""
    # Create enum types (with IF NOT EXISTS)
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE composition_status AS ENUM ('pending', 'queued', 'processing', 'completed', 'failed', 'cancelled'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE job_type AS ENUM ('composition_render', 'video_transcode', 'audio_process', 'thumbnail_generate'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE job_status AS ENUM ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled', 'retrying'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE metric_type AS ENUM ('processing_duration', 'file_size', 'bitrate', 'frame_rate', 'resolution', 'queue_wait_time', 'memory_usage', 'cpu_usage'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    # Create updated_at trigger function (idempotent with CREATE OR REPLACE)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )

    # Create compositions table
    op.create_table(
        "compositions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "queued",
                "processing",
                "completed",
                "failed",
                "cancelled",
                name="composition_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("composition_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("processing_progress", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_url", sa.String(length=1024), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_compositions")),
    )
    op.create_index(op.f("ix_compositions_status"), "compositions", ["status"], unique=False)
    op.create_index(op.f("ix_compositions_title"), "compositions", ["title"], unique=False)
    op.create_index(
        "ix_compositions_status_created_at", "compositions", ["status", "created_at"], unique=False
    )
    op.create_index(
        "ix_compositions_composition_config",
        "compositions",
        ["composition_config"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_compositions_processing_progress",
        "compositions",
        ["processing_progress"],
        unique=False,
        postgresql_using="gin",
    )

    # Create trigger for compositions
    op.execute(
        """
        CREATE TRIGGER update_compositions_updated_at
        BEFORE UPDATE ON compositions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # Create processing_jobs table
    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("composition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_type",
            postgresql.ENUM(
                "composition_render",
                "video_transcode",
                "audio_process",
                "thumbnail_generate",
                name="job_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "queued",
                "running",
                "completed",
                "failed",
                "cancelled",
                "retrying",
                name="job_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "retry_count >= 0", name=op.f("ck_processing_jobs_retry_count_positive")
        ),
        sa.ForeignKeyConstraint(
            ["composition_id"],
            ["compositions.id"],
            name=op.f("fk_processing_jobs_composition_id_compositions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processing_jobs")),
    )
    op.create_index(
        op.f("ix_processing_jobs_composition_id"),
        "processing_jobs",
        ["composition_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_processing_jobs_job_type"), "processing_jobs", ["job_type"], unique=False
    )
    op.create_index(op.f("ix_processing_jobs_status"), "processing_jobs", ["status"], unique=False)
    op.create_index(
        "ix_processing_jobs_composition_status",
        "processing_jobs",
        ["composition_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_processing_jobs_type_status", "processing_jobs", ["job_type", "status"], unique=False
    )
    op.create_index(
        "ix_processing_jobs_status_created_at",
        "processing_jobs",
        ["status", "created_at"],
        unique=False,
    )

    # Create trigger for processing_jobs
    op.execute(
        """
        CREATE TRIGGER update_processing_jobs_updated_at
        BEFORE UPDATE ON processing_jobs
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # Create job_metrics table
    op.create_table(
        "job_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("composition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("processing_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "metric_type",
            postgresql.ENUM(
                "processing_duration",
                "file_size",
                "bitrate",
                "frame_rate",
                "resolution",
                "queue_wait_time",
                "memory_usage",
                "cpu_usage",
                name="metric_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("metric_value", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("metric_unit", sa.String(length=50), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("metric_value >= 0", name=op.f("ck_job_metrics_value_positive")),
        sa.ForeignKeyConstraint(
            ["composition_id"],
            ["compositions.id"],
            name=op.f("fk_job_metrics_composition_id_compositions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processing_job_id"],
            ["processing_jobs.id"],
            name=op.f("fk_job_metrics_processing_job_id_processing_jobs"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_metrics")),
    )
    op.create_index(
        op.f("ix_job_metrics_composition_id"), "job_metrics", ["composition_id"], unique=False
    )
    op.create_index(
        op.f("ix_job_metrics_metric_type"), "job_metrics", ["metric_type"], unique=False
    )
    op.create_index(
        op.f("ix_job_metrics_processing_job_id"), "job_metrics", ["processing_job_id"], unique=False
    )
    op.create_index(
        op.f("ix_job_metrics_recorded_at"), "job_metrics", ["recorded_at"], unique=False
    )
    op.create_index(
        "ix_job_metrics_composition_type",
        "job_metrics",
        ["composition_id", "metric_type"],
        unique=False,
    )
    op.create_index(
        "ix_job_metrics_job_type", "job_metrics", ["processing_job_id", "metric_type"], unique=False
    )
    op.create_index(
        "ix_job_metrics_type_recorded", "job_metrics", ["metric_type", "recorded_at"], unique=False
    )

    # Create trigger for job_metrics
    op.execute(
        """
        CREATE TRIGGER update_job_metrics_updated_at
        BEFORE UPDATE ON job_metrics
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    """Drop all tables, triggers, and enums."""
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_job_metrics_updated_at ON job_metrics")
    op.execute("DROP TRIGGER IF EXISTS update_processing_jobs_updated_at ON processing_jobs")
    op.execute("DROP TRIGGER IF EXISTS update_compositions_updated_at ON compositions")

    # Drop tables (cascade will handle foreign keys)
    op.drop_table("job_metrics")
    op.drop_table("processing_jobs")
    op.drop_table("compositions")

    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS metric_type")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS job_type")
    op.execute("DROP TYPE IF EXISTS composition_status")
