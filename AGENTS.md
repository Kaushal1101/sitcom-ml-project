# Agent Instructions & State

## Project Identity
Name: Mood-Moment Recommender
Lead Architect: [Your Name]
Core Mission: Semantic TV episode discovery via social & narrative signals.

## Current Project State (Update after every session)
- Phase: 1 (Initial Data Ingestion)
- Active Task: Finalizing TMDB Scraper
- Blockers: None

## Agent Directives
1. **Source of Truth:** Always refer to `.cursor/rules/` for architectural logic.
2. **Context Scanning:** Before proposing changes, scan `master_dataset.csv` (if exists) to ensure schema compliance.
3. **Environment:** Use `.env` for all API keys (TMDB, Reddit). Never hardcode.