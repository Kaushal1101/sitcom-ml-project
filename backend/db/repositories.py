from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import Episode, EpisodeSourceDocument, Series

SOURCE_WIKI = "wiki"
SOURCE_UNIFIED = "unified"


def series_id_wiki(series_slug: str) -> str:
    """Stable series PK for wiki-first ingestion: ``series_{slug}``."""
    return f"series_{series_slug}"


def make_episode_id(series_slug: str, season: int, episode: int) -> str:
    return f"{series_slug}_s{season:02d}_e{episode:02d}"


def parse_episode_id(episode_id: str) -> tuple[str, int, int] | None:
    """Parse ``{slug}_s{season}_e{episode}`` into slug, season, episode number."""
    m = re.match(r"^(.+)_s(\d+)_e(\d+)$", episode_id)
    if not m:
        return None
    return m.group(1), int(m.group(2)), int(m.group(3))


def upsert_series(
    session: Session,
    *,
    series_id: str,
    slug: str,
    title: str,
    tmdb_tv_id: int | None = None,
) -> Series:
    row = session.get(Series, series_id)
    if row is None:
        row = Series(id=series_id, slug=slug, title=title, tmdb_tv_id=tmdb_tv_id)
        session.add(row)
    else:
        row.slug = slug
        row.title = title
        if tmdb_tv_id is not None:
            row.tmdb_tv_id = tmdb_tv_id
    return row


def upsert_episode(
    session: Session,
    *,
    episode_id: str,
    series_id: str,
    season_number: int,
    episode_number: int,
    patch: Mapping[str, Any] | None = None,
) -> Episode:
    """Insert or update an episode. Only keys present in ``patch`` with non-None values are applied."""
    patch = patch or {}
    row = session.get(Episode, episode_id)
    now = datetime.utcnow()
    if row is None:
        row = Episode(
            episode_id=episode_id,
            series_id=series_id,
            season_number=season_number,
            episode_number=episode_number,
            created_at=now,
            updated_at=now,
        )
        session.add(row)

    for key in ("title", "overview", "air_date", "tmdb_episode_id"):
        if key not in patch:
            continue
        val = patch[key]
        if val is None:
            continue
        if key == "air_date" and isinstance(val, str):
            val = date.fromisoformat(val)
        setattr(row, key, val)

    row.updated_at = now
    return row


def upsert_episode_source_document(
    session: Session,
    *,
    episode_id: str,
    source: str,
    content: str,
) -> EpisodeSourceDocument:
    """Idempotent upsert for one (episode_id, source) slice; does not touch ``episode`` core columns."""
    now = datetime.utcnow()
    row = session.execute(
        select(EpisodeSourceDocument).where(
            EpisodeSourceDocument.episode_id == episode_id,
            EpisodeSourceDocument.source == source,
        )
    ).scalar_one_or_none()
    if row is None:
        row = EpisodeSourceDocument(
            episode_id=episode_id, source=source, content=content, updated_at=now
        )
        session.add(row)
    else:
        row.content = content
        row.updated_at = now
    return row
