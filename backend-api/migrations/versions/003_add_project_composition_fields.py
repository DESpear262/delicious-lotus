"""add project composition relationship fields

Revision ID: 003
Revises: 002
Create Date: 2025-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add project fields for composition relationship, aspect ratio, timebase, and soft delete."""

    # Add new columns to projects table
    op.add_column("projects", sa.Column("aspect_ratio", sa.String(length=20), nullable=False, server_default="16:9"))
    op.add_column("projects", sa.Column("timebase_fps", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("projects", sa.Column("composition_id", postgresql.UUID(as_uuid=True), nullable=True, unique=True))
    op.add_column("projects", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"))

    # Add foreign key constraint for composition_id
    op.create_foreign_key(
        op.f("fk_projects_composition_id_compositions"),
        "projects",
        "compositions",
        ["composition_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add index for soft delete filtering
    op.create_index(op.f("ix_projects_is_deleted"), "projects", ["is_deleted"], unique=False)

    # Add index for last_modified_at for sorting
    op.create_index(op.f("ix_projects_last_modified_at"), "projects", ["last_modified_at"], unique=False)

    # Add composite indexes for common query patterns
    op.create_index(
        "ix_projects_owner_deleted_modified",
        "projects",
        ["owner_user_id", "is_deleted", "last_modified_at"],
        unique=False,
    )
    op.create_index(
        "ix_projects_owner_deleted_created",
        "projects",
        ["owner_user_id", "is_deleted", "created_at"],
        unique=False,
    )

    # Rename owner_user_id to user_id for consistency (optional, but matches task spec)
    op.alter_column("projects", "owner_user_id", new_column_name="user_id")

    # Update foreign key constraint name after column rename
    op.drop_constraint("fk_projects_owner_user_id_users", "projects", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_projects_user_id_users"),
        "projects",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop old index and create new one with renamed column
    op.drop_index("ix_projects_owner_user_id", table_name="projects")
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)


def downgrade() -> None:
    """Remove project composition relationship fields."""

    # Drop indexes
    op.drop_index("ix_projects_owner_deleted_created", table_name="projects")
    op.drop_index("ix_projects_owner_deleted_modified", table_name="projects")
    op.drop_index(op.f("ix_projects_last_modified_at"), table_name="projects")
    op.drop_index(op.f("ix_projects_is_deleted"), table_name="projects")

    # Drop foreign key constraint
    op.drop_constraint(op.f("fk_projects_composition_id_compositions"), "projects", type_="foreignkey")

    # Drop new columns
    op.drop_column("projects", "is_deleted")
    op.drop_column("projects", "composition_id")
    op.drop_column("projects", "timebase_fps")
    op.drop_column("projects", "aspect_ratio")

    # Rename user_id back to owner_user_id
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_constraint(op.f("fk_projects_user_id_users"), "projects", type_="foreignkey")

    op.alter_column("projects", "user_id", new_column_name="owner_user_id")

    op.create_foreign_key(
        "fk_projects_owner_user_id_users",
        "projects",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_projects_owner_user_id", "projects", ["owner_user_id"], unique=False)
