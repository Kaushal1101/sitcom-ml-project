"""episode_source_document cold text table

Revision ID: 002
Revises: 001
Create Date: 2026-04-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "episode_source_document",
        sa.Column("episode_id", sa.String(length=256), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["episode_id"], ["episode.episode_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("episode_id", "source"),
    )
    op.create_index(
        "ix_episode_source_document_episode_id",
        "episode_source_document",
        ["episode_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_episode_source_document_episode_id", table_name="episode_source_document")
    op.drop_table("episode_source_document")
