"""Proposal Writer node: drafts evidence-grounded cover letter and screening answers."""

from __future__ import annotations

from typing import Any

from agent.handoffs import ProposalDraft
from agent.llm_router import call_node_llm, load_prompt, mask_pii
from agent.memory.store import get_memory_store


async def writer_node(state: dict[str, Any]) -> dict[str, Any]:
    job = state["job"]
    job_spec = state.get("job_spec", {})
    evidence = state.get("evidence", [])
    price_quote = state.get("price_quote", {})
    user_id = state.get("user_id", "default-user")
    trace_id = state.get("trace_id", "")
    strategy = state.get("strategy", "evidence_first")
    critiques = state.get("critiques", [])

    memories = get_memory_store().list_memories(user_id)
    style_rules = [m["rule"] for m in memories["style_memory"]]

    # Always pull fresh evidence-grounded claims
    top_ev = evidence[:3]
    ev_ids = [e["evidence_id"] for e in top_ev]

    if top_ev:
        primary = top_ev[0]
        if strategy == "outcome_led":
            opening = (
                f"Outcome achieved: {primary.get('outcome', 'verified delivery')} on "
                f"{primary.get('title', 'a similar build')} [{primary['evidence_id']}]."
            )
        else:
            opening = (
                f"For your {job_spec.get('title', job.get('title', 'project'))}, I recently delivered "
                f"{primary.get('title', 'a similar system')} ({primary.get('outcome', 'production deployment')}) "
                f"[{primary['evidence_id']}]."
            )
        supporting_lines = []
        for ev in top_ev[1:]:
            supporting_lines.append(
                f"Additionally, {ev.get('title', 'related work')} demonstrated "
                f"{ev.get('outcome', 'measurable impact')} [{ev['evidence_id']}]."
            )
        body = " ".join([opening] + supporting_lines)
    else:
        body = (
            f"I have reviewed the requirements for {job_spec.get('title', job.get('title', 'your project'))}. "
            f"No direct portfolio case study matched all requirements, so I would begin with a scoped technical discovery."
        )

    bid = price_quote.get("bid_amount_usd", 450)
    closing = (
        f" My proposed bid is ${bid:.0f} USD for a {job_spec.get('timeline_days', 14)}-day delivery. "
        f"Happy to walk through the architecture and milestones on a brief call."
    )
    cover_letter = f"{body}{closing}".strip()

    # Apply learned style memory constraints
    for rule in style_rules:
        if "passionate" in rule.lower():
            cover_letter = cover_letter.replace("passionate", "focused")

    # Screening answers grounded in evidence
    screening_answers = []
    for q in job_spec.get("screening_questions", []):
        if top_ev:
            p = top_ev[0]
            screening_answers.append(
                f"In {p['title']} [{p['evidence_id']}], we achieved {p.get('outcome', 'verified results')} "
                f"using {', '.join(p.get('skills', [])[:3])}."
            )
        else:
            screening_answers.append("I would start by establishing reproducible baselines and clear evaluation metrics.")

    llm_prompt_input = (
        f"Job Title: {job_spec.get('title', job.get('title', ''))}\n"
        f"Strategy: {strategy}\n"
        f"Style Rules: {style_rules}\n"
        f"Proposed Bid: ${bid:.0f} USD ({job_spec.get('timeline_days', 14)} days)\n"
        f"Verified Evidence (cite using [evidence_id]):\n"
        + "\n".join(f"- [{e['evidence_id']}] {e.get('title')}: {e.get('outcome')}" for e in top_ev)
        + "\nWrite a concise (<1200 chars), personalized cover letter citing the exact [evidence_id] tags."
    )
    llm_meta = await call_node_llm("writer", load_prompt("writer"), mask_pii(llm_prompt_input))
    if llm_meta.get("text") and len(llm_meta["text"].strip()) > 60:
        cover_letter = llm_meta["text"].strip()
        for rule in style_rules:
            if "passionate" in rule.lower():
                cover_letter = cover_letter.replace("passionate", "focused")
    draft = ProposalDraft(
        job_id=job["job_id"],
        cover_letter=cover_letter,
        screening_answers=screening_answers,
        evidence_ids=ev_ids,
        strategy=strategy,
        status="pending_verification",
    )
    return {
        "proposal_draft": draft.model_dump(),
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "writer",
            "tool": "none",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"Drafted {len(cover_letter)} chars citing {ev_ids} (strategy={strategy}, rev={len(critiques)})",
            "trace_id": trace_id,
        }],
    }
