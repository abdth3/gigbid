"""Hand-written LangGraph Bid Graph with parallel Send(), Critic loop, and interrupt() (C1-C7)."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt

from agent.handoffs import BidDecision
from agent.llm_router import load_config
from agent.mcp_client import get_mcp_client
from agent.memory.store import get_memory_store
from agent.nodes.analyst import analyst_node
from agent.nodes.compliance import compliance_node
from agent.nodes.critic import critic_node
from agent.nodes.fit_matcher import fit_matcher_node
from agent.nodes.pricing import pricing_node
from agent.nodes.risk_assessor import risk_assessor_node
from agent.nodes.scout import scout_node
from agent.nodes.verifier import verifier_node
from agent.nodes.writer import writer_node
from agent.state import GigBidState


def fan_out_analysis(state: GigBidState) -> list[Send]:
    """Run Job Analyst, Risk Assessor, and Fit Matcher in parallel using LangGraph Send()."""
    return [
        Send("analyst", state),
        Send("risk_assessor", state),
        Send("fit_matcher", state),
    ]


async def decision_node(state: GigBidState) -> dict[str, Any]:
    cfg = load_config()
    thresholds = cfg.get("thresholds", {})
    budgets = cfg.get("budgets", {})
    min_fit = float(thresholds.get("minimum_fit_score", 0.55))
    max_risk = float(thresholds.get("maximum_risk_score", 0.70))

    risk = state.get("risk_report", {})
    fit = state.get("fit_report", {})
    risk_score = float(risk.get("score", 0.0))
    fit_score = float(fit.get("score", 0.0))

    # Budget guard (C4)
    if state.get("tokens_used", 0) > int(budgets.get("max_tokens_per_job", 12000)):
        return {
            "needs_attention": True,
            "needs_attention_reason": "Token budget exceeded",
            "decision": BidDecision(action="skip", reason="Token budget exceeded").model_dump(),
            "step_count": 1,
        }

    if risk.get("is_scam") or risk_score >= max_risk:
        dec = BidDecision(
            action="skip",
            reason=f"Skipped due to high risk ({risk_score}) / scam flags: {risk.get('flags', [])}",
        )
    elif fit_score < min_fit:
        dec = BidDecision(
            action="skip",
            reason=f"Skipped due to low portfolio fit ({fit_score} < {min_fit})",
        )
    else:
        dec = BidDecision(
            action="bid",
            reason=f"Recommended BID: fit={fit_score}, risk={risk_score}",
        )

    return {
        "decision": dec.model_dump(),
        "step_count": 1,
        "execution_trace": [{
            "node": "decision",
            "tool": "none",
            "model": "policy-router",
            "tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 0.3,
            "observation": f"action={dec.action} ({dec.reason})",
            "trace_id": state.get("trace_id", ""),
        }],
    }


def route_after_decision(state: GigBidState) -> str:
    action = (state.get("decision") or {}).get("action", "skip")
    return "pricing" if action == "bid" else END


def route_after_critic(state: GigBidState) -> str:
    critiques = state.get("critiques", [])
    last = critiques[-1] if critiques else {"passed": True}
    rev_count = int(state.get("revision_count", 0))
    if not last.get("passed", True) and rev_count <= 2:
        return "writer"
    return "compliance"


async def human_approval_node(state: GigBidState) -> dict[str, Any]:
    """Pause with LangGraph interrupt() and surface dry_run preview + evidence + risk + price."""
    draft = dict(state.get("proposal_draft", {}))
    price = state.get("price_quote", {})
    user_id = state.get("user_id", "default-user")
    trace_id = state.get("trace_id", "")

    mcp = get_mcp_client()
    dry_run_preview = await mcp.call_tool(
        "executor",
        "create_proposal_draft",
        {
            "job_id": draft["job_id"],
            "cover_letter": draft["cover_letter"],
            "bid_amount_usd": price.get("bid_amount_usd", 400.0),
            "screening_answers": draft.get("screening_answers", []),
            "idempotency_key": f"dry-{draft['job_id']}-{user_id}",
            "dry_run": True,
            "user_id": user_id,
            "trace_id": trace_id,
        },
    )

    # Interrupt graph execution until human approves, edits, or rejects in UI
    human_response = interrupt({
        "type": "proposal_approval",
        "job_id": draft["job_id"],
        "draft": draft,
        "evidence": state.get("evidence", []),
        "risk_report": state.get("risk_report", {}),
        "price_quote": price,
        "compliance_verdict": state.get("compliance_verdict", {}),
        "dry_run_preview": dry_run_preview,
    })

    action = (human_response or {}).get("action", "approve")
    edited_text = (human_response or {}).get("edited_cover_letter")
    reason = (human_response or {}).get("reason", "")

    if action == "edit" and edited_text:
        # Promote style rules from diff & update draft (C5 & R7)
        get_memory_store().promote_from_edit(user_id, draft["cover_letter"], edited_text)
        draft["cover_letter"] = edited_text
        draft["status"] = "edited_approved"
    elif action == "reject":
        draft["status"] = "rejected"
    else:
        draft["status"] = "approved"

    return {
        "proposal_draft": draft,
        "dry_run_preview": dry_run_preview,
        "approval_status": action,
        "human_feedback": reason,
        "step_count": 1,
    }


async def submit_approved_node(state: GigBidState) -> dict[str, Any]:
    """Submit approved proposal exactly once using idempotency_key."""
    status = state.get("approval_status", "reject")
    if status == "reject":
        return {
            "submission_result": {"status": "rejected", "reason": state.get("human_feedback", "")},
            "step_count": 1,
        }

    draft = state["proposal_draft"]
    price = state["price_quote"]
    user_id = state.get("user_id", "default-user")
    trace_id = state.get("trace_id", "")
    job_id = draft["job_id"]
    mcp = get_mcp_client()

    # Create persisted draft then submit with deterministic idempotency_key
    created = await mcp.call_tool(
        "executor",
        "create_proposal_draft",
        {
            "job_id": job_id,
            "cover_letter": draft["cover_letter"],
            "bid_amount_usd": price.get("bid_amount_usd", 400.0),
            "screening_answers": draft.get("screening_answers", []),
            "idempotency_key": f"draft-{job_id}-{user_id}",
            "dry_run": False,
            "user_id": user_id,
            "trace_id": trace_id,
        },
    )
    submitted = await mcp.call_tool(
        "executor",
        "submit_proposal",
        {
            "draft_id": created["draft_id"],
            "idempotency_key": f"submit-{job_id}-{user_id}",
            "dry_run": False,
            "user_id": user_id,
            "trace_id": trace_id,
        },
    )

    # Promote verified outcome into outcome_memory (R7)
    if submitted.get("status") in {"replied", "won"}:
        get_memory_store().promote_outcome(
            user_id=user_id,
            outcome=submitted["status"],
            category=state.get("persona", "ai_ml_engineer"),
            strategy=draft.get("strategy", "evidence_first"),
        )

    return {
        "submission_result": submitted,
        "step_count": 1,
        "execution_trace": [{
            "node": "submit_approved",
            "tool": "create_proposal_draft,submit_proposal",
            "model": "deterministic-executor",
            "tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 2.0,
            "observation": f"Submitted draft {created['draft_id']} -> {submitted.get('status')}",
            "trace_id": trace_id,
        }],
    }


def build_bid_graph(checkpointer: Any = None):
    builder = StateGraph(GigBidState)

    builder.add_node("scout", scout_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("risk_assessor", risk_assessor_node)
    builder.add_node("fit_matcher", fit_matcher_node)
    builder.add_node("decision", decision_node)
    builder.add_node("pricing", pricing_node)
    builder.add_node("writer", writer_node)
    builder.add_node("verifier", verifier_node)
    builder.add_node("critic", critic_node)
    builder.add_node("compliance", compliance_node)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("submit_approved", submit_approved_node)

    builder.add_edge(START, "scout")
    builder.add_conditional_edges("scout", fan_out_analysis, ["analyst", "risk_assessor", "fit_matcher"])
    builder.add_edge("analyst", "decision")
    builder.add_edge("risk_assessor", "decision")
    builder.add_edge("fit_matcher", "decision")

    builder.add_conditional_edges("decision", route_after_decision, {"pricing": "pricing", END: END})
    builder.add_edge("pricing", "writer")
    builder.add_edge("writer", "verifier")
    builder.add_edge("verifier", "critic")
    builder.add_conditional_edges("critic", route_after_critic, {"writer": "writer", "compliance": "compliance"})
    builder.add_edge("compliance", "human_approval")
    builder.add_edge("human_approval", "submit_approved")
    builder.add_edge("submit_approved", END)

    return builder.compile(checkpointer=checkpointer)
