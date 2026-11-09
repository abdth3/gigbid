"""Portfolio MCP tools (read-only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from rag.ingest.loader import get_corpus_store
from rag.retriever import retrieve_evidence

PERSONAS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "personas"


class SearchEvidenceInput(BaseModel):
    requirement: str = Field(..., min_length=2, description="Job requirement or skill query")
    k: int = Field(default=5, ge=1, le=20, description="Number of evidence items to return")
    filters: dict[str, Any] | None = Field(default=None, description="Optional metadata filters (type, industry)")
    persona: str = Field(default="ai_ml_engineer", description="Target freelancer persona")


def search_evidence_impl(
    requirement: str,
    k: int = 5,
    filters: dict[str, Any] | None = None,
    persona: str = "ai_ml_engineer",
) -> list[dict[str, Any]]:
    items = retrieve_evidence(query=requirement, persona=persona, k=k, filters=filters)
    return [
        {
            "evidence_id": it.evidence_id,
            "type": it.type,
            "title": it.title,
            "summary": it.text,
            "skills": it.skills,
            "date": it.date,
            "client_industry": it.client_industry,
            "outcome": it.outcome,
            "source": it.source,
            "score": round(it.score, 4),
        }
        for it in items
    ]


def get_case_study_impl(id: str, persona: str = "ai_ml_engineer") -> dict[str, Any]:
    store = get_corpus_store()
    for chunk in store.get_chunks(persona):
        if chunk.evidence_id == id:
            return {
                "evidence_id": chunk.evidence_id,
                "type": chunk.type,
                "title": chunk.title,
                "text": chunk.text,
                "skills": chunk.skills,
                "date": chunk.date,
                "client_industry": chunk.client_industry,
                "outcome": chunk.outcome,
                "source": chunk.source,
            }
    return {"error": f"Case study {id} not found for persona {persona}"}


def list_skills_impl(persona: str = "ai_ml_engineer") -> dict[str, Any]:
    profile_path = PERSONAS_DIR / persona / "profile.json"
    if profile_path.exists():
        prof = json.loads(profile_path.read_text(encoding="utf-8"))
        return {"persona": persona, "skills": prof.get("skills", [])}
    return {"persona": persona, "skills": []}
