"""Configurable RAG retriever factory with evidence cache."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from rag.ingest.loader import get_corpus_store
from rag.variants import (
    v0_naive,
    v1_decomp,
    v2_hybrid,
    v3_rerank,
    v4_outcome,
    v5_multivector,
    v8_corrective,
    v9_skill_graph,
)
from rag.variants.base import RetrievedItem

VARIANTS = {
    "v0_naive": v0_naive.retrieve,
    "v1_decomp": v1_decomp.retrieve,
    "v2_hybrid": v2_hybrid.retrieve,
    "v3_rerank": v3_rerank.retrieve,
    "v4_outcome": v4_outcome.retrieve,
    "v5_multivector": v5_multivector.retrieve,
    "v8_corrective": v8_corrective.retrieve,
    "v9_skill_graph": v9_skill_graph.retrieve,
}

CONFIG_PATH = Path(__file__).resolve().parent.parent / "agent" / "config.yaml"


def get_configured_variant() -> str:
    if CONFIG_PATH.exists():
        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        return cfg.get("rag", {}).get("variant", "v4_outcome")
    return "v4_outcome"


def retrieve_evidence(
    query: str,
    persona: str = "ai_ml_engineer",
    k: int = 5,
    filters: dict[str, Any] | None = None,
    variant: str | None = None,
) -> list[RetrievedItem]:
    chosen = variant or get_configured_variant()
    fn = VARIANTS.get(chosen, v4_outcome.retrieve)
    chunks = get_corpus_store().get_chunks(persona)
    return fn(query=query, chunks=chunks, k=k, filters=filters)
