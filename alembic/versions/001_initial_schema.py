"""initial schema: series, episode, character, episode_character

Revision ID: 001
Revises:
Create Date: 2026-04-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "series",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("tmdb_tv_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.UniqueConstraint("tmdb_tv_id"),
    )
    op.create_index("ix_series_slug", "series", ["slug"], unique=False)

    op.create_table(
        "episode",
        sa.Column("episode_id", sa.String(length=256), nullable=False),
        sa.Column("series_id", sa.String(length=128), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("air_date", sa.Date(), nullable=True),
        sa.Column("tmdb_episode_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("episode_id"),
        sa.UniqueConstraint("series_id", "season_number", "episode_number", name="uq_episode_series_season_ep"),
        sa.UniqueConstraint("series_id", "tmdb_episode_id", name="uq_episode_series_tmdb_episode"),
    )
    op.create_index("ix_episode_series_id", "episode", ["series_id"], unique=False)

    op.create_table(
        "character",
        sa.Column("id", sa.String(length=256), nullable=False),
        sa.Column("series_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("tmdb_person_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["series_id"], ["series.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("series_id", "tmdb_person_id", name="uq_character_series_tmdb_person"),
    )
    op.create_index("ix_character_series_id", "character", ["series_id"], unique=False)

    op.create_table(
        "episode_character",
        sa.Column("episode_id", sa.String(length=256), nullable=False),
        sa.Column("character_id", sa.String(length=256), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("billing_order", sa.Integer(), nullable=True),
        sa.Column("credit_as", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["character.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["episode_id"], ["episode.episode_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("episode_id", "character_id"),
    )
    op.create_index(
        "ix_episode_character_character_id", "episode_character", ["character_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_episode_character_character_id", table_name="episode_character")
    op.drop_table("episode_character")
    op.drop_index("ix_character_series_id", table_name="character")
    op.drop_table("character")
    op.drop_index("ix_episode_series_id", table_name="episode")
    op.drop_table("episode")
    op.drop_index("ix_series_slug", table_name="series")
    op.drop_table("series")
