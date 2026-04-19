"""LangGraph pipeline: Dunderpedia scrape → SQLite ingest."""

from backend.pipeline.graph import build_pipeline_graph, run_pipeline

__all__ = ["build_pipeline_graph", "run_pipeline"]
