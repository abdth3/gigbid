"""V3: Cross-encoder / pairwise interaction reranking over V2 hybrid candidates."""

from __future__ import annotations

from rag.ingest.loader import PortfolioChunk
from rag.variants import v2_hybrid
from rag.variants.base import RetrievedItem, tokenize


def _cross_score(query: str, item: RetrievedItem) -> float:
    q_tokens = set(tokenize(query))
    doc_tokens = set(tokenize(f"{item.title} {item.text} {' '.join(item.skills)} {item.client_industry}"))
    if not q_tokens:
        return item.score
    overlap = len(q_tokens & doc_tokens) / len(q_tokens)
    skill_overlap = len(q_tokens & {s.lower() for s in item.skills}) / max(1, len(q_tokens))
    # Case studies get a slight precision preference over raw past proposals when exact skills match
    type_bonus = 0.08 if item.type == "case_study" else 0.0
    return 0.45 * item.score * 30 + 0.35 * overlap + 0.20 * skill_overlap + type_bonus


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
) -> list[RetrievedItem]:
    candidates = v2_hybrid.retrieve(query, chunks, k=max(k * 4, 20), filters=filters)
    for c in candidates:
        c.score = _cross_score(query, c)
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[:k]
