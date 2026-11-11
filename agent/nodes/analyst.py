"""Job Analyst node: extracts structured JobSpec from untrusted job post."""

from __future__ import annotations

import re
from typing import Any

from agent.handoffs import JobSpec
from agent.llm_router import call_node_llm, load_prompt, mask_pii


async def analyst_node(state: dict[str, Any]) -> dict[str, Any]:
    job = state["job"]
    trace_id = state.get("trace_id", "")
    raw_desc = job.get("description", "")
    # Delimit untrusted input (E4 Guardrails)
    delimited = f"<untrusted_job_post>\n{raw_desc}\n</untrusted_job_post>"
    llm_meta = await call_node_llm("analyst", load_prompt("analyst"), mask_pii(delimited))

    budget = job.get("budget") or {}
    deliverables = [s.strip() for s in re.split(r"[.;\n]+", raw_desc) if 10 < len(s.strip()) < 140][:4]
    hidden_needs = []
    if "reproduc" in raw_desc.lower():
        hidden_needs.append("Reproducible code & documentation")
    if "metric" in raw_desc.lower() or "evaluation" in raw_desc.lower():
        hidden_needs.append("Quantitative evaluation report")

    spec = JobSpec(
        job_id=job["job_id"],
        title=job.get("title", ""),
        deliverables=deliverables or ["Deliver requested solution"],
        required_skills=job.get("required_skills", []),
        budget_min=budget.get("min"),
        budget_max=budget.get("max"),
        timeline_days=int(job.get("duration_days", 14)),
        screening_questions=job.get("screening_questions", []),
        hidden_needs=hidden_needs,
    )
    return {
        "job_spec": spec.model_dump(),
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "analyst",
            "tool": "none",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"Extracted {len(spec.required_skills)} skills, {len(spec.deliverables)} deliverables",
            "trace_id": trace_id,
        }],
    }
