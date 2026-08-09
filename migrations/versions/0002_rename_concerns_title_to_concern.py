"""rename concerns.title to concerns.concern

Revision ID: 0002_rename_concern
Revises: 0001_initial
Create Date: 2026-08-09

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_rename_concern"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("concerns", "title", new_column_name="concern")


def downgrade() -> None:
    op.alter_column("concerns", "concern", new_column_name="title")
