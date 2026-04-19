"""wiki-only series id pattern; tmdb_tv_id nullable without unique

Revision ID: 003
Revises: 002
Create Date: 2026-04-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Rename legacy tmdb_{id} series PKs to series_{slug} and fix FKs
    rows = conn.execute(sa.text("SELECT id, slug FROM series WHERE id LIKE 'tmdb_%'")).fetchall()
    for old_id, slug in rows:
        if not slug:
            continue
        new_id = f"series_{slug}"
        conn.execute(
            sa.text("UPDATE episode SET series_id = :new_id WHERE series_id = :old_id"),
            {"new_id": new_id, "old_id": old_id},
        )
        conn.execute(
            sa.text("UPDATE character SET series_id = :new_id WHERE series_id = :old_id"),
            {"new_id": new_id, "old_id": old_id},
        )
        conn.execute(
            sa.text("UPDATE series SET id = :new_id WHERE id = :old_id"),
            {"new_id": new_id, "old_id": old_id},
        )

    # Rebuild series: drop UNIQUE(tmdb_tv_id), allow NULL (SQLite has no ALTER DROP CONSTRAINT)
    conn.execute(
        sa.text("""
        CREATE TABLE series_new (
            id VARCHAR(128) NOT NULL,
            slug VARCHAR(128) NOT NULL,
            title VARCHAR(512) NOT NULL,
            tmdb_tv_id INTEGER,
            PRIMARY KEY (id),
            CONSTRAINT uq_series_slug UNIQUE (slug)
        )
    """)
    )
    conn.execute(
        sa.text("""
        INSERT INTO series_new (id, slug, title, tmdb_tv_id)
        SELECT id, slug, title, tmdb_tv_id FROM series
    """)
    )
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
    conn.execute(sa.text("DROP TABLE series"))
    conn.execute(sa.text("ALTER TABLE series_new RENAME TO series"))
    conn.execute(sa.text("PRAGMA foreign_keys=ON"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_series_slug ON series (slug)"))
    conn.execute(sa.text("DELETE FROM episode_source_document WHERE source = 'reddit'"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        CREATE TABLE series_old (
            id VARCHAR(128) NOT NULL,
            slug VARCHAR(128) NOT NULL,
            title VARCHAR(512) NOT NULL,
            tmdb_tv_id INTEGER NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT uq_series_slug UNIQUE (slug),
            CONSTRAINT uq_series_tmdb_tv_id UNIQUE (tmdb_tv_id)
        )
    """)
    )
    conn.execute(
        sa.text("""
        INSERT INTO series_old (id, slug, title, tmdb_tv_id)
        SELECT id, slug, title, COALESCE(tmdb_tv_id, 0) FROM series
    """)
    )
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
    conn.execute(sa.text("DROP TABLE series"))
    conn.execute(sa.text("ALTER TABLE series_old RENAME TO series"))
    conn.execute(sa.text("PRAGMA foreign_keys=ON"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_series_slug ON series (slug)"))
