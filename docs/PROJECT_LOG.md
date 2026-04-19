# Project log (multi-agent)

Append-only session reports so agents and humans see **what changed**, **who** (role), and **how it was verified**. Newest entries at the **top**.

Do not put secrets or `.env` contents here.

---

## 2026-04-18 — Project admin

**Summary:** Repository sync to `origin`: Phase 1 wiki-first stack already described below (LangGraph `python -m backend.pipeline`, Dunderpedia runner, Alembic/SQLite, rules). Added **`project_admin.mdc`** requirement: read the newest sections of this file before any remote **push** so commits match verified agent work.

**Verification:** `git log -1 --oneline` after push; smoke checks in `AGENTS.md`.

---

## 2026-04-18 — Scraper (scraping logic)

**Summary:** Phase 1 pilot is **Dunderpedia-only** (The Office US Fandom wiki) via the MediaWiki **parse** API—same article HTML as the site, avoids Cloudflare issues on naive `/wiki/` fetches. Raw caches plus a **slim** `extracted_data.json` (wiki metadata, narrative plot/trivia/cast debug, social stub `not_used_wiki_only`) land under `data/raw/{episode_id}/` with `episode_id = make_episode_id(...)`. Scraping is invoked through **`run_scrape_for_ref`** in `backend/scraping/runner.py` (used by the LangGraph pipeline); there is no `python -m backend.scraping` entry.

**Changes:**

- **Provider + HTTP:** `DunderpediaWikiProvider` / `fetch_dunderpedia_article` in `backend/scraping/providers/wiki_fandom.py`; jitter + rotating User-Agents in `http_client.py`.
- **Unified JSON:** `build_extracted_data` in `backend/scraping/extracted_data.py` — metadata from wiki only (no TMDB placeholders); plot = Cold_open + Summary; `social.comments` empty with `social_status` for ingest compatibility.
- **Episode identity:** `EpisodeRef` + `_EPISODE_REGISTRY` / `ref_for_episode_id` in `episode_ref.py`; pilot `the_office_s02_e04` → wiki page `The_Fire`.
- **Raw artifacts per episode:** `wiki_parse_api.json`, `wiki_article_from_api.html`, `wiki_extracted.json`, `extracted_data.json`.
- **Cursor rules:** `scraping_rules.mdc` updated for runner vs pipeline CLI, registry, and `wiki_sqlite` boundary; `roadmap.mdc` / `project_context.mdc` aligned with wiki-first pipeline.

**Commands / verification:**

- `PYTHONPATH=. python -m backend.pipeline --skip-ingest` (scrape-only) or full `python -m backend.pipeline`
- `python -c "import json; print(json.load(open('data/raw/the_office_s02_e04/extracted_data.json')).keys())"`
- Spot-check `metadata.provenance.source == dunderpedia_fandom` and narrative section lengths in CLI/pipeline output

**Follow-ups:** Register more `EpisodeRef`s for new episodes; Reddit/TMDB sources and richer `social` when product scope expands; optional restore of a thin `python -m backend.scraping` wrapper around `runner` if a scrape-only CLI is desired outside the pipeline.

---

## 2026-04-18 — Database architect (storage)

**Summary:** Storage layer is wiki-first SQLite with a clear module map; Alembic history covers initial schema, cold text, and wiki-only series PK / nullable external ids. Cursor rules (`storage_rules.mdc`, `data_spec.mdc`) document `backend/ingestion/wiki_sqlite.py`, slim `repositories`, `character_repo`, `retrieval/embedding_text`, and the LangGraph pipeline entrypoint.

**Changes:**

- **Schema:** `series` uses `id = series_{slug}`; optional `tmdb_tv_id` (nullable, non-unique); `episode_source_document` holds `wiki` and `unified` slices per `episode_id`; cast remains `character` / `episode_character` for future enrichment.
- **Migrations:** `001_initial_schema` → `002_episode_source_document` → `003_wiki_only_series_tmdb_nullable` (legacy `tmdb_*` series ids renamed, `PRAGMA foreign_keys` around table rebuild, stale `reddit` doc rows removed).
- **Code map:** Core upserts and ID helpers in `backend/db/repositories.py`; cast helpers in `backend/db/character_repo.py`; `ingest_raw_dir` in `backend/ingestion/wiki_sqlite.py`; `episode_embedding_text` in `backend/retrieval/embedding_text.py`.
- **Docs:** `.cursor/rules/storage_rules.mdc` and `data_spec.mdc` updated with globs, stack note (no `chromadb`/`requests` in `pyproject.toml`), and `EpisodeRef` / `make_episode_id` alignment.

**Commands / verification:**

- `PYTHONPATH=. alembic upgrade head`
- `PYTHONPATH=. python -m backend.pipeline --skip-scrape` (after raw JSON exists) or full pipeline for registered `episode_id`
- `sqlite3 data/app.sqlite3 ".schema series"` and `SELECT id, slug FROM series LIMIT 3;`

**Follow-ups:** Optional cast ingestion from wiki text into `character_repo`; `episode_features` table if ranking columns outgrow `episode`.

---

## 2026-04-18 — Orchestrator / Platform

**Summary:** LangGraph pipeline is the canonical scrape → SQLite path; wiki-first ingestion and retrieval helpers are split under `backend/ingestion` and `backend/retrieval`.

**Changes:**

- `python -m backend.pipeline` runs Dunderpedia scrape then `ingest_raw_dir` into SQLite (`series`, `episode`, `episode_source_document`).
- Standalone `scripts/` ingestion CLIs removed; operational notes live in `AGENTS.md`.
- `backend/retrieval/embedding_text.py` holds `episode_embedding_text` for future vectors; `backend/db/repositories.py` trimmed to pipeline hot path.

**Commands / verification:**

- `alembic upgrade head`
- `python -m backend.pipeline`
- `sqlite3 data/app.sqlite3 "SELECT episode_id, title FROM episode;"`

**Follow-ups:** Register more episodes in `backend/scraping/episode_ref.py` when expanding beyond the pilot.

---

## Entry template (copy below the line for new sessions)

```markdown
## YYYY-MM-DD — <Agent role, e.g. Storage / Scraper / Orchestrator>

**Summary:**

**Changes:**

**Commands / verification:**

**Follow-ups:**

---
```
