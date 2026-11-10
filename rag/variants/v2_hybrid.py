"""V2: Hybrid BM25 + Dense retrieval with Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from rag.ingest.loader import PortfolioChunk
from rag.variants.base import (
    RetrievedItem,
    bm25_scores,
    deduplicate_by_evidence,
    dense_scores,
    to_retrieved,
)
from rag.variants.v0_naive import _apply_filters


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
    rrf_k: int = 60,
) -> list[RetrievedItem]:
    filtered = _apply_filters(chunks, filters)
    if not filtered:
        return []
    d_scores = dense_scores(query, filtered)
    b_scores = bm25_scores(query, filtered)

    d_order = sorted(range(len(filtered)), key=lambda i: d_scores[i], reverse=True)
    b_order = sorted(range(len(filtered)), key=lambda i: b_scores[i], reverse=True)

    rrf: dict[int, float] = {}
    for rank, idx in enumerate(d_order, start=1):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (rrf_k + rank)
    for rank, idx in enumerate(b_order, start=1):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (rrf_k + rank)

    items = [to_retrieved(filtered[idx], score) for idx, score in rrf.items()]
    return deduplicate_by_evidence(items, k)
