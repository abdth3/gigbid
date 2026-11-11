"""Proposal studio, human approval/edit/reject (LangGraph resume), and pipeline board routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from langgraph.types import Command

from agent.graphs.bid_graph import build_bid_graph
from agent.graphs.checkpointer import get_async_checkpointer
from agent.nodes.verifier import verifier_node
from agent.nodes.writer import writer_node
from apps.api.auth.security import get_current_user
from apps.api.schemas.models import ApprovalActionRequest, RegenerateParagraphRequest
from apps.api.state_store import get_api_store
from gigsim.store import get_gigsim_store

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


@router.get("/pipeline")
def get_pipeline_board(user: dict = Depends(get_current_user)):
    api_store = get_api_store()
    runs = api_store.list_runs(user["user_id"])
    gigsim = get_gigsim_store()
    columns: dict[str, list[dict]] = {
        "drafted": [],
        "submitted": [],
        "viewed": [],
        "replied": [],
        "interview": [],
        "hired": [],
        "lost": [],
    }
    for r in runs:
        jid = r["job_id"]
        stage = api_store.get_stage(user["user_id"], jid)
        if stage in columns:
            job = gigsim.get_job(jid) or {}
            columns[stage].append({
                "job_id": jid,
                "title": job.get("title", jid),
                "bid_amount_usd": (r.get("price_quote") or {}).get("bid_amount_usd"),
                "fit_score": (r.get("fit_report") or {}).get("score", 0.0),
                "approval_status": r.get("approval_status"),
            })
    return {"columns": columns}


@router.post("/{job_id}/regenerate")
async def regenerate_proposal(job_id: str, req: RegenerateParagraphRequest, user: dict = Depends(get_current_user)):
    """Re-run Writer + Claim Verifier after evidence changes or user request."""
    api_store = get_api_store()
    run = api_store.get_run(user["user_id"], job_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    job = get_gigsim_store().get_job(job_id) or {"job_id": job_id, "title": job_id}
    # Re-fetch evidence from updated corpus store (catches deleted evidence!)
    from agent.nodes.fit_matcher import fit_matcher_node
    fit_out = await fit_matcher_node({"job": job, "persona": user.get("persona", "ai_ml_engineer"), "trace_id": run.get("trace_id", "")})

    writer_state = {
        "job": job,
        "job_spec": run.get("job_spec", {}),
        "evidence": fit_out["evidence"],
        "price_quote": run.get("price_quote", {}),
        "user_id": user["user_id"],
        "trace_id": run.get("trace_id", ""),
        "critiques": run.get("critiques", []),
    }
    w_out = await writer_node(writer_state)
    v_out = await verifier_node({
        "proposal_draft": w_out["proposal_draft"],
        "evidence": fit_out["evidence"],
        "trace_id": run.get("trace_id", ""),
    })

    run["evidence"] = fit_out["evidence"]
    run["fit_report"] = fit_out["fit_report"]
    run["proposal_draft"] = v_out["proposal_draft"]
    run["claim_verification"] = v_out["claim_verification"]
    api_store.set_run(user["user_id"], job_id, run)
    return {"status": "regenerated", "run": run}


@router.post("/{job_id}/approve")
async def approve_or_reject_proposal(job_id: str, req: ApprovalActionRequest, user: dict = Depends(get_current_user)):
    """Resume interrupted LangGraph thread with human approval, edit, or rejection."""
    api_store = get_api_store()
    run = api_store.get_run(user["user_id"], job_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    thread_id = run["thread_id"]
    checkpointer = await get_async_checkpointer()
    graph = build_bid_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    resume_payload = {
        "action": req.action,
        "edited_cover_letter": req.edited_cover_letter,
        "reason": req.reason,
    }
    result = await graph.ainvoke(Command(resume=resume_payload), config=config)

    run["proposal_draft"] = result.get("proposal_draft", run.get("proposal_draft"))
    run["approval_status"] = req.action
    run["submission_result"] = result.get("submission_result")
    run["execution_trace"] = result.get("execution_trace", run.get("execution_trace", []))

    if req.action == "reject":
        api_store.set_stage(user["user_id"], job_id, "lost")
        if req.reason:
            api_store.rejection_reasons.append(req.reason)
    else:
        sub_status = (result.get("submission_result") or {}).get("status", "submitted")
        stage = "replied" if sub_status == "replied" else ("viewed" if sub_status == "viewed" else "submitted")
        api_store.set_stage(user["user_id"], job_id, stage)

    api_store.set_run(user["user_id"], job_id, run)
    return {"status": req.action, "run": run}
