"""Live Upwork MCP adapter (Streamable HTTP + OAuth 2.1 encrypted token store)."""

from __future__ import annotations

import os
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

UPWORK_MCP_URL = "https://mcp.upwork.com/mcp"


class UpworkLiveAdapter:
    """Adapter mapping Upwork's official MCP server onto MarketplacePort.

    - Connects over Streamable HTTP using MultiServerMCPClient.
    - Uses per-user decrypted OAuth 2.1 Bearer token.
    - All writes are draft-only; user confirms submission on Upwork.com.
    - Never scrapes or automates browser sessions.
    """

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token or os.getenv("UPWORK_OAUTH_TOKEN", "")

    def _build_client(self) -> MultiServerMCPClient:
        if not self.access_token:
            raise RuntimeError(
                "Upwork live mode requires an OAuth 2.1 access token. "
                "Connect your Upwork account in Settings."
            )
        return MultiServerMCPClient(
            {
                "upwork": {
                    "transport": "streamable_http",
                    "url": UPWORK_MCP_URL,
                    "headers": {"Authorization": f"Bearer {self.access_token}"},
                }
            }
        )

    async def _call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        client = self._build_client()
        tools = await client.get_tools()
        target = next((t for t in tools if t.name == tool_name), None)
        if target is None:
            raise RuntimeError(f"Upwork MCP tool '{tool_name}' unavailable")
        return await target.ainvoke(args)

    async def search_jobs(self, query: str = "", limit: int = 20, persona: str | None = None) -> list[dict[str, Any]]:
        res = await self._call_tool("search_jobs", {"query": query, "limit": limit})
        return res if isinstance(res, list) else res.get("jobs", [])

    async def get_job(self, job_id: str) -> dict[str, Any]:
        return await self._call_tool("get_job", {"job_id": job_id})

    async def get_client_history(self, client_id: str) -> dict[str, Any]:
        return await self._call_tool("get_client_history", {"client_id": client_id})

    async def get_market_stats(self, skills: list[str]) -> dict[str, Any]:
        return {"sample_size": 0, "p25_bid_usd": 300, "median_bid_usd": 600, "p75_bid_usd": 1200, "avg_proposals": 12.0}

    async def get_connects_balance(self, user_id: str = "default-user") -> dict[str, Any]:
        return await self._call_tool("get_connects_balance", {})

    async def create_proposal_draft(
        self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False
    ) -> dict[str, Any]:
        if dry_run:
            return {**payload, "dry_run": True, "status": "preview_live_draft"}
        return await self._call_tool(
            "create_proposal_draft",
            {
                "job_id": payload["job_id"],
                "cover_letter": payload["cover_letter"],
                "bid_amount_usd": payload["bid_amount_usd"],
                "screening_answers": payload.get("screening_answers", []),
            },
        )

    async def submit_proposal(
        self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False
    ) -> dict[str, Any]:
        # Live Upwork rule: proposals are created as drafts only; user confirms on Upwork.com.
        return {
            "draft_id": payload.get("draft_id"),
            "status": "draft_ready_for_upwork_confirmation",
            "dry_run": dry_run,
            "note": "Confirm and submit this draft directly on Upwork.",
        }

    async def list_messages(self, job_id: str) -> list[dict[str, Any]]:
        res = await self._call_tool("list_messages", {"job_id": job_id})
        return res if isinstance(res, list) else res.get("messages", [])

    async def send_message(
        self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False
    ) -> dict[str, Any]:
        if dry_run:
            return {**payload, "dry_run": True, "status": "preview_message_draft"}
        return await self._call_tool(
            "create_message_draft",
            {"job_id": payload["job_id"], "text": payload["text"]},
        )
