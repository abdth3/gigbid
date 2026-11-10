"""Shared retrieval primitives: dense cosine, BM25, and result types."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer

from rag.ingest.loader import PortfolioChunk


@dataclass
class RetrievedItem:
    evidence_id: str
    chunk_id: str
    type: str
    title: str
    text: str
    skills: list[str]
    date: str
    client_industry: str
    outcome: str
    source: str
    score: float
    sub_view: str = "summary"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "chunk_id": self.chunk_id,
            "type": self.type,
            "title": self.title,
            "text": self.text,
            "skills": self.skills,
            "date": self.date,
            "client_industry": self.client_industry,
            "outcome": self.outcome,
            "source": self.source,
            "score": round(float(self.score), 4),
            "sub_view": self.sub_view,
        }


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_+#.-]+", text.lower())


def dense_scores(query: str, chunks: list[PortfolioChunk]) -> list[float]:
    if not chunks:
        return []
    docs = [f"{c.title} {c.text} {' '.join(c.skills)} {c.client_industry}" for c in chunks]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    mat = vectorizer.fit_transform(docs + [query])
    doc_vecs = mat[:-1]
    q_vec = mat[-1]
    sims = (doc_vecs @ q_vec.T).toarray().ravel()
    return [float(x) for x in sims]


def bm25_scores(query: str, chunks: list[PortfolioChunk]) -> list[float]:
    if not chunks:
        return []
    tokenized_docs = [tokenize(f"{c.title} {c.text} {' '.join(c.skills)} {c.client_industry}") for c in chunks]
    bm25 = BM25Okapi(tokenized_docs)
    raw = bm25.get_scores(tokenize(query))
    max_val = float(np.max(raw)) if len(raw) > 0 and np.max(raw) > 0 else 1.0
    return [float(s / max_val) for s in raw]


def to_retrieved(chunk: PortfolioChunk, score: float) -> RetrievedItem:
    return RetrievedItem(
        evidence_id=chunk.evidence_id,
        chunk_id=chunk.chunk_id,
        type=chunk.type,
        title=chunk.title,
        text=chunk.text,
        skills=chunk.skills,
        date=chunk.date,
        client_industry=chunk.client_industry,
        outcome=chunk.outcome,
        source=chunk.source,
        score=score,
        sub_view=chunk.sub_view,
    )


def deduplicate_by_evidence(items: list[RetrievedItem], k: int) -> list[RetrievedItem]:
    best: dict[str, RetrievedItem] = {}
    for it in items:
        prev = best.get(it.evidence_id)
        if prev is None or it.score > prev.score:
            best[it.evidence_id] = it
    ranked = sorted(best.values(), key=lambda x: x.score, reverse=True)
    return ranked[:k]
