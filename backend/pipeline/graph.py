"""LangGraph: linear scrape → ingest for one episode."""
from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.ingestion.wiki_sqlite import ingest_raw_dir
from backend.scraping.episode_ref import ref_for_episode_id
from backend.scraping.runner import run_scrape_for_ref


class PipelineState(TypedDict, total=False):
    """Graph state passed between nodes (merged by LangGraph)."""

    episode_id: str
    project_root: str
    skip_scrape: bool
    skip_ingest: bool
    scrape_summary: dict[str, Any]
    ingest_summary: dict[str, str]


def _node_scrape(state: PipelineState) -> dict[str, Any]:
    if state.get("skip_scrape"):
        return {}
    root = Path(state["project_root"])
    ref = ref_for_episode_id(state["episode_id"])
    data_root = root / "data" / "raw"
    summary = run_scrape_for_ref(ref, data_root)
    # Drop large previews from state to keep checkpoints small
    slim = {k: v for k, v in summary.items() if k != "previews"}
    return {"scrape_summary": slim}


def _node_ingest(state: PipelineState) -> dict[str, Any]:
    if state.get("skip_ingest"):
        return {}
    root = Path(state["project_root"])
    episode_id = state["episode_id"]
    raw_dir = root / "data" / "raw" / episode_id
    written = ingest_raw_dir(episode_id, raw_dir)
    return {"ingest_summary": written}


def build_pipeline_graph():
    g = StateGraph(PipelineState)
    g.add_node("scrape", _node_scrape)
    g.add_node("ingest", _node_ingest)
    g.add_edge(START, "scrape")
    g.add_edge("scrape", "ingest")
    g.add_edge("ingest", END)
    return g


def compile_pipeline():
    return build_pipeline_graph().compile()


def run_pipeline(
    *,
    episode_id: str,
    project_root: Path,
    skip_scrape: bool = False,
    skip_ingest: bool = False,
) -> PipelineState:
    app = compile_pipeline()
    initial: PipelineState = {
        "episode_id": episode_id,
        "project_root": str(project_root.resolve()),
        "skip_scrape": skip_scrape,
        "skip_ingest": skip_ingest,
    }
    result = app.invoke(initial)
    return result  # type: ignore[return-value]
