"""MCP Client discipline: per-agent tool allowlists, timeouts, bounded retries, and degraded mode."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from mcp_servers.marketplace.server import (
    create_proposal_draft,
    get_client_history,
    get_connects_balance,
    get_job,
    list_messages,
    search_jobs,
    send_message,
    submit_proposal,
)
from mcp_servers.portfolio.server import get_case_study, list_skills, search_evidence
from mcp_servers.workspace.server import (
    create_email_draft,
    create_interview_hold,
    get_free_slots,
)

logger = logging.getLogger("gigbid.mcp_client")

# Per-agent tool allowlists (A6: each agent gets only the tools it needs)
AGENT_TOOL_ALLOWLIST: dict[str, set[str]] = {
    "scout": {"search_jobs", "get_job"},
    "analyst": set(),  # No MCP access needed
    "risk_assessor": {"get_client_history"},
    "fit_matcher": {"search_evidence", "get_case_study", "list_skills"},
    "pricing": {"get_connects_balance"},
    "writer": {"search_evidence", "get_case_study"},
    "critic": {"search_evidence", "get_case_study"},
    "compliance": set(),
    "client_liaison": {
        "list_messages",
        "send_message",
        "get_free_slots",
        "create_interview_hold",
        "create_email_draft",
    },
    "executor": {"create_proposal_draft", "submit_proposal", "send_message"},
}

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "search_jobs": search_jobs,
    "get_job": get_job,
    "get_client_history": get_client_history,
    "get_connects_balance": get_connects_balance,
    "list_messages": list_messages,
    "create_proposal_draft": create_proposal_draft,
    "submit_proposal": submit_proposal,
    "send_message": send_message,
    "search_evidence": search_evidence,
    "get_case_study": get_case_study,
    "list_skills": list_skills,
    "get_free_slots": get_free_slots,
    "create_interview_hold": create_interview_hold,
    "create_email_draft": create_email_draft,
}


class MarketplaceDegradedError(RuntimeError):
    """Raised when the marketplace MCP server is unreachable or simulated offline."""


class MCPClientRouter:
    """Routes agent tool calls with allowlists, timeouts, retries, and degraded-mode queue."""

    def __init__(self) -> None:
        self.marketplace_offline: bool = False
        self.queued_jobs: list[dict[str, Any]] = []

    def set_marketplace_offline(self, offline: bool) -> None:
        self.marketplace_offline = offline

    def get_allowed_tools(self, agent_name: str) -> list[str]:
        return sorted(AGENT_TOOL_ALLOWLIST.get(agent_name, set()))

    async def call_tool(
        self,
        agent_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        timeout_s: float = 8.0,
        max_retries: int = 2,
    ) -> Any:
        allowed = AGENT_TOOL_ALLOWLIST.get(agent_name, set())
        if tool_name not in allowed:
            raise PermissionError(f"Agent '{agent_name}' is not allowed to call tool '{tool_name}'")

        marketplace_tools = {
            "search_jobs", "get_job", "get_client_history", "get_connects_balance",
            "list_messages", "create_proposal_draft", "submit_proposal", "send_message",
        }
        if tool_name in marketplace_tools and self.marketplace_offline:
            raise MarketplaceDegradedError(
                "Marketplace MCP server is currently unavailable; work queued for recovery."
            )

        fn = TOOL_REGISTRY[tool_name]
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(fn):
                    return await asyncio.wait_for(fn(**arguments), timeout=timeout_s)
                return fn(**arguments)
            except MarketplaceDegradedError:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    await asyncio.sleep(0.05 * (2 ** attempt))
        raise RuntimeError(f"Tool '{tool_name}' failed after {max_retries + 1} attempts: {last_exc}")


_MCP_CLIENT = MCPClientRouter()


def get_mcp_client() -> MCPClientRouter:
    return _MCP_CLIENT
