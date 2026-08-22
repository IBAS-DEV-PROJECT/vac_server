"""add concerns.topic_other

Revision ID: 0003_topic_other
Revises: 0002_rename_concern
Create Date: 2026-08-22

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_topic_other"
down_revision: str | None = "0002_rename_concern"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "concerns", sa.Column("topic_other", sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("concerns", "topic_other")
