"""Wiki-first SQLite ingestion (from scraped JSON on disk)."""

from backend.ingestion.wiki_sqlite import ingest_raw_dir

__all__ = ["ingest_raw_dir"]
