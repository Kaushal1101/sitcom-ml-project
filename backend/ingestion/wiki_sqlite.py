"""Load wiki / unified JSON from data/raw/{episode_id}/ into SQLite."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.db.repositories import (
    SOURCE_UNIFIED,
    SOURCE_WIKI,
    parse_episode_id,
    series_id_wiki,
    upsert_episode,
    upsert_episode_source_document,
    upsert_series,
)
from backend.db.session import session_scope


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _wiki_text_from_extracted_data(data: dict[str, Any]) -> str:
    n = data.get("narrative") or {}
    parts: list[str] = []
    if n.get("plot"):
        parts.append("## Plot\n" + str(n["plot"]).strip())
    if n.get("trivia"):
        parts.append("## Trivia\n" + str(n["trivia"]).strip())
    if n.get("lede_text"):
        parts.append("## Lede\n" + str(n["lede_text"]).strip())
    if n.get("cast_text_debug"):
        parts.append("## Cast (wiki)\n" + str(n["cast_text_debug"]).strip())
    return "\n\n".join(parts)


def _wiki_text_from_wiki_extracted(data: dict[str, Any]) -> str:
    parts: list[str] = []
    if data.get("lede_text"):
        parts.append("## Lede\n" + str(data["lede_text"]).strip())
    if data.get("infobox_text"):
        parts.append("## Infobox\n" + str(data["infobox_text"]).strip())
    sections = data.get("sections") or {}
    for name, body in sections.items():
        parts.append(f"## {name}\n{str(body).strip()}")
    return "\n\n".join(parts)


def _coerce_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _upsert_core_from_extracted(session: Session, episode_id: str, data: dict[str, Any]) -> None:
    meta = data.get("metadata") or {}
    slug = meta.get("series_slug")
    if not slug:
        raise ValueError("extracted_data.json: missing metadata.series_slug")
    sid = series_id_wiki(str(slug))
    series_title = meta.get("series_title") or str(slug).replace("_", " ").title()
    tmdb_tv = _coerce_int(meta.get("tmdb_tv_id"))
    upsert_series(session, series_id=sid, slug=str(slug), title=str(series_title), tmdb_tv_id=tmdb_tv)

    season = _coerce_int(meta.get("season_number"))
    epnum = _coerce_int(meta.get("episode_number"))
    if season is None or epnum is None:
        raise ValueError("extracted_data.json: metadata needs season_number and episode_number")

    patch: dict[str, Any] = {}
    if meta.get("episode_title"):
        patch["title"] = meta["episode_title"]
    if meta.get("air_date"):
        patch["air_date"] = meta["air_date"]
    teid = _coerce_int(meta.get("tmdb_episode_id"))
    if teid is not None:
        patch["tmdb_episode_id"] = teid

    upsert_episode(
        session,
        episode_id=episode_id,
        series_id=sid,
        season_number=season,
        episode_number=epnum,
        patch=patch,
    )


def _upsert_core_from_wiki_extracted(session: Session, episode_id: str, data: dict[str, Any]) -> None:
    parsed = parse_episode_id(episode_id)
    if not parsed:
        raise ValueError(
            f"episode_id {episode_id!r} must look like '{{slug}}_s{{season}}_e{{episode}}' "
            "when using wiki_extracted.json without extracted_data.json metadata."
        )
    slug, season, epnum = parsed
    sid = series_id_wiki(slug)
    series_title = slug.replace("_", " ").title()
    upsert_series(session, series_id=sid, slug=slug, title=series_title, tmdb_tv_id=None)

    patch: dict[str, Any] = {}
    if data.get("page_title"):
        patch["title"] = data["page_title"]
    if data.get("lede_text"):
        lede = str(data["lede_text"]).strip()
        patch["overview"] = lede[:8000] if len(lede) > 8000 else lede

    upsert_episode(
        session,
        episode_id=episode_id,
        series_id=sid,
        season_number=season,
        episode_number=epnum,
        patch=patch,
    )


def ingest_raw_dir(episode_id: str, raw_dir: Path) -> dict[str, str]:
    """Upsert series, episode, and document rows; returns summary of sources written."""
    extracted_path = raw_dir / "extracted_data.json"
    wiki_path = raw_dir / "wiki_extracted.json"

    if not extracted_path.is_file() and not wiki_path.is_file():
        raise FileNotFoundError(
            f"No extracted_data.json or wiki_extracted.json under {raw_dir}"
        )

    written: dict[str, str] = {}

    with session_scope() as session:
        if extracted_path.is_file():
            data = _read_json(extracted_path)
            eid = data.get("episode_id")
            if eid and eid != episode_id:
                raise ValueError(
                    f"extracted_data.json episode_id {eid!r} does not match episode_id {episode_id!r}"
                )
            _upsert_core_from_extracted(session, episode_id, data)

            wiki_body = _wiki_text_from_extracted_data(data)
            if wiki_body.strip():
                upsert_episode_source_document(
                    session, episode_id=episode_id, source=SOURCE_WIKI, content=wiki_body
                )
                written[SOURCE_WIKI] = f"{len(wiki_body)} chars"

            unified_body = json.dumps(data, ensure_ascii=False, indent=2)
            upsert_episode_source_document(
                session, episode_id=episode_id, source=SOURCE_UNIFIED, content=unified_body
            )
            written[SOURCE_UNIFIED] = f"{len(unified_body)} chars"

        else:
            data = _read_json(wiki_path)
            eid = data.get("episode_id")
            if eid and eid != episode_id:
                raise ValueError(
                    f"wiki_extracted.json episode_id {eid!r} does not match episode_id {episode_id!r}"
                )
            _upsert_core_from_wiki_extracted(session, episode_id, data)

            wiki_body = _wiki_text_from_wiki_extracted(data)
            if not wiki_body.strip():
                raise ValueError(f"Empty wiki body after parsing {wiki_path}")
            upsert_episode_source_document(
                session, episode_id=episode_id, source=SOURCE_WIKI, content=wiki_body
            )
            written[SOURCE_WIKI] = f"{len(wiki_body)} chars"

    return written
