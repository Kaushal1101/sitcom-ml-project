from __future__ import annotations

from dataclasses import dataclass

from backend.db.repositories import make_episode_id


@dataclass(frozen=True, slots=True)
class EpisodeRef:
    """Canonical episode identity for paths and joins.

    ``series_slug`` is a **project convention**: it should match the ``slug`` on the
    ``series`` row in SQLite (same string ``make_episode_id`` uses in ``episode_id``).
    It is a project convention (not an external API id); keep it stable so ``episode_id``
    stays aligned across scrapers, raw paths, and SQLite.
    """

    series_slug: str
    season_number: int
    episode_number: int
    wiki_origin: str  # e.g. https://theoffice.fandom.com
    wiki_page_title: str  # MediaWiki page title, e.g. The_Fire

    @property
    def episode_id(self) -> str:
        return make_episode_id(self.series_slug, self.season_number, self.episode_number)


# Pilot: The Office S02E04 — "The Fire" (Dunderpedia).
THE_OFFICE_S02E04 = EpisodeRef(
    series_slug="the_office",
    season_number=2,
    episode_number=4,
    wiki_origin="https://theoffice.fandom.com",
    wiki_page_title="The_Fire",
)

_EPISODE_REGISTRY: dict[str, EpisodeRef] = {
    THE_OFFICE_S02E04.episode_id: THE_OFFICE_S02E04,
}


def ref_for_episode_id(episode_id: str) -> EpisodeRef:
    """Resolve a registered ``EpisodeRef`` for ``episode_id`` (extend registry for new episodes)."""
    ref = _EPISODE_REGISTRY.get(episode_id)
    if ref is None:
        known = ", ".join(sorted(_EPISODE_REGISTRY)) or "(empty)"
        raise KeyError(
            f"No EpisodeRef registered for {episode_id!r}. Register it in episode_ref._EPISODE_REGISTRY. "
            f"Known: {known}"
        )
    return ref
