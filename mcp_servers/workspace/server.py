"""Workspace MCP Server (calendar slots, tentative interview holds, email drafts)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

mcp = FastMCP("gigbid-workspace")

_INTERVIEW_HOLDS: list[dict[str, Any]] = []
_EMAIL_DRAFTS: list[dict[str, Any]] = []


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
def get_free_slots(days_ahead: int = 3) -> list[dict[str, str]]:
    """Return available 30-minute interview slots for the next N days."""
    base = datetime(2026, 11, 13, 14, 0, tzinfo=timezone.utc)
    slots = []
    for d in range(min(days_ahead, 7)):
        day = base + timedelta(days=d)
        for hour in (14, 17):
            start = day.replace(hour=hour)
            end = start + timedelta(minutes=30)
            slots.append({
                "slot_id": f"slot-{start.strftime('%Y%m%d-%H%M')}",
                "start_iso": start.isoformat(),
                "end_iso": end.isoformat(),
                "label": start.strftime("%a %b %d, %H:%M UTC"),
            })
    return slots


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True))
def create_interview_hold(
    job_id: str,
    slot_iso: str,
    client_name: str = "Client",
    idempotency_key: str = "hold-default",
) -> dict[str, Any]:
    """Create a tentative calendar hold for a client interview."""
    for h in _INTERVIEW_HOLDS:
        if h["idempotency_key"] == idempotency_key:
            return h
    hold = {
        "hold_id": f"hold-{len(_INTERVIEW_HOLDS)+1}",
        "job_id": job_id,
        "slot_iso": slot_iso,
        "client_name": client_name,
        "status": "tentative",
        "idempotency_key": idempotency_key,
    }
    _INTERVIEW_HOLDS.append(hold)
    return hold


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True))
def create_email_draft(
    subject: str,
    body: str,
    recipient_hint: str = "client-thread",
) -> dict[str, Any]:
    """Create a local email/follow-up draft (never auto-sent)."""
    draft = {
        "email_draft_id": f"email-{len(_EMAIL_DRAFTS)+1}",
        "subject": subject,
        "body": body,
        "recipient_hint": recipient_hint,
        "status": "draft",
    }
    _EMAIL_DRAFTS.append(draft)
    return draft


if __name__ == "__main__":
    mcp.run()
