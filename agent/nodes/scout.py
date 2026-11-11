"""Scout node: fetches and deduplicates new jobs via Marketplace MCP."""

from __future__ import annotations

from typing import Any

from agent.llm_router import call_node_llm, load_prompt, mask_pii
from agent.mcp_client import get_mcp_client


async def scout_node(state: dict[str, Any]) -> dict[str, Any]:
    job = state.get("job")
    trace_id = state.get("trace_id", "")
    user_id = state.get("user_id", "default-user")
    persona = state.get("persona", "ai_ml_engineer")

    if not job:
        mcp = get_mcp_client()
        jobs = await mcp.call_tool(
            "scout",
            "search_jobs",
            {"query": "", "limit": 1, "persona": persona, "user_id": user_id, "trace_id": trace_id},
        )
        job = jobs[0] if jobs else {}

    llm_meta = await call_node_llm("scout", load_prompt("scout"), mask_pii(job.get("title", "")))
    return {
        "job": job,
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "scout",
            "tool": "search_jobs" if not state.get("job") else "queued_job",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"Loaded job {job.get('job_id', 'unknown')}",
            "trace_id": trace_id,
        }],
    }
