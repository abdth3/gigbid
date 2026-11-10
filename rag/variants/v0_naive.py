"""V0: Naive dense fixed-chunk top-k cosine baseline."""

from __future__ import annotations

from rag.ingest.loader import PortfolioChunk
from rag.variants.base import RetrievedItem, deduplicate_by_evidence, dense_scores, to_retrieved


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
) -> list[RetrievedItem]:
    filtered = _apply_filters(chunks, filters)
    if not filtered:
        return []
    scores = dense_scores(query, filtered)
    items = [to_retrieved(c, s) for c, s in zip(filtered, scores)]
    return deduplicate_by_evidence(items, k)


def _apply_filters(chunks: list[PortfolioChunk], filters: dict | None) -> list[PortfolioChunk]:
    if not filters:
        return chunks
    out = chunks
    if "type" in filters and filters["type"]:
        out = [c for c in out if c.type == filters["type"]]
    if "industry" in filters and filters["industry"]:
        out = [c for c in out if c.client_industry.lower() == filters["industry"].lower()]
    return out
