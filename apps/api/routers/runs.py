"""Agent Run Viewer, SSE live progress streaming, checkpoint replay, and degraded mode toggle."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from agent.graphs.bid_graph import build_bid_graph
from agent.graphs.checkpointer import get_async_checkpointer
from agent.mcp_client import get_mcp_client
from apps.api.auth.security import get_current_user
from apps.api.state_store import get_api_store
from apps.api.streaming import stream_graph_events
from gigsim.store import get_gigsim_store

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("")
def list_runs(user: dict = Depends(get_current_user)):
    return {"runs": get_api_store().list_runs(user["user_id"])}


@router.get("/marketplace-status")
def marketplace_status():
    mcp = get_mcp_client()
    return {
        "offline": mcp.marketplace_offline,
        "queued_count": len(mcp.queued_jobs),
    }


@router.post("/marketplace-status")
def set_marketplace_status(offline: bool):
    mcp = get_mcp_client()
    mcp.set_marketplace_offline(offline)
    return {
        "offline": mcp.marketplace_offline,
        "queued_count": len(mcp.queued_jobs),
    }


@router.get("/{job_id}")
def get_run(job_id: str, user: dict = Depends(get_current_user)):
    run = get_api_store().get_run(user["user_id"], job_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{job_id}/stream")
async def stream_run(job_id: str, user: dict = Depends(get_current_user)):
    job = get_gigsim_store().get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    thread_id = f"stream-{user['user_id']}-{job_id}-{uuid.uuid4().hex[:6]}"
    checkpointer = await get_async_checkpointer()
    graph = build_bid_graph(checkpointer=checkpointer)
    initial_state = {
        "thread_id": thread_id,
        "trace_id": f"trace-{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "persona": user.get("persona", "ai_ml_engineer"),
        "job": job,
        "revision_count": 0,
    }
    config = {"configurable": {"thread_id": thread_id}}
    return StreamingResponse(stream_graph_events(graph, initial_state, config), media_type="text/event-stream")
