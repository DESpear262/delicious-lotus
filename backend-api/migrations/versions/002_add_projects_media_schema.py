"""add projects media schema with users folders and job tracking

Revision ID: 002
Revises: 001
Create Date: 2025-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add users, projects, folders, media_assets, and job tracking tables."""

    # Create enum types for media and job statuses
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE media_type AS ENUM ('video', 'audio', 'image'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE export_job_status AS ENUM ('pending', 'queued', 'processing', 'completed', 'failed', 'cancelled'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE ai_job_type AS ENUM ('text_to_video', 'image_to_video', 'audio_generation'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE ai_job_status AS ENUM ('pending', 'queued', 'processing', 'completed', 'failed', 'cancelled'); "
        "EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    # Subtask 14.1: Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_created_at"), "users", ["created_at"], unique=False)

    # Create trigger for users
    op.execute(
        """
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # Subtask 14.2: Create projects table
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("last_modified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name=op.f("fk_projects_owner_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
    )
    op.create_index(op.f("ix_projects_owner_user_id"), "projects", ["owner_user_id"], unique=False)
    op.create_index(op.f("ix_projects_created_at"), "projects", ["created_at"], unique=False)

    # Create trigger for projects
    op.execute(
        """
        CREATE TRIGGER update_projects_updated_at
        BEFORE UPDATE ON projects
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # Subtask 14.2: Create folders table with hierarchical structure
    op.create_table(
        "folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name=op.f("fk_folders_owner_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["folders.id"],
            name=op.f("fk_folders_parent_id_folders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_folders")),
    )
    op.create_index(op.f("ix_folders_owner_user_id"), "folders", ["owner_user_id"], unique=False)
    op.create_index(op.f("ix_folders_parent_id"), "folders", ["parent_id"], unique=False)
    op.create_index(op.f("ix_folders_created_at"), "folders", ["created_at"], unique=False)

    # Create trigger for folders
    op.execute(
        """
        CREATE TRIGGER update_folders_updated_at
        BEFORE UPDATE ON folders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # Subtask 14.3: Create media_assets table with comprehensive metadata
    # Create media_asset_type and media_asset_status enums
    op.execute("CREATE TYPE media_asset_type AS ENUM ('image', 'video', 'audio');")
    op.execute("CREATE TYPE media_asset_status AS ENUM ('pending_upload', 'uploading', 'ready', 'failed', 'deleted');")

    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column(
            "file_type",
            postgresql.ENUM(
                "image",
                "video",
                "audio",
                name="media_asset_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("s3_key", sa.String(length=1024), nullable=False, unique=True),
        sa.Column("thumbnail_s3_key", sa.String(length=1024), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending_upload",
                "uploading",
                "ready",
                "failed",
                "deleted",
                name="media_asset_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending_upload",
        ),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("file_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_media_assets_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["folders.id"],
            name=op.f("fk_media_assets_folder_id_folders"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_media_assets")),
        sa.CheckConstraint("file_size > 0", name=op.f("ck_media_assets_file_size_positive")),
    )
    op.create_index(op.f("ix_media_assets_user_id"), "media_assets", ["user_id"], unique=False)
    op.create_index(op.f("ix_media_assets_file_type"), "media_assets", ["file_type"], unique=False)
    op.create_index(op.f("ix_media_assets_status"), "media_assets", ["status"], unique=False)
    op.create_index(op.f("ix_media_assets_folder_id"), "media_assets", ["folder_id"], unique=False)
    op.create_index(op.f("ix_media_assets_is_deleted"), "media_assets", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_media_assets_created_at"), "media_assets", ["created_at"], unique=False)
    op.create_index(
        "ix_media_assets_file_metadata",
        "media_assets",
        ["file_metadata"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_media_assets_tags",
        "media_assets",
        ["tags"],
        unique=False,
        postgresql_using="gin",
    )
    # Composite indexes
    op.create_index("ix_media_assets_user_type", "media_assets", ["user_id", "file_type"], unique=False)
    op.create_index("ix_media_assets_user_status", "media_assets", ["user_id", "status"], unique=False)
    op.create_index("ix_media_assets_user_deleted", "media_assets", ["user_id", "is_deleted"], unique=False)
    op.create_index("ix_media_assets_folder_deleted", "media_assets", ["folder_id", "is_deleted"], unique=False)
    op.create_index("ix_media_assets_status_created", "media_assets", ["status", "created_at"], unique=False)

    # Create trigger for media_assets
    op.execute(
        """
        CREATE TRIGGER update_media_assets_updated_at
        BEFORE UPDATE ON media_assets
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # Subtask 14.4: Create export_jobs table
    op.create_table(
        "export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("composition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "queued",
                "processing",
                "completed",
                "failed",
                "cancelled",
                name="export_job_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("download_url", sa.String(length=1024), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
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
        sa.CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name=op.f("ck_export_jobs_progress_range"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_export_jobs_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["composition_id"],
            ["compositions.id"],
            name=op.f("fk_export_jobs_composition_id_compositions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_jobs")),
    )
    op.create_index(op.f("ix_export_jobs_project_id"), "export_jobs", ["project_id"], unique=False)
    op.create_index(op.f("ix_export_jobs_composition_id"), "export_jobs", ["composition_id"], unique=False)
    op.create_index(op.f("ix_export_jobs_status"), "export_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_export_jobs_created_at"), "export_jobs", ["created_at"], unique=False)
    op.create_index(
        "ix_export_jobs_settings",
        "export_jobs",
        ["settings"],
        unique=False,
        postgresql_using="gin",
    )

    # Create trigger for export_jobs
    op.execute(
        """
        CREATE TRIGGER update_export_jobs_updated_at
        BEFORE UPDATE ON export_jobs
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # Subtask 14.4: Create ai_generation_jobs table
    op.create_table(
        "ai_generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_type",
            postgresql.ENUM(
                "text_to_video",
                "image_to_video",
                "audio_generation",
                name="ai_job_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "queued",
                "processing",
                "completed",
                "failed",
                "cancelled",
                name="ai_job_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name=op.f("fk_ai_generation_jobs_owner_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["media_asset_id"],
            ["media_assets.id"],
            name=op.f("fk_ai_generation_jobs_media_asset_id_media_assets"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_generation_jobs")),
    )
    op.create_index(op.f("ix_ai_generation_jobs_owner_user_id"), "ai_generation_jobs", ["owner_user_id"], unique=False)
    op.create_index(op.f("ix_ai_generation_jobs_job_type"), "ai_generation_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_ai_generation_jobs_status"), "ai_generation_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_ai_generation_jobs_created_at"), "ai_generation_jobs", ["created_at"], unique=False)
    op.create_index(
        "ix_ai_generation_jobs_settings",
        "ai_generation_jobs",
        ["settings"],
        unique=False,
        postgresql_using="gin",
    )

    # Create trigger for ai_generation_jobs
    op.execute(
        """
        CREATE TRIGGER update_ai_generation_jobs_updated_at
        BEFORE UPDATE ON ai_generation_jobs
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # Subtask 14.5: Update compositions table with new columns
    op.add_column("compositions", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("compositions", sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("compositions", sa.Column("aspect_ratio", sa.String(length=20), nullable=True))
    op.add_column("compositions", sa.Column("timebase_fps", sa.Integer(), server_default="30", nullable=False))

    # Add foreign key constraints for new columns
    op.create_foreign_key(
        op.f("fk_compositions_project_id_projects"),
        "compositions",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_compositions_owner_user_id_users"),
        "compositions",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add indexes for new foreign key columns
    op.create_index(op.f("ix_compositions_project_id"), "compositions", ["project_id"], unique=False)
    op.create_index(op.f("ix_compositions_owner_user_id"), "compositions", ["owner_user_id"], unique=False)


def downgrade() -> None:
    """Remove all tables and columns added in this migration."""

    # Drop indexes on compositions new columns
    op.drop_index(op.f("ix_compositions_owner_user_id"), table_name="compositions")
    op.drop_index(op.f("ix_compositions_project_id"), table_name="compositions")

    # Drop foreign key constraints from compositions
    op.drop_constraint(op.f("fk_compositions_owner_user_id_users"), "compositions", type_="foreignkey")
    op.drop_constraint(op.f("fk_compositions_project_id_projects"), "compositions", type_="foreignkey")

    # Drop new columns from compositions
    op.drop_column("compositions", "timebase_fps")
    op.drop_column("compositions", "aspect_ratio")
    op.drop_column("compositions", "owner_user_id")
    op.drop_column("compositions", "project_id")

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_ai_generation_jobs_updated_at ON ai_generation_jobs")
    op.execute("DROP TRIGGER IF EXISTS update_export_jobs_updated_at ON export_jobs")
    op.execute("DROP TRIGGER IF EXISTS update_media_assets_updated_at ON media_assets")
    op.execute("DROP TRIGGER IF EXISTS update_folders_updated_at ON folders")
    op.execute("DROP TRIGGER IF EXISTS update_projects_updated_at ON projects")
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")

    # Drop tables in reverse dependency order
    op.drop_table("ai_generation_jobs")
    op.drop_table("export_jobs")
    op.drop_table("media_assets")
    op.drop_table("folders")
    op.drop_table("projects")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS ai_job_status")
    op.execute("DROP TYPE IF EXISTS ai_job_type")
    op.execute("DROP TYPE IF EXISTS export_job_status")
    op.execute("DROP TYPE IF EXISTS media_type")
