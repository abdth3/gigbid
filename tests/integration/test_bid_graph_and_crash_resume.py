"""Integration tests: BidGraph vs GigSim, idempotency, crash-and-resume durability, and degraded mode."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from agent.graphs.bid_graph import build_bid_graph
from agent.mcp_client import MarketplaceDegradedError, get_mcp_client
from gigsim.store import get_gigsim_store

DEV_JOBS_PATH = Path(__file__).resolve().parent.parent.parent / "evals" / "datasets" / "dev_jobs.json"


def test_scam_job_is_skipped():
    jobs = json.loads(DEV_JOBS_PATH.read_text(encoding="utf-8"))
    scam_job = next(j for j in jobs if j["is_scam"])
    graph = build_bid_graph(checkpointer=MemorySaver())
    res = asyncio.run(
        graph.ainvoke(
            {"thread_id": "test-scam", "trace_id": "t-scam", "user_id": "test-u", "persona": "ai_ml_engineer", "job": scam_job, "revision_count": 0},
            config={"configurable": {"thread_id": "test-scam"}},
        )
    )
    assert res["decision"]["action"] == "skip"
    assert res["risk_report"]["is_scam"] is True


def test_interrupt_crash_resume_submits_exactly_once():
    jobs = json.loads(DEV_JOBS_PATH.read_text(encoding="utf-8"))
    good_job = next(j for j in jobs if j["gold_decision"] == "bid" and j["persona_target"] == "ai_ml_engineer")

    saver = MemorySaver()
    graph1 = build_bid_graph(checkpointer=saver)
    cfg = {"configurable": {"thread_id": "test-crash-resume"}}

    asyncio.run(
        graph1.ainvoke(
            {"thread_id": "test-crash-resume", "trace_id": "t-cr", "user_id": "crash-user", "persona": "ai_ml_engineer", "job": good_job, "revision_count": 0},
            config=cfg,
        )
    )
    # Simulate API crash & rebuild graph using same persisted checkpointer
    graph2 = build_bid_graph(checkpointer=saver)
    snap = asyncio.run(graph2.aget_state(cfg))
    assert snap.next, "Graph should be paused at human_approval interrupt"

    bal_before = get_gigsim_store().get_connects_balance("crash-user")["connects_balance"]
    res = asyncio.run(graph2.ainvoke(Command(resume={"action": "approve"}), config=cfg))
    bal_after = get_gigsim_store().get_connects_balance("crash-user")["connects_balance"]
    assert res["submission_result"]["proposal_id"].startswith("prop-")
    assert bal_after < bal_before

    # Verify idempotency: retrying submit with same idempotency_key does not double-spend Connects
    mcp = get_mcp_client()
    asyncio.run(
        mcp.call_tool(
            "executor",
            "submit_proposal",
            {"draft_id": res["submission_result"]["draft_id"], "idempotency_key": f"submit-{good_job['job_id']}-crash-user", "user_id": "crash-user"},
        )
    )
    assert get_gigsim_store().get_connects_balance("crash-user")["connects_balance"] == bal_after


def test_degraded_mode_raises_and_recovers():
    mcp = get_mcp_client()
    mcp.set_marketplace_offline(True)
    try:
        try:
            asyncio.run(mcp.call_tool("scout", "search_jobs", {"query": "", "limit": 1}))
            assert False, "Expected MarketplaceDegradedError"
        except MarketplaceDegradedError:
            pass
    finally:
        mcp.set_marketplace_offline(False)
