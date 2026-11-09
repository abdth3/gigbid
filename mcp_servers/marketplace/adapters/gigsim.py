"""GigSim marketplace adapter implementing MarketplacePort."""

from __future__ import annotations

import os
from typing import Any

import httpx

from gigsim.store import get_gigsim_store


class GigSimAdapter:
    """Adapter that talks to GigSim via HTTP (when GIGSIM_HTTP=1) or in-process store."""

    def __init__(self, base_url: str | None = None, api_token: str | None = None) -> None:
        self.base_url = base_url or os.getenv("GIGSIM_BASE_URL", "")
        self.api_token = api_token or os.getenv("GIGSIM_API_TOKEN", "local-dev-token")
        self.use_http = os.getenv("GIGSIM_USE_HTTP", "0") == "1" and bool(self.base_url)

    async def search_jobs(self, query: str = "", limit: int = 20, persona: str | None = None) -> list[dict[str, Any]]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/jobs",
                    params={"query": query, "limit": limit, "persona": persona},
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()["jobs"]
        return get_gigsim_store().search_jobs(query=query, limit=limit, persona=persona)

    async def get_job(self, job_id: str) -> dict[str, Any]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/jobs/{job_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()
        job = get_gigsim_store().get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job

    async def get_client_history(self, client_id: str) -> dict[str, Any]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/clients/{client_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()
        return get_gigsim_store().get_client_history(client_id)

    async def get_market_stats(self, skills: list[str]) -> dict[str, Any]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/market-stats",
                    params={"skills": ",".join(skills)},
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()
        return get_gigsim_store().get_market_stats(skills)

    async def get_connects_balance(self, user_id: str = "default-user") -> dict[str, Any]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/connects/{user_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()
        return get_gigsim_store().get_connects_balance(user_id)

    async def create_proposal_draft(
        self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False
    ) -> dict[str, Any]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{self.base_url}/proposals/draft",
                    json={**payload, "idempotency_key": idempotency_key, "dry_run": dry_run},
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()
        return get_gigsim_store().create_proposal_draft(
            user_id=payload.get("user_id", "default-user"),
            job_id=payload["job_id"],
            cover_letter=payload["cover_letter"],
            bid_amount_usd=payload["bid_amount_usd"],
            screening_answers=payload.get("screening_answers", []),
            idempotency_key=idempotency_key,
            dry_run=dry_run,
        )

    async def submit_proposal(
        self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False
    ) -> dict[str, Any]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{self.base_url}/proposals/submit",
                    json={**payload, "idempotency_key": idempotency_key, "dry_run": dry_run},
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()
        return get_gigsim_store().submit_proposal(
            user_id=payload.get("user_id", "default-user"),
            draft_id=payload["draft_id"],
            idempotency_key=idempotency_key,
            dry_run=dry_run,
        )

    async def list_messages(self, job_id: str) -> list[dict[str, Any]]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    f"{self.base_url}/messages/{job_id}",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()["messages"]
        return get_gigsim_store().list_messages(job_id)

    async def send_message(
        self, payload: dict[str, Any], idempotency_key: str, dry_run: bool = False
    ) -> dict[str, Any]:
        if self.use_http:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{self.base_url}/messages/send",
                    json={**payload, "idempotency_key": idempotency_key, "dry_run": dry_run},
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                r.raise_for_status()
                return r.json()
        return get_gigsim_store().send_message(
            user_id=payload.get("user_id", "default-user"),
            job_id=payload["job_id"],
            text=payload["text"],
            idempotency_key=idempotency_key,
            dry_run=dry_run,
        )
