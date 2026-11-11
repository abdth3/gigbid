"""Hand-written LangGraph Conversation Graph with interrupt() approval gate (C1)."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from agent.mcp_client import get_mcp_client
from agent.nodes.client_liaison import client_liaison_node
from agent.state import ConversationState


async def conversation_approval_node(state: ConversationState) -> dict[str, Any]:
    human_response = interrupt({
        "type": "message_approval",
        "job_id": state["job_id"],
        "client_intent": state.get("client_intent", {}),
        "draft_reply": state.get("draft_reply", ""),
        "proposed_slots": state.get("proposed_slots", []),
    })
    action = (human_response or {}).get("action", "approve")
    edited = (human_response or {}).get("edited_reply")
    return {
        "approval_status": action,
        "draft_reply": edited if (action == "edit" and edited) else state.get("draft_reply", ""),
    }


async def send_reply_node(state: ConversationState) -> dict[str, Any]:
    if state.get("approval_status") == "reject":
        return {"send_result": {"status": "rejected"}}

    mcp = get_mcp_client()
    job_id = state["job_id"]
    user_id = state.get("user_id", "default-user")
    trace_id = state.get("trace_id", "")

    slots = state.get("proposed_slots", [])
    if slots and (state.get("client_intent") or {}).get("intent") == "interview_request":
        await mcp.call_tool(
            "client_liaison",
            "create_interview_hold",
            {
                "job_id": job_id,
                "slot_iso": slots[0]["start_iso"],
                "idempotency_key": f"hold-{job_id}-{slots[0]['slot_id']}",
            },
        )

    res = await mcp.call_tool(
        "client_liaison",
        "send_message",
        {
            "job_id": job_id,
            "text": state.get("draft_reply", ""),
            "idempotency_key": f"msg-{job_id}-{len(state.get('messages', []))}",
            "dry_run": False,
            "user_id": user_id,
            "trace_id": trace_id,
        },
    )
    return {"send_result": res}


def build_conversation_graph(checkpointer: Any = None):
    builder = StateGraph(ConversationState)
    builder.add_node("client_liaison", client_liaison_node)
    builder.add_node("human_approval", conversation_approval_node)
    builder.add_node("send_reply", send_reply_node)

    builder.add_edge(START, "client_liaison")
    builder.add_edge("client_liaison", "human_approval")
    builder.add_edge("human_approval", "send_reply")
    builder.add_edge("send_reply", END)

    return builder.compile(checkpointer=checkpointer)
