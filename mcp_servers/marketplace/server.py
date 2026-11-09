"""Marketplace MCP Server wrapping GigSim or Live Upwork via MarketplacePort."""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from agent.marketplace_port import get_marketplace_adapter

AUDIT_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "mcp_audit.jsonl"

mcp = FastMCP("gigbid-marketplace")

_RATE_WINDOWS: dict[str, list[float]] = defaultdict(list)


def _check_auth_and_rate_limit(user_id: str, bearer_token: str | None = None) -> None:
    expected = os.getenv("MCP_BEARER_TOKEN", "")
    if expected and bearer_token != expected:
        raise PermissionError("Invalid bearer token for Marketplace MCP server")
    now = time.time()
    rpm_limit = int(os.getenv("MARKETPLACE_MAX_RPM", "30"))
    win = [t for t in _RATE_WINDOWS[user_id] if now - t < 60.0]
    if len(win) >= rpm_limit:
        raise RuntimeError(f"Per-user rate limit ({rpm_limit} RPM) exceeded for {user_id}")
    win.append(now)
    _RATE_WINDOWS[user_id] = win


def _audit(user_id: str, tool: str, arguments: dict[str, Any], result: Any, trace_id: str = "") -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user_id,
        "tool": tool,
        "arguments": arguments,
        "result_summary": str(result)[:300],
        "trace_id": trace_id,
    }
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


class CreateDraftOutput(BaseModel):
    draft_id: str
    job_id: str
    bid_amount_usd: float
    connects_required: int
    dry_run: bool
    status: str


class SubmitProposalOutput(BaseModel):
    proposal_id: str | None = None
    draft_id: str
    job_id: str | None = None
    status: str
    dry_run: bool


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
async def search_jobs(
    query: str = "",
    limit: int = 20,
    persona: str | None = None,
    user_id: str = "default-user",
    trace_id: str = "",
) -> list[dict[str, Any]]:
    """Search available freelance jobs on the configured marketplace."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.search_jobs(query=query, limit=limit, persona=persona)
    _audit(user_id, "search_jobs", {"query": query, "limit": limit, "persona": persona}, {"count": len(res)}, trace_id)
    return res


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
async def get_job(job_id: str, user_id: str = "default-user", trace_id: str = "") -> dict[str, Any]:
    """Fetch full details for a single job posting."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.get_job(job_id)
    _audit(user_id, "get_job", {"job_id": job_id}, {"title": res.get("title")}, trace_id)
    return res


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
async def get_client_history(client_id: str, user_id: str = "default-user", trace_id: str = "") -> dict[str, Any]:
    """Fetch client payment verification, spend, rating, and hire rate history."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.get_client_history(client_id)
    _audit(user_id, "get_client_history", {"client_id": client_id}, res, trace_id)
    return res


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
async def get_connects_balance(user_id: str = "default-user", trace_id: str = "") -> dict[str, Any]:
    """Fetch current Connects balance for the user."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.get_connects_balance(user_id)
    _audit(user_id, "get_connects_balance", {"user_id": user_id}, res, trace_id)
    return res


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
async def list_messages(job_id: str, user_id: str = "default-user", trace_id: str = "") -> list[dict[str, Any]]:
    """List client conversation messages for a job thread."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.list_messages(job_id)
    _audit(user_id, "list_messages", {"job_id": job_id}, {"count": len(res)}, trace_id)
    return res


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True))
async def create_proposal_draft(
    job_id: str,
    cover_letter: str = Field(..., min_length=20, max_length=1800),
    bid_amount_usd: float = Field(..., gt=0, le=50000),
    screening_answers: list[str] = Field(default_factory=list),
    idempotency_key: str = Field(..., min_length=4),
    dry_run: bool = False,
    user_id: str = "default-user",
    trace_id: str = "",
) -> dict[str, Any]:
    """Create a proposal draft (or dry_run preview) with idempotency protection."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.create_proposal_draft(
        payload={
            "user_id": user_id,
            "job_id": job_id,
            "cover_letter": cover_letter,
            "bid_amount_usd": bid_amount_usd,
            "screening_answers": screening_answers,
        },
        idempotency_key=idempotency_key,
        dry_run=dry_run,
    )
    _audit(user_id, "create_proposal_draft", {"job_id": job_id, "bid_amount_usd": bid_amount_usd, "dry_run": dry_run}, res, trace_id)
    return res


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
async def submit_proposal(
    draft_id: str = Field(..., min_length=3),
    idempotency_key: str = Field(..., min_length=4),
    dry_run: bool = False,
    user_id: str = "default-user",
    trace_id: str = "",
) -> dict[str, Any]:
    """Submit an approved proposal draft and spend Connects (idempotent)."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.submit_proposal(
        payload={"user_id": user_id, "draft_id": draft_id},
        idempotency_key=idempotency_key,
        dry_run=dry_run,
    )
    _audit(user_id, "submit_proposal", {"draft_id": draft_id, "dry_run": dry_run}, res, trace_id)
    return res


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
async def send_message(
    job_id: str,
    text: str = Field(..., min_length=2, max_length=2000),
    idempotency_key: str = Field(..., min_length=4),
    dry_run: bool = False,
    user_id: str = "default-user",
    trace_id: str = "",
) -> dict[str, Any]:
    """Send an approved client message (or dry_run preview) with idempotency protection."""
    _check_auth_and_rate_limit(user_id)
    adapter = get_marketplace_adapter()
    res = await adapter.send_message(
        payload={"user_id": user_id, "job_id": job_id, "text": text},
        idempotency_key=idempotency_key,
        dry_run=dry_run,
    )
    _audit(user_id, "send_message", {"job_id": job_id, "dry_run": dry_run}, res, trace_id)
    return res


if __name__ == "__main__":
    mcp.run()
