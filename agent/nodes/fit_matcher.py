"""Fit Matcher node: maps requirements to portfolio evidence via Portfolio MCP."""

from __future__ import annotations

from typing import Any

from agent.handoffs import FitReport
from agent.llm_router import call_node_llm, load_prompt, mask_pii
from agent.mcp_client import get_mcp_client


async def fit_matcher_node(state: dict[str, Any]) -> dict[str, Any]:
    job = state["job"]
    persona = state.get("persona", "ai_ml_engineer")
    trace_id = state.get("trace_id", "")
    req_skills = job.get("required_skills", [])
    query = f"{job.get('title', '')} {' '.join(req_skills)}"

    mcp = get_mcp_client()
    skills_resp = await mcp.call_tool("fit_matcher", "list_skills", {"persona": persona})
    persona_skills = {s.lower() for s in skills_resp.get("skills", [])}

    evidence = await mcp.call_tool(
        "fit_matcher",
        "search_evidence",
        {"requirement": query, "k": 5, "persona": persona},
    )
    llm_meta = await call_node_llm("fit_matcher", load_prompt("fit_matcher"), mask_pii(query))

    matched = [s for s in req_skills if s.lower() in persona_skills]
    missing = [s for s in req_skills if s.lower() not in persona_skills]

    # Also check skills inside retrieved evidence
    ev_skills = {s.lower() for ev in evidence for s in ev.get("skills", [])}
    for s in list(missing):
        if s.lower() in ev_skills:
            matched.append(s)
            missing.remove(s)

    skill_ratio = len(matched) / max(1, len(req_skills))
    ev_bonus = 0.20 if evidence else 0.0
    fit_score = min(1.0, round(0.80 * skill_ratio + ev_bonus, 2))

    matrix = []
    for idx, req in enumerate(req_skills):
        ev_match = evidence[idx % len(evidence)]["evidence_id"] if evidence else "none"
        matrix.append({
            "requirement": req,
            "evidence_id": ev_match,
            "status": "matched" if req in matched else "gap",
        })

    report = FitReport(
        score=fit_score,
        matched_skills=matched,
        missing_skills=missing,
        evidence_ids=[e["evidence_id"] for e in evidence],
        requirement_matrix=matrix,
        reasons=[
            f"Matched {len(matched)}/{len(req_skills)} required skills",
            f"Retrieved {len(evidence)} supporting portfolio items",
        ],
    )
    return {
        "fit_report": report.model_dump(),
        "evidence": evidence,
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "fit_matcher",
            "tool": "search_evidence,list_skills",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"Fit={fit_score}, evidence={len(evidence)}",
            "trace_id": trace_id,
        }],
    }
