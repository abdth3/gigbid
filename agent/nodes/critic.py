"""Critic node: checks grounding, personalisation, and Nov 2 length cap (max 2 loops)."""

from __future__ import annotations

from typing import Any

from agent.handoffs import Critique
from agent.llm_router import call_node_llm, load_config, load_prompt, mask_pii


async def critic_node(state: dict[str, Any]) -> dict[str, Any]:
    draft = state.get("proposal_draft", {})
    ver = state.get("claim_verification", {})
    rev_count = int(state.get("revision_count", 0))
    trace_id = state.get("trace_id", "")

    cover = draft.get("cover_letter", "")
    max_chars = int(load_config().get("policy_nov2", {}).get("max_cover_letter_chars", 1800))

    grounding_ok = ver.get("unsupported_after", 0) == 0
    generic_bad = any(p in cover.lower() for p in ["dear sir/madam", "i am passionate", "to whom it may concern"])
    personalisation_ok = not generic_bad and len(cover) >= 60
    length_ok = len(cover) <= max_chars

    issues = []
    if not grounding_ok:
        issues.append("Contains unsupported claims")
    if not personalisation_ok:
        issues.append("Opening is generic or too short")
    if not length_ok:
        issues.append(f"Exceeds {max_chars} char policy limit")

    passed = grounding_ok and personalisation_ok and length_ok
    critique = Critique(
        passed=passed,
        grounding_ok=grounding_ok,
        personalisation_ok=personalisation_ok,
        length_ok=length_ok,
        issues=issues,
        revision_number=rev_count,
    )
    llm_meta = await call_node_llm("critic", load_prompt("critic"), mask_pii(cover))

    return {
        "critiques": [critique.model_dump()],
        "revision_count": rev_count + (0 if passed else 1),
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "critic",
            "tool": "none",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"passed={passed}, issues={issues}",
            "trace_id": trace_id,
        }],
    }
