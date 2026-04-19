"""Scrape one episode to data/raw/{episode_id}/ (Dunderpedia)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.scraping.episode_ref import EpisodeRef
from backend.scraping.extracted_data import (
    build_extracted_data,
    narrative_plot_text,
    write_extracted_data,
)
from backend.scraping.providers.wiki_fandom import DunderpediaWikiProvider


def run_scrape_for_ref(ref: EpisodeRef, data_root: Path) -> dict[str, Any]:
    """
    Fetch wiki article, write raw caches + extracted_data.json under ``data_root / ref.episode_id``.

    Returns a JSON-friendly summary dict (suitable for LangGraph state).
    """
    provider = DunderpediaWikiProvider(data_root=data_root)
    result = provider.fetch_episode(ref)

    extracted = build_extracted_data(ref, result)
    out_dir = data_root / ref.episode_id
    extracted_path = out_dir / "extracted_data.json"
    write_extracted_data(extracted_path, extracted)

    plot = narrative_plot_text(result.sections)
    trivia = result.sections.get("Trivia", "")
    cast = result.sections.get("Cast", "")

    return {
        "episode_id": ref.episode_id,
        "wiki_page": result.page_title,
        "output_dir": str(out_dir),
        "extracted_data": str(extracted_path),
        "files_written": [
            str(out_dir / "wiki_parse_api.json"),
            str(out_dir / "wiki_article_from_api.html"),
            str(out_dir / "wiki_extracted.json"),
            str(extracted_path),
        ],
        "api_url": result.api_url,
        "evidence": {
            "narrative_plot_char_count": len(plot),
            "narrative_trivia_char_count": len(trivia),
        },
        "section_ids": list(result.sections.keys()),
        "previews": {
            "plot": plot[:1200] + ("…" if len(plot) > 1200 else ""),
            "trivia": trivia[:800] + ("…" if len(trivia) > 800 else ""),
            "cast": cast[:800] + ("…" if len(cast) > 800 else ""),
        },
    }
