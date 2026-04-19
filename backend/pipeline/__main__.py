"""CLI: LangGraph pipeline (scrape → ingest)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from backend.pipeline.graph import run_pipeline
from backend.scraping.episode_ref import THE_OFFICE_S02E04


def main() -> int:
    load_dotenv()
    project_root = Path(__file__).resolve().parents[2]

    p = argparse.ArgumentParser(description="Run wiki scrape → SQLite ingest (LangGraph)")
    p.add_argument(
        "--episode-id",
        default=None,
        help=f"Canonical episode id (default: pilot {THE_OFFICE_S02E04.episode_id})",
    )
    p.add_argument("--pilot", action="store_true", help=f"Same as --episode-id {THE_OFFICE_S02E04.episode_id}")
    p.add_argument("--skip-scrape", action="store_true", help="Only run ingest (raw JSON must exist)")
    p.add_argument("--skip-ingest", action="store_true", help="Only run scrape")
    p.add_argument("--json", action="store_true", help="Print final state as JSON")
    args = p.parse_args()

    if args.pilot and args.episode_id:
        print("Use either --pilot or --episode-id, not both.", file=sys.stderr)
        return 2

    episode_id = THE_OFFICE_S02E04.episode_id if args.pilot else args.episode_id
    if not episode_id:
        episode_id = THE_OFFICE_S02E04.episode_id

    try:
        out = run_pipeline(
            episode_id=episode_id,
            project_root=project_root,
            skip_scrape=args.skip_scrape,
            skip_ingest=args.skip_ingest,
        )
    except KeyError as e:
        print(e, file=sys.stderr)
        return 2
    except Exception as e:
        print(f"pipeline failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(dict(out), indent=2, default=str))
    else:
        print(f"episode_id={out.get('episode_id')}")
        if out.get("scrape_summary"):
            print("scrape: ok")
            ss = out["scrape_summary"]
            if isinstance(ss, dict) and ss.get("evidence"):
                print(f"  narrative evidence: {ss['evidence']}")
        elif args.skip_scrape:
            print("scrape: skipped")
        if out.get("ingest_summary"):
            print("ingest:", out["ingest_summary"])
        elif args.skip_ingest:
            print("ingest: skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
