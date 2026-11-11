"""Background worker for scheduled scouting and idempotent job analysis (E1)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from agent.graphs.bid_graph import build_bid_graph
from agent.graphs.checkpointer import get_async_checkpointer
from agent.mcp_client import get_mcp_client

PROCESSED_IDS_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "worker_processed.json"


def _load_processed() -> set[str]:
    if PROCESSED_IDS_PATH.exists():
        return set(json.loads(PROCESSED_IDS_PATH.read_text(encoding="utf-8")))
    return set()


def _save_processed(ids: set[str]) -> None:
    PROCESSED_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROCESSED_IDS_PATH.write_text(json.dumps(sorted(ids), indent=2), encoding="utf-8")


async def run_scheduled_scout(user_id: str = "reviewer", persona: str = "ai_ml_engineer", limit: int = 5) -> list[str]:
    """Idempotently scout new jobs and run Bid Graph up to human_approval interrupt."""
    processed = _load_processed()
    mcp = get_mcp_client()
    jobs = await mcp.call_tool(
        "scout",
        "search_jobs",
        {"query": "", "limit": limit, "persona": persona, "user_id": user_id},
    )
    checkpointer = await get_async_checkpointer()
    graph = build_bid_graph(checkpointer=checkpointer)

    newly_processed: list[str] = []
    for job in jobs:
        jid = job["job_id"]
        key = f"{user_id}::{jid}"
        if key in processed:
            continue
        thread_id = f"bid-{user_id}-{jid}"
        await graph.ainvoke(
            {
                "thread_id": thread_id,
                "trace_id": f"worker-{jid}",
                "user_id": user_id,
                "persona": persona,
                "job": job,
                "revision_count": 0,
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        processed.add(key)
        newly_processed.append(jid)

    _save_processed(processed)
    return newly_processed


if __name__ == "__main__":
    res = asyncio.run(run_scheduled_scout())
    print(f"Worker processed {len(res)} new jobs: {res}")
