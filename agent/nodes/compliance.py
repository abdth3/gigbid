"""Compliance Guard node: enforces policy pack v2.0 (including Nov 2 update) and masks PII."""

from __future__ import annotations

import re
from typing import Any

from agent.handoffs import ComplianceVerdict
from agent.llm_router import call_node_llm, load_config, load_prompt, mask_pii

FORBIDDEN_PATTERNS = [
    (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "off_platform_email"),
    (r"(telegram|whatsapp|discord|skype)\s*[@:]?", "off_platform_messaging"),
    (r"100%\s*(guarantee|bug[- ]free|money[- ]back)", "prohibited_guarantee"),
    (r"pay\s+(directly|outside|via\s+crypto)", "off_platform_payment"),
]


async def compliance_node(state: dict[str, Any]) -> dict[str, Any]:
    draft = dict(state.get("proposal_draft", {}))
    cover = draft.get("cover_letter", "")
    trace_id = state.get("trace_id", "")
    max_chars = int(load_config().get("policy_nov2", {}).get("max_cover_letter_chars", 1800))

    blocked: list[str] = []
    for pat, label in FORBIDDEN_PATTERNS:
        if re.search(pat, cover, flags=re.I):
            blocked.append(label)

    if len(cover) > max_chars:
        blocked.append(f"exceeds_{max_chars}_char_limit")
        cover = cover[:max_chars]

    sanitized = mask_pii(cover)
    draft["cover_letter"] = sanitized
    passed = len(blocked) == 0

    verdict = ComplianceVerdict(
        passed=passed,
        blocked_reasons=blocked,
        sanitized_cover_letter=sanitized,
    )
    llm_meta = await call_node_llm("compliance", load_prompt("compliance"), sanitized)

    return {
        "proposal_draft": draft,
        "compliance_verdict": verdict.model_dump(),
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "compliance",
            "tool": "policy_pack_v2",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"passed={passed}, blocked={blocked}",
            "trace_id": trace_id,
        }],
    }
