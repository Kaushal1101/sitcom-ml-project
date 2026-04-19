"""Concatenate episode DB fields + cold wiki/unified docs for embedding / RAG."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import Episode, EpisodeSourceDocument
from backend.db.repositories import SOURCE_UNIFIED, SOURCE_WIKI


def get_episode_source_document(
    session: Session, episode_id: str, source: str
) -> EpisodeSourceDocument | None:
    return session.execute(
        select(EpisodeSourceDocument).where(
            EpisodeSourceDocument.episode_id == episode_id,
            EpisodeSourceDocument.source == source,
        )
    ).scalar_one_or_none()


def episode_embedding_text(
    session: Session, episode_id: str, *, max_unified_chars: int = 120_000
) -> str:
    """Episode title/overview plus cold ``wiki`` (or truncated ``unified`` JSON)."""
    ep = session.get(Episode, episode_id)
    if ep is None:
        raise ValueError(f"Unknown episode_id={episode_id}")

    parts: list[str] = []
    if ep.title:
        parts.append(ep.title)
    if ep.overview:
        parts.append(ep.overview)

    wiki = get_episode_source_document(session, episode_id, SOURCE_WIKI)
    unified = get_episode_source_document(session, episode_id, SOURCE_UNIFIED)

    if wiki and wiki.content.strip():
        parts.append(wiki.content.strip())
    elif unified and unified.content.strip():
        u = unified.content.strip()
        if len(u) > max_unified_chars:
            u = u[:max_unified_chars] + "\n…[truncated]"
        parts.append(u)

    return "\n\n".join(parts)
