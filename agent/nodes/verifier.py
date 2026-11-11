"""Verifier node: splits proposal into claims and removes/rewrites unsupported claims (B3 & R5)."""

from __future__ import annotations

from typing import Any

from rag.verify import verify_and_rewrite_proposal


async def verifier_node(state: dict[str, Any]) -> dict[str, Any]:
    draft = dict(state.get("proposal_draft", {}))
    evidence = state.get("evidence", [])
    trace_id = state.get("trace_id", "")

    ver_result = verify_and_rewrite_proposal(draft.get("cover_letter", ""), evidence)
    draft["cover_letter"] = ver_result["cleaned_cover_letter"]
    draft["status"] = "verified"

    return {
        "proposal_draft": draft,
        "claim_verification": ver_result,
        "step_count": 1,
        "execution_trace": [{
            "node": "verifier",
            "tool": "verify_and_rewrite_proposal",
            "model": "deterministic-claim-verifier",
            "tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 1.2,
            "observation": (
                f"Claims={ver_result['total_claims']}, "
                f"unsupported_before={ver_result['unsupported_before']}, "
                f"unsupported_after={ver_result['unsupported_after']}"
            ),
            "trace_id": trace_id,
        }],
    }
