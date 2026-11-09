"""Single MarketplacePort interface with config-driven GigSim or Live Upwork adapter."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

import yaml

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


class MarketplacePort(Protocol):
    async def search_jobs(self, query: str = "", limit: int = 20, persona: str | None = None) -> list[dict[str, Any]]: ...
    async def get_job(self, job_id: str) -> dict[str, Any]: ...
    async def get_client_history(self, client_id: str) -> dict[str, Any]: ...
    async def get_market_stats(self, skills: list[str]) -> dict[str, Any]: ...
    async def get_connects_balance(self, user_id: str = "default-user") -> dict[str, Any]: ...
    async def create_proposal_draft(self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False) -> dict[str, Any]: ...
    async def submit_proposal(self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False) -> dict[str, Any]: ...
    async def list_messages(self, job_id: str) -> list[dict[str, Any]]: ...
    async def send_message(self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False) -> dict[str, Any]: ...


def get_marketplace_mode() -> str:
    env_mode = os.getenv("MARKETPLACE_MODE")
    if env_mode:
        return env_mode
    if CONFIG_PATH.exists():
        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        return cfg.get("marketplace", {}).get("mode", "gigsim")
    return "gigsim"


def get_marketplace_adapter(oauth_token: str | None = None) -> MarketplacePort:
    mode = get_marketplace_mode()
    if mode == "upwork_live":
        from mcp_servers.marketplace.adapters.upwork_live import UpworkLiveAdapter
        return UpworkLiveAdapter(access_token=oauth_token)
    from mcp_servers.marketplace.adapters.gigsim import GigSimAdapter
    return GigSimAdapter()
