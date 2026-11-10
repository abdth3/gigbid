"""V5: Multi-vector indexing — summary, README, and code indexed separately, fused per project."""

from __future__ import annotations

from collections import defaultdict
from rag.ingest.loader import PortfolioChunk
from rag.variants.base import RetrievedItem, bm25_scores, dense_scores, to_retrieved
from rag.variants.v0_naive import _apply_filters


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
) -> list[RetrievedItem]:
    filtered = _apply_filters(chunks, filters)
    if not filtered:
        return []
    d_scores = dense_scores(query, filtered)
    b_scores = bm25_scores(query, filtered)

    by_evidence: dict[str, list[tuple[PortfolioChunk, float]]] = defaultdict(list)
    for c, ds, bs in zip(filtered, d_scores, b_scores):
        by_evidence[c.evidence_id].append((c, 0.55 * ds + 0.45 * bs))

    fused: list[RetrievedItem] = []
    for ev_id, views in by_evidence.items():
        # Combine best sub-view score + bonus for multi-view corroboration (summary + code/readme)
        views.sort(key=lambda x: x[1], reverse=True)
        top_chunk, top_score = views[0]
        multi_bonus = 0.08 * (len(views) - 1)
        item = to_retrieved(top_chunk, top_score + multi_bonus)
        fused.append(item)

    fused.sort(key=lambda x: x.score, reverse=True)
    return fused[:k]
