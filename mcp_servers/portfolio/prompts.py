"""Portfolio MCP prompt templates for freelancers."""

from __future__ import annotations


def answer_screening_question_prompt(question: str, persona: str = "ai_ml_engineer") -> str:
    return (
        f"You are answering a client's screening question for persona '{persona}'.\n"
        f"Question: {question}\n\n"
        f"1. Call `search_evidence` with the core requirement from the question.\n"
        f"2. Cite at least one returned `evidence_id` in brackets like [evidence_id].\n"
        f"3. Do NOT fabricate any metric, tool, or outcome not present in the retrieved evidence."
    )


def draft_evidence_opening_prompt(job_title: str, key_skill: str) -> str:
    return (
        f"Draft a 2-sentence proposal opening for '{job_title}' focusing on '{key_skill}'. "
        f"Call `search_evidence` first and cite a real measurable outcome from the returned items."
    )
