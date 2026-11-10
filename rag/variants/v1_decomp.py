"""V1: Requirement decomposition — one retrieval per extracted requirement, then merge."""

from __future__ import annotations

import re
from rag.ingest.loader import PortfolioChunk
from rag.variants.base import RetrievedItem, deduplicate_by_evidence, dense_scores, to_retrieved
from rag.variants.v0_naive import _apply_filters


def split_requirements(query: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[,;\n•]+|\band\b", query) if len(p.strip()) >= 2]
    return parts[:8] if parts else [query]


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
) -> list[RetrievedItem]:
    filtered = _apply_filters(chunks, filters)
    if not filtered:
        return []
    sub_queries = split_requirements(query)
    agg_scores: dict[str, float] = {}
    chunk_map = {c.chunk_id: c for c in filtered}
    for sq in sub_queries:
        scores = dense_scores(sq, filtered)
        for c, s in zip(filtered, scores):
            agg_scores[c.chunk_id] = agg_scores.get(c.chunk_id, 0.0) + s / len(sub_queries)
    items = [to_retrieved(chunk_map[cid], sc) for cid, sc in agg_scores.items()]
    return deduplicate_by_evidence(items, k)
