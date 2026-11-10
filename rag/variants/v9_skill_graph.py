"""V9: Skill Graph (GraphRAG) — connects skills, projects, industries and outcomes as a graph."""

from __future__ import annotations

from collections import defaultdict
from rag.ingest.loader import PortfolioChunk
from rag.variants import v2_hybrid
from rag.variants.base import RetrievedItem, deduplicate_by_evidence, to_retrieved, tokenize


def retrieve(
    query: str,
    chunks: list[PortfolioChunk],
    k: int = 5,
    filters: dict | None = None,
) -> list[RetrievedItem]:
    if not chunks:
        return []
    # Build lightweight bipartite skill/industry <-> evidence graph
    skill_to_ev: dict[str, set[str]] = defaultdict(set)
    industry_to_ev: dict[str, set[str]] = defaultdict(set)
    ev_best_chunk: dict[str, PortfolioChunk] = {}

    for c in chunks:
        ev_best_chunk.setdefault(c.evidence_id, c)
        for s in c.skills:
            skill_to_ev[s.lower()].add(c.evidence_id)
        if c.client_industry:
            industry_to_ev[c.client_industry.lower()].add(c.evidence_id)

    q_tokens = set(tokenize(query))
    graph_scores: dict[str, float] = defaultdict(float)
    for skill, ev_ids in skill_to_ev.items():
        if skill in query.lower() or skill in q_tokens:
            for eid in ev_ids:
                graph_scores[eid] += 0.35
    for ind, ev_ids in industry_to_ev.items():
        if ind in query.lower():
            for eid in ev_ids:
                graph_scores[eid] += 0.30

    hybrid_items = v2_hybrid.retrieve(query, chunks, k=max(k * 3, 15), filters=filters)
    combined: list[RetrievedItem] = []
    seen = set()
    for it in hybrid_items:
        it.score = it.score + graph_scores.get(it.evidence_id, 0.0)
        combined.append(it)
        seen.add(it.evidence_id)

    for eid, gscore in graph_scores.items():
        if eid not in seen and eid in ev_best_chunk:
            c = ev_best_chunk[eid]
            if filters and filters.get("type") and c.type != filters["type"]:
                continue
            combined.append(to_retrieved(c, gscore))

    return deduplicate_by_evidence(combined, k)
