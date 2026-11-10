"""Typed LangGraph state definitions with reducers for parallel branches (C2)."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


def _merge_dicts(a: dict[str, Any] | None, b: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(a or {})
    if b:
        out.update(b)
    return out


class GigBidState(TypedDict, total=False):
    # Identity & tracing
    thread_id: str
    trace_id: str
    user_id: str
    persona: str
    strategy: str  # X2 A/B strategy: "evidence_first" | "outcome_led"

    # Job & parallel branch outputs
    job: dict[str, Any]
    job_spec: dict[str, Any]
    risk_report: dict[str, Any]
    fit_report: dict[str, Any]
    evidence: list[dict[str, Any]]

    # Sequential decision, pricing, drafting, verification, critique & compliance
    decision: dict[str, Any]
    price_quote: dict[str, Any]
    proposal_draft: dict[str, Any]
    claim_verification: dict[str, Any]
    critiques: Annotated[list[dict[str, Any]], operator.add]
    revision_count: int
    compliance_verdict: dict[str, Any]

    # Approval & execution
    dry_run_preview: dict[str, Any]
    approval_status: str  # pending_approval | approved | edited | rejected
    human_feedback: str
    submission_result: dict[str, Any]

    # Budgets & execution trace (kept separate from working state and long-term memory)
    step_count: Annotated[int, operator.add]
    tokens_used: Annotated[int, operator.add]
    needs_attention: bool
    needs_attention_reason: str
    execution_trace: Annotated[list[dict[str, Any]], operator.add]
    errors: Annotated[list[str], operator.add]


class ConversationState(TypedDict, total=False):
    thread_id: str
    trace_id: str
    user_id: str
    persona: str
    job_id: str
    messages: list[dict[str, Any]]
    client_intent: dict[str, Any]
    draft_reply: str
    proposed_slots: list[dict[str, str]]
    approval_status: str
    send_result: dict[str, Any]
    execution_trace: Annotated[list[dict[str, Any]], operator.add]
    errors: Annotated[list[str], operator.add]
