"""V8: Corrective / Self-RAG loop — grades evidence, re-queries when weak, refuses when none."""

from __future__ import annotations

from rag.ingest.loader import PortfolioChunk
from rag.variants import v3_rerank
from rag.variants.base import RetrievedItem, tokenize


def _grade_relevance(query: str, items: list[RetrievedItem]) -> float:
    if not items:
        return 0.0
    q_tokens = set(tokenize(query))
    top_tokens = set(tokenize(f"{items[0].title} {items[0].text} {' '.join(items[0].skills)}"))
    if not q_tokens:
        return 0.0
    return len(q_tokens & top_tokens) / len(q_tokens)


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
    min_grade: float = 0.15,
) -> list[RetrievedItem]:
    # Attempt 1: V3 rerank
    results = v3_rerank.retrieve(query, chunks, k=k, filters=filters)
    grade = _grade_relevance(query, results)
    if grade >= min_grade:
        return results

    # Attempt 2: Re-query using expanded keywords (strip filler, focus on technical terms)
    tech_terms = [t for t in tokenize(query) if len(t) > 2]
    expanded_query = " ".join(tech_terms[:10])
    retry_results = v3_rerank.retrieve(expanded_query, chunks, k=k, filters=filters)
    retry_grade = _grade_relevance(query, retry_results)
    if retry_grade >= min_grade:
        return retry_results

    # Refuse to claim when no relevant evidence meets threshold
    return []
