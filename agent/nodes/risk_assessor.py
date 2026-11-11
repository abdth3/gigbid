"""Risk Assessor node: scores client quality, detects scams & prompt injections."""

from __future__ import annotations

import re
from typing import Any

from agent.handoffs import RiskReport
from agent.llm_router import call_node_llm, load_prompt, mask_pii
from agent.mcp_client import get_mcp_client

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"\[system\s+override\]",
    r"important\s+admin\s+note",
    r"hidden\s+prompt",
    r"disregard\s+compliance",
]

SCAM_PATTERNS = [
    r"for\s+free",
    r"unpaid\s+trial",
    r"telegram\s*@",
    r"whatsapp",
    r"pay\s+directly\s+outside",
    r"\$0\s+milestone",
    r"winner\s+gets\s+paid",
]


async def risk_assessor_node(state: dict[str, Any]) -> dict[str, Any]:
    job = state["job"]
    trace_id = state.get("trace_id", "")
    user_id = state.get("user_id", "default-user")
    client_id = job.get("client_id", "unknown")

    mcp = get_mcp_client()
    client_hist = await mcp.call_tool(
        "risk_assessor",
        "get_client_history",
        {"client_id": client_id, "user_id": user_id, "trace_id": trace_id},
    )

    text = f"{job.get('title', '')}\n{job.get('description', '')}"
    delimited = f"<untrusted_job_post>\n{text}\n</untrusted_job_post>"
    llm_meta = await call_node_llm("risk_assessor", load_prompt("risk_assessor"), mask_pii(delimited))

    flags: list[str] = []
    lower = text.lower()
    injection_detected = any(re.search(pat, lower) for pat in INJECTION_PATTERNS)
    if injection_detected:
        flags.append("prompt_injection_detected")

    scam_match = any(re.search(pat, lower) for pat in SCAM_PATTERNS)
    budget_max = (job.get("budget") or {}).get("max", 0) or 0
    if scam_match or budget_max <= 50:
        flags.append("scam_or_unpaid_work")

    if not client_hist.get("payment_verified", True):
        flags.append("payment_unverified")

    score = 0.10
    if "scam_or_unpaid_work" in flags:
        score += 0.70
    if "payment_unverified" in flags:
        score += 0.15
    if injection_detected:
        score += 0.10  # Flagged & sanitized, not necessarily a scam job itself if client is legit
    score = min(1.0, round(score, 2))

    report = RiskReport(
        score=score,
        is_scam="scam_or_unpaid_work" in flags,
        injection_detected=injection_detected,
        flags=flags,
        explanation=(
            f"Client verified={client_hist.get('payment_verified')}, "
            f"hire_rate={client_hist.get('hire_rate', 0)}. Flags: {flags or ['none']}."
        ),
    )
    return {
        "risk_report": report.model_dump(),
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "risk_assessor",
            "tool": "get_client_history",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"Risk={score}, is_scam={report.is_scam}, injection={injection_detected}",
            "trace_id": trace_id,
        }],
    }
