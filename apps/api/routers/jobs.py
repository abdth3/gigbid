"""Job inbox, job detail, skip, and analysis execution routes."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException

from agent.graphs.bid_graph import build_bid_graph
from agent.graphs.checkpointer import get_async_checkpointer
from agent.mcp_client import MarketplaceDegradedError, get_mcp_client
from apps.api.auth.security import get_current_user
from apps.api.schemas.models import AnalyzeJobRequest
from apps.api.state_store import get_api_store
from gigsim.store import get_gigsim_store

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def list_jobs(query: str = "", limit: int = 30, user: dict = Depends(get_current_user)):
    mcp = get_mcp_client()
    if mcp.marketplace_offline:
        return {
            "degraded": True,
            "banner": "Marketplace MCP server is unavailable. Showing cached inbox; new analyses are queued.",
            "jobs": [],
        }

    persona = user.get("persona", "ai_ml_engineer")
    store = get_gigsim_store()
    all_persona_jobs = store.search_jobs(query=query, limit=200, persona=persona)
    # Surface a balanced mix at the top: high-fit jobs first, then 1 scam, 1 injection, then rest
    if not query:
        clean_jobs = [j for j in all_persona_jobs if j.get("gold_decision") == "bid" and not j.get("is_injection")]
        scam_jobs = [j for j in all_persona_jobs if j.get("is_scam")]
        inj_jobs = [j for j in all_persona_jobs if j.get("is_injection")]
        other_jobs = [j for j in all_persona_jobs if j not in clean_jobs[:3] and j not in scam_jobs[:2] and j not in inj_jobs[:2]]
        raw_jobs = (clean_jobs[:3] + scam_jobs[:1] + inj_jobs[:1] + other_jobs)[:limit]
    else:
        raw_jobs = all_persona_jobs[:limit]
    api_store = get_api_store()

    enriched = []
    for j in raw_jobs:
        run = api_store.get_run(user["user_id"], j["job_id"])
        fit_score = (run or {}).get("fit_report", {}).get("score", 0.0)
        risk_score = (run or {}).get("risk_report", {}).get("score", 0.0)
        is_scam = (run or {}).get("risk_report", {}).get("is_scam", False)
        rec = (run or {}).get("decision", {}).get("action", "pending")
        stage = api_store.get_stage(user["user_id"], j["job_id"])
        enriched.append({
            **j,
            "fit_score": fit_score,
            "risk_score": risk_score,
            "is_scam": is_scam,
            "recommended_action": rec,
            "stage": stage,
            "thread_id": (run or {}).get("thread_id"),
            "approval_status": (run or {}).get("approval_status"),
        })

    enriched.sort(key=lambda x: (x["recommended_action"] != "pending", x["fit_score"], -x["risk_score"]), reverse=True)
    return {"degraded": False, "jobs": enriched}


@router.get("/{job_id}")
def get_job_detail(job_id: str, user: dict = Depends(get_current_user)):
    job = get_gigsim_store().get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    run = get_api_store().get_run(user["user_id"], job_id)
    return {
        "job": job,
        "run": run,
        "stage": get_api_store().get_stage(user["user_id"], job_id),
    }


@router.post("/{job_id}/skip")
def skip_job(job_id: str, reason: str = "Skipped by user", user: dict = Depends(get_current_user)):
    api_store = get_api_store()
    api_store.set_stage(user["user_id"], job_id, "lost")
    api_store.rejection_reasons.append(reason)
    api_store.save()
    return {"status": "skipped", "job_id": job_id, "reason": reason}


@router.post("/analyze")
async def analyze_job(req: AnalyzeJobRequest, user: dict = Depends(get_current_user)):
    mcp = get_mcp_client()
    if mcp.marketplace_offline:
        mcp.queued_jobs.append({"user_id": user["user_id"], "job_id": req.job_id})
        return {
            "degraded": True,
            "status": "queued",
            "message": "Marketplace MCP server is offline. Job queued for automatic recovery.",
        }

    job = get_gigsim_store().get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    thread_id = f"bid-{user['user_id']}-{req.job_id}"
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"
    checkpointer = await get_async_checkpointer()
    graph = build_bid_graph(checkpointer=checkpointer)

    initial_state = {
        "thread_id": thread_id,
        "trace_id": trace_id,
        "user_id": user["user_id"],
        "persona": user.get("persona", "ai_ml_engineer"),
        "strategy": req.strategy,
        "job": job,
        "revision_count": 0,
    }
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await graph.ainvoke(initial_state, config=config)
    except MarketplaceDegradedError as exc:
        return {"degraded": True, "status": "queued", "message": str(exc)}

    state_snap = await graph.aget_state(config)
    vals = state_snap.values if state_snap else result
    is_interrupted = bool(state_snap and state_snap.next)

    api_store = get_api_store()
    run_record = {
        "thread_id": thread_id,
        "trace_id": trace_id,
        "job_id": req.job_id,
        "job_spec": vals.get("job_spec"),
        "risk_report": vals.get("risk_report"),
        "fit_report": vals.get("fit_report"),
        "evidence": vals.get("evidence", []),
        "decision": vals.get("decision"),
        "price_quote": vals.get("price_quote"),
        "proposal_draft": vals.get("proposal_draft"),
        "claim_verification": vals.get("claim_verification"),
        "critiques": vals.get("critiques", []),
        "compliance_verdict": vals.get("compliance_verdict"),
        "execution_trace": vals.get("execution_trace", []),
        "tokens_used": vals.get("tokens_used", 0),
        "approval_status": "pending_approval" if is_interrupted else vals.get("approval_status", "skipped"),
        "submission_result": vals.get("submission_result"),
    }
    api_store.set_run(user["user_id"], req.job_id, run_record)
    if is_interrupted:
        api_store.set_stage(user["user_id"], req.job_id, "drafted")
    elif (vals.get("decision") or {}).get("action") == "skip":
        api_store.set_stage(user["user_id"], req.job_id, "lost")

    return {"degraded": False, "run": run_record}
