# Agent Instructions & State

## Progress tracking (read this first)

| What | Where | Use it for |
|------|--------|------------|
| **Current snapshot** | This file (`AGENTS.md`) | Phase, active task, blockers, how to run — **update the section below** after substantive sessions. |
| **Full session history** | [docs/PROJECT_LOG.md](docs/PROJECT_LOG.md) | Append-only reports: what changed, which **role** (Scraper, Storage, Orchestrator, …), verification commands. **Newest entries at the top.** |

**How to use the log without huge context:** Open `docs/PROJECT_LOG.md` and read only the **first few `##` dated sections** (usually 1–3) for recent work. Load the whole file only when you need older history or archaeology. Do not put secrets or `.env` values in the log.

---

## Project Identity
Name: Mood-Moment Recommender
Lead Architect: [Your Name]
Core Mission: Semantic TV episode discovery via social & narrative signals.

## Current Project State (Update after every session)
- Phase: 1 (Initial Data Ingestion)
- Active Task: Phase 1 — **LangGraph pipeline** `python -m backend.pipeline` (scrape → ingest); ingest logic in `backend/ingestion/wiki_sqlite.py`; embedding text for future vectors in `backend/retrieval/embedding_text.py`
- Blockers: None

## How to run the pipeline

From the repo root (with `PYTHONPATH=.` or after `pip install -e .`):

```bash
python -m backend.pipeline
```

Use `--skip-scrape` or `--skip-ingest` for partial runs (e.g. scrape-only or ingest-only from existing `data/raw/{episode_id}/`). Default pilot episode unless you pass `--episode-id` or `--pilot`.

Apply DB schema with Alembic before first ingest if needed: `alembic upgrade head`.

## Agent Directives
1. **Source of Truth:** Always refer to `.cursor/rules/` for architectural logic.
2. **Context Scanning:** Before proposing changes, scan `master_dataset.csv` (if exists) to ensure schema compliance.
3. **Environment:** Use `.env` for local paths (e.g. `SQLITE_PATH`) and scraping options. Never hardcode secrets.
4. **Progress log:** After substantive work, append one new dated section to the **top** of [docs/PROJECT_LOG.md](docs/PROJECT_LOG.md) (heading like `## YYYY-MM-DD — Scraper` or `Storage`; use the template at the bottom of that file). Include summary, changes, verification, optional follow-ups. Then refresh **Current Project State** in this file. Keep long narratives in the log — do not paste full reports into `AGENTS.md`.
5. **Orchestrator:** See [.cursor/rules/orchestrator.mdc](.cursor/rules/orchestrator.mdc) for handoffs and ensuring log entries exist alongside `AGENTS.md` updates.
6. **Project admin (git / hygiene):** See [.cursor/rules/project_admin.mdc](.cursor/rules/project_admin.mdc) — remotes, `.gitignore`, releases/tags; not architecture.
