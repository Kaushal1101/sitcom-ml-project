"""Character / cast queries — reserved for future cast ingestion (not used by wiki-only pipeline)."""
from __future__ import annotations

from sqlalchemy import nulls_last, select
from sqlalchemy.orm import Session

from backend.db.models import Character, Episode, EpisodeCharacter


def upsert_character(
    session: Session,
    *,
    character_id: str,
    series_id: str,
    display_name: str,
    tmdb_person_id: int | None,
) -> Character:
    row = session.get(Character, character_id)
    if row is None:
        row = Character(
            id=character_id,
            series_id=series_id,
            display_name=display_name,
            tmdb_person_id=tmdb_person_id,
        )
        session.add(row)
    else:
        row.display_name = display_name
        if tmdb_person_id is not None:
            row.tmdb_person_id = tmdb_person_id
    return row


def list_episodes_for_character(session: Session, character_id: str) -> list[Episode]:
    q = (
        select(Episode)
        .join(EpisodeCharacter, EpisodeCharacter.episode_id == Episode.episode_id)
        .where(EpisodeCharacter.character_id == character_id)
        .order_by(Episode.season_number, Episode.episode_number)
    )
    return list(session.scalars(q).unique().all())


def find_character_ids_by_display_name(
    session: Session, series_id: str, name_substring: str
) -> list[str]:
    q = select(Character.id).where(
        Character.series_id == series_id,
        Character.display_name.ilike(f"%{name_substring}%"),
    )
    return list(session.scalars(q).all())


def list_character_display_names_for_episode(session: Session, episode_id: str) -> list[str]:
    q = (
        select(Character.display_name)
        .join(EpisodeCharacter, EpisodeCharacter.character_id == Character.id)
        .where(EpisodeCharacter.episode_id == episode_id)
        .order_by(nulls_last(EpisodeCharacter.billing_order), Character.display_name)
    )
    return list(session.scalars(q).all())
