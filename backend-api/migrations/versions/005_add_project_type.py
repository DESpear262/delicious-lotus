"""add project type

Revision ID: 005
Revises: 004
Create Date: 2025-11-22

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add project_type column to projects table."""
    op.add_column('projects', sa.Column('project_type', sa.String(length=50), server_default='custom', nullable=False))


def downgrade() -> None:
    """Remove project_type column."""
    op.drop_column('projects', 'project_type')
