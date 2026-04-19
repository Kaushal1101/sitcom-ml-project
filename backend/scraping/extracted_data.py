from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from backend.scraping.episode_ref import EpisodeRef
from backend.scraping.providers.wiki_fandom import WikiArticleResult

SOCIAL_WIKI_ONLY = "not_used_wiki_only"


def narrative_plot_text(sections: Mapping[str, str]) -> str:
    """Dunderpedia uses Cold_open + Summary instead of a heading named Plot."""
    cold = sections.get("Cold_open", "")
    summary = sections.get("Summary", "")
    parts = [p for p in (cold, summary) if p]
    return "\n\n".join(parts).strip()


def _parse_air_date_from_infobox(infobox_text: str | None) -> str | None:
    if not infobox_text:
        return None
    m = re.search(r"Airdate\s*\n?\s*([^\n]+)", infobox_text, re.IGNORECASE)
    if not m:
        return None
    s = m.group(1).strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def build_extracted_data(
    ref: EpisodeRef,
    wiki: WikiArticleResult,
    *,
    series_title: str = "The Office",
) -> dict[str, Any]:
    """
    Unified per-episode JSON for Dunderpedia-only runs: wiki metadata + narrative + social stub.

    ``episode_id`` matches ``data/raw/{episode_id}/`` and SQLite keys.
    """
    plot = narrative_plot_text(wiki.sections)
    trivia = wiki.sections.get("Trivia", "").strip()
    cast_text = wiki.sections.get("Cast", "").strip()
    air_date = _parse_air_date_from_infobox(wiki.infobox_text)

    metadata: dict[str, Any] = {
        "episode_id": ref.episode_id,
        "series_title": series_title,
        "series_slug": ref.series_slug,
        "episode_title": wiki.page_title,
        "season_number": ref.season_number,
        "episode_number": ref.episode_number,
        "air_date": air_date,
        "provenance": {
            "source": "dunderpedia_fandom",
            "episode_title": "wiki_parse_api",
            "air_date": "wiki_infobox" if air_date else "unknown",
        },
    }

    narrative: dict[str, Any] = {
        "plot": plot,
        "plot_sections_used": ["Cold_open", "Summary"],
        "trivia": trivia,
        "cast_text_debug": cast_text or None,
        "lede_text": wiki.lede_text,
    }

    social: dict[str, Any] = {
        "comments": [],
        "social_status": SOCIAL_WIKI_ONLY,
    }

    return {
        "episode_id": ref.episode_id,
        "metadata": metadata,
        "narrative": narrative,
        "social": social,
    }


def write_extracted_data(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
