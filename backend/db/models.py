from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    pass


class Series(Base):
    """Canonical TV series (one row per show)."""

    __tablename__ = "series"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    tmdb_tv_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # optional external id; not unique

    episodes: Mapped[list["Episode"]] = relationship(back_populates="series")
    characters: Mapped[list["Character"]] = relationship(back_populates="series")


class Episode(Base):
    """One row per episode; episode_id is the global join key (CSV, APIs, vector metadata)."""

    __tablename__ = "episode"
    __table_args__ = (
        UniqueConstraint("series_id", "season_number", "episode_number", name="uq_episode_series_season_ep"),
        UniqueConstraint("series_id", "tmdb_episode_id", name="uq_episode_series_tmdb_episode"),
        Index("ix_episode_series_id", "series_id"),
    )

    episode_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    series_id: Mapped[str] = mapped_column(String(128), ForeignKey("series.id", ondelete="CASCADE"))
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    overview: Mapped[str | None] = mapped_column(Text)
    air_date: Mapped[date | None] = mapped_column(Date)
    tmdb_episode_id: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    series: Mapped["Series"] = relationship(back_populates="episodes")
    episode_characters: Mapped[list["EpisodeCharacter"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )
    source_documents: Mapped[list["EpisodeSourceDocument"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )


class EpisodeSourceDocument(Base):
    """Cold storage for heavy scraped text (wiki narrative + optional unified JSON blob)."""

    __tablename__ = "episode_source_document"
    __table_args__ = (Index("ix_episode_source_document_episode_id", "episode_id"),)

    episode_id: Mapped[str] = mapped_column(
        String(256), ForeignKey("episode.episode_id", ondelete="CASCADE"), primary_key=True
    )
    source: Mapped[str] = mapped_column(String(32), primary_key=True)  # wiki | unified
    content: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    episode: Mapped["Episode"] = relationship(back_populates="source_documents")


class Character(Base):
    """Character scoped to a series (names can collide across shows). Optional tmdb_person_id for future linking."""

    __tablename__ = "character"
    __table_args__ = (
        UniqueConstraint("series_id", "tmdb_person_id", name="uq_character_series_tmdb_person"),
        Index("ix_character_series_id", "series_id"),
    )

    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    series_id: Mapped[str] = mapped_column(String(128), ForeignKey("series.id", ondelete="CASCADE"))
    display_name: Mapped[str] = mapped_column(String(512), nullable=False)
    tmdb_person_id: Mapped[int | None] = mapped_column(Integer)

    series: Mapped["Series"] = relationship(back_populates="characters")
    episode_links: Mapped[list["EpisodeCharacter"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class EpisodeCharacter(Base):
    """Many-to-many: which characters appear in an episode (authoritative for MVP lookups)."""

    __tablename__ = "episode_character"
    __table_args__ = (Index("ix_episode_character_character_id", "character_id"),)

    episode_id: Mapped[str] = mapped_column(
        String(256), ForeignKey("episode.episode_id", ondelete="CASCADE"), primary_key=True
    )
    character_id: Mapped[str] = mapped_column(
        String(256), ForeignKey("character.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="guest"
    )  # main, guest, background
    billing_order: Mapped[int | None] = mapped_column(Integer)
    credit_as: Mapped[str | None] = mapped_column(
        String(512)
    )  # character name as credited on this episode

    episode: Mapped["Episode"] = relationship(back_populates="episode_characters")
    character: Mapped["Character"] = relationship(back_populates="episode_links")
