"""Client messages & Conversation Graph approval routes."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends
from langgraph.types import Command

from agent.graphs.checkpointer import get_async_checkpointer
from agent.graphs.conversation_graph import build_conversation_graph
from apps.api.auth.security import get_current_user
from apps.api.schemas.models import MessageReplyRequest
from apps.api.state_store import get_api_store
from gigsim.store import get_gigsim_store

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("")
def list_threads(user: dict = Depends(get_current_user)):
    gigsim = get_gigsim_store()
    api_store = get_api_store()
    threads = []
    for job_id, msgs in gigsim.messages.items():
        # Scope message threads by tenant (E4)
        if not api_store.get_run(user["user_id"], job_id):
            continue
        job = gigsim.get_job(job_id) or {}
        threads.append({
            "job_id": job_id,
            "job_title": job.get("title", job_id),
            "messages": msgs,
        })
    return {"threads": threads}


@router.post("/{job_id}/draft")
async def draft_reply(job_id: str, user: dict = Depends(get_current_user)):
    thread_id = f"conv-{user['user_id']}-{job_id}"
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"
    checkpointer = await get_async_checkpointer()
    graph = build_conversation_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    res = await graph.ainvoke(
        {
            "thread_id": thread_id,
            "trace_id": trace_id,
            "user_id": user["user_id"],
            "persona": user.get("persona", "ai_ml_engineer"),
            "job_id": job_id,
        },
        config=config,
    )
    snap = await graph.aget_state(config)
    vals = snap.values if snap else res
    return {
        "thread_id": thread_id,
        "client_intent": vals.get("client_intent"),
        "draft_reply": vals.get("draft_reply"),
        "proposed_slots": vals.get("proposed_slots", []),
        "awaiting_approval": bool(snap and snap.next),
    }


@router.post("/approve")
async def approve_reply(req: MessageReplyRequest, user: dict = Depends(get_current_user)):
    thread_id = f"conv-{user['user_id']}-{req.job_id}"
    checkpointer = await get_async_checkpointer()
    graph = build_conversation_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    res = await graph.ainvoke(
        Command(resume={"action": req.action, "edited_reply": req.edited_reply}),
        config=config,
    )
    if req.action != "reject":
        get_api_store().set_stage(user["user_id"], req.job_id, "interview")
    return {"status": req.action, "send_result": res.get("send_result")}
