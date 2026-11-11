"""Client Liaison node: classifies client intent, proposes calendar slots, drafts reply."""

from __future__ import annotations

from typing import Any

from agent.handoffs import ClientIntent
from agent.llm_router import call_node_llm, load_prompt, mask_pii
from agent.mcp_client import get_mcp_client


async def client_liaison_node(state: dict[str, Any]) -> dict[str, Any]:
    job_id = state["job_id"]
    trace_id = state.get("trace_id", "")
    user_id = state.get("user_id", "default-user")
    mcp = get_mcp_client()

    messages = state.get("messages")
    if not messages:
        messages = await mcp.call_tool(
            "client_liaison",
            "list_messages",
            {"job_id": job_id, "user_id": user_id, "trace_id": trace_id},
        )

    latest_text = messages[-1]["text"] if messages else "Thanks for your proposal! Can we chat?"
    lower = latest_text.lower()

    if any(w in lower for w in ["telegram", "whatsapp", "free sample", "pay outside"]):
        intent_type = "scam_signal"
        reply = "Thank you for reaching out. All project communication and payments must remain on the platform per policy."
        slots = []
        flags = ["off_platform_or_scam_signal"]
    elif any(w in lower for w in ["chat", "call", "interview", "available", "schedule", "thursday", "friday"]):
        intent_type = "interview_request"
        slots = await mcp.call_tool("client_liaison", "get_free_slots", {"days_ahead": 3})
        slot_labels = ", ".join(s["label"] for s in slots[:2])
        reply = f"Great! I would be glad to walk through the architecture. I am available at: {slot_labels}. Which works best?"
        flags = []
    elif any(w in lower for w in ["budget", "rate", "price", "discount", "lower"]):
        intent_type = "negotiation"
        slots = []
        reply = "Happy to adjust scope to fit your budget ceiling—we can prioritize the core deliverable in Milestone 1."
        flags = []
    else:
        intent_type = "question"
        slots = []
        reply = "Thanks for your question! I can share the technical breakdown and evaluation plan right here."
        flags = []

    llm_meta = await call_node_llm("client_liaison", load_prompt("client_liaison"), mask_pii(latest_text))
    intent = ClientIntent(
        intent=intent_type,
        confidence=0.92,
        suggested_reply=reply,
        proposed_slots=slots[:3],
        flags=flags,
    )
    return {
        "messages": messages,
        "client_intent": intent.model_dump(),
        "draft_reply": reply,
        "proposed_slots": slots[:3],
        "execution_trace": [{
            "node": "client_liaison",
            "tool": "list_messages,get_free_slots",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"Classified intent={intent_type}, slots={len(slots[:3])}",
            "trace_id": trace_id,
        }],
    }
