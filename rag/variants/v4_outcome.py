"""V4: Outcome-aware ranking — boosts evidence from won/replied proposals and verified outcomes."""

from __future__ import annotations

from rag.ingest.loader import PortfolioChunk
from rag.variants import v3_rerank
from rag.variants.base import RetrievedItem


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
) -> list[RetrievedItem]:
    candidates = v3_rerank.retrieve(query, chunks, k=max(k * 3, 15), filters=filters)
    for c in candidates:
        out = (c.outcome or "").lower()
        if out == "won" or "%" in out or "rating_5" in out:
            c.score *= 1.25
        elif out == "replied" or "rating_4" in out:
            c.score *= 1.12
        elif out == "ignored":
            c.score *= 0.80
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:k]
