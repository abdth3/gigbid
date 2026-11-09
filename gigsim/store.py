"""GigSim state store, rate limiter, and simulated client decision engine."""

from __future__ import annotations

import json
import os
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DEV_JOBS_PATH = ROOT / "evals" / "datasets" / "dev_jobs.json"
CLIENTS_PATH = DATA_DIR / "gigsim_clients.json"
HIST_JOBS_PATH = DATA_DIR / "historical_jobs.json"


class RateLimitExceeded(Exception):
    """Raised when caller exceeds GigSim per-user RPM limit."""


class SimulatedServerError(Exception):
    """Raised to simulate occasional 5xx marketplace failures."""


class GigSimStore:
    """In-memory + JSON-seeded marketplace simulator."""

    def __init__(self, rpm_limit: int = 60, error_rate: float = 0.0) -> None:
        self.rpm_limit = rpm_limit
        self.error_rate = error_rate
        self.rng = random.Random(42)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.clients: dict[str, dict[str, Any]] = {}
        self.historical_jobs: list[dict[str, Any]] = []
        self.connects: dict[str, int] = defaultdict(lambda: 120)
        self.drafts: dict[str, dict[str, Any]] = {}
        self.proposals: dict[str, dict[str, Any]] = {}
        self.messages: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.idempotency_cache: dict[str, dict[str, Any]] = {}
        self.request_timestamps: dict[str, list[float]] = defaultdict(list)
        self._load_seed_data()

    def _load_seed_data(self) -> None:
        if DEV_JOBS_PATH.exists():
            dev_jobs = json.loads(DEV_JOBS_PATH.read_text(encoding="utf-8"))
            for job in dev_jobs:
                self.jobs[job["job_id"]] = job
        if CLIENTS_PATH.exists():
            clients = json.loads(CLIENTS_PATH.read_text(encoding="utf-8"))
            for c in clients:
                self.clients[c["client_id"]] = c
        if HIST_JOBS_PATH.exists():
            self.historical_jobs = json.loads(HIST_JOBS_PATH.read_text(encoding="utf-8"))

    def check_rate_limit(self, user_id: str) -> None:
        now = time.time()
        window = [t for t in self.request_timestamps[user_id] if now - t < 60.0]
        if len(window) >= self.rpm_limit:
            raise RateLimitExceeded(f"Rate limit {self.rpm_limit} RPM exceeded for {user_id}")
        window.append(now)
        self.request_timestamps[user_id] = window
        if self.error_rate > 0 and self.rng.random() < self.error_rate:
            raise SimulatedServerError("GigSim transient 503 Service Unavailable")

    def search_jobs(self, query: str = "", limit: int = 20, persona: str | None = None) -> list[dict[str, Any]]:
        q = query.lower().strip()
        results = []
        for job in self.jobs.values():
            if persona and job.get("persona_target") != persona:
                continue
            if not q or q in job["title"].lower() or q in job["description"].lower() or any(
                q in s.lower() for s in job.get("required_skills", [])
            ):
                results.append(job)
            if len(results) >= limit:
                break
        return results

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    def get_client_history(self, client_id: str) -> dict[str, Any]:
        client = self.clients.get(client_id)
        if not client:
            return {
                "client_id": client_id,
                "name": "Unknown Client",
                "payment_verified": False,
                "completed_projects": 0,
                "average_rating": 0.0,
                "total_spent_usd": 0,
                "hire_rate": 0.0,
            }
        # Never expose hidden_preferences to agents!
        return {k: v for k, v in client.items() if k != "hidden_preferences"}

    def get_market_stats(self, skills: list[str]) -> dict[str, Any]:
        skill_set = {s.lower() for s in skills}
        matched = [
            h for h in self.historical_jobs
            if skill_set & {s.lower() for s in h.get("required_skills", [])}
        ]
        if not matched:
            matched = self.historical_jobs[:50]
        bids = sorted(h["winning_bid"] for h in matched)
        n = len(bids)
        return {
            "sample_size": n,
            "p25_bid_usd": bids[max(0, int(n * 0.25))],
            "median_bid_usd": bids[n // 2],
            "p75_bid_usd": bids[min(n - 1, int(n * 0.75))],
            "avg_proposals": round(sum(h["proposals_count"] for h in matched) / max(1, n), 1),
        }

    def get_connects_balance(self, user_id: str) -> dict[str, Any]:
        return {"user_id": user_id, "connects_balance": self.connects[user_id]}

    def compute_connects_cost(self, job_id: str, bid_amount_usd: float) -> int:
        job = self.jobs.get(job_id, {})
        base_cost = int(job.get("connects_cost", 8))
        # Nov 2, 2026 Platform Policy Update: +4 Connects surcharge for bids > $500
        surcharge = 4 if bid_amount_usd > 500 else 0
        return base_cost + surcharge

    def create_proposal_draft(
        self,
        user_id: str,
        job_id: str,
        cover_letter: str,
        bid_amount_usd: float,
        screening_answers: list[str],
        idempotency_key: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        if idempotency_key in self.idempotency_cache and not dry_run:
            return self.idempotency_cache[idempotency_key]

        connects_required = self.compute_connects_cost(job_id, bid_amount_usd)
        preview = {
            "draft_id": f"draft-{job_id}-{user_id}",
            "job_id": job_id,
            "user_id": user_id,
            "bid_amount_usd": bid_amount_usd,
            "connects_required": connects_required,
            "cover_letter_chars": len(cover_letter),
            "screening_answers_count": len(screening_answers),
            "dry_run": dry_run,
            "status": "preview" if dry_run else "draft_created",
        }
        if dry_run:
            return preview

        draft_record = {
            **preview,
            "cover_letter": cover_letter,
            "screening_answers": screening_answers,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.drafts[draft_record["draft_id"]] = draft_record
        self.idempotency_cache[idempotency_key] = draft_record
        return draft_record

    def submit_proposal(
        self,
        user_id: str,
        draft_id: str,
        idempotency_key: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        if idempotency_key in self.idempotency_cache and not dry_run:
            return self.idempotency_cache[idempotency_key]

        draft = self.drafts.get(draft_id)
        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        connects_cost = draft["connects_required"]
        if dry_run:
            return {
                "draft_id": draft_id,
                "job_id": draft["job_id"],
                "connects_to_spend": connects_cost,
                "remaining_connects_after": self.connects[user_id] - connects_cost,
                "dry_run": True,
                "status": "preview",
            }

        if self.connects[user_id] < connects_cost:
            raise ValueError("Insufficient Connects balance")

        self.connects[user_id] -= connects_cost
        prop_id = f"prop-{draft['job_id']}-{user_id}"
        outcome = self.simulate_client_outcome(draft["job_id"], draft["cover_letter"], draft["bid_amount_usd"])
        record = {
            "proposal_id": prop_id,
            "draft_id": draft_id,
            "job_id": draft["job_id"],
            "user_id": user_id,
            "bid_amount_usd": draft["bid_amount_usd"],
            "connects_spent": connects_cost,
            "status": outcome["status"],
            "client_reply": outcome.get("reply_text"),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "dry_run": False,
        }
        self.proposals[prop_id] = record
        if outcome.get("reply_text"):
            self.messages[draft["job_id"]].append({
                "message_id": f"msg-{len(self.messages[draft['job_id']])+1}",
                "job_id": draft["job_id"],
                "sender": "client",
                "text": outcome["reply_text"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        self.idempotency_cache[idempotency_key] = record
        return record

    def simulate_client_outcome(self, job_id: str, cover_letter: str, bid_amount_usd: float) -> dict[str, Any]:
        """Hidden client decision engine: checks evidence specificity, generic openings, and budget ceiling."""
        job = self.jobs.get(job_id, {})
        client = self.clients.get(job.get("client_id", ""), {})
        prefs = client.get("hidden_preferences", {})

        lower = cover_letter.lower()
        generic_phrases = ["dear sir/madam", "i am passionate", "100% guarantee", "kindly hire me"]
        is_generic = any(p in lower for p in generic_phrases)
        has_evidence = ("[" in cover_letter and "]" in cover_letter) or any(
            kw in lower for kw in ["reduced", "achieved", "improved", "delivered", "%", "ms", "f1", "case"]
        )
        budget_max = prefs.get("budget_ceiling", job.get("budget", {}).get("max", 1000))
        within_budget = bid_amount_usd <= budget_max * 1.15

        score = 0.25
        if has_evidence:
            score += 0.35
        if within_budget:
            score += 0.20
        if not is_generic:
            score += 0.15
        if job.get("is_scam"):
            score = 0.05

        if score >= 0.80:
            return {
                "status": "replied",
                "replied": True,
                "hired": score >= 0.90,
                "reply_text": (
                    f"Hi! Thanks for sharing specific outcomes on similar work. "
                    f"We'd like to schedule a 20-minute technical chat to discuss {job.get('title', 'this project')}. "
                    f"Are you available Thursday or Friday afternoon?"
                ),
            }
        elif score >= 0.65:
            return {
                "status": "viewed",
                "replied": False,
                "hired": False,
                "reply_text": None,
            }
        return {"status": "submitted", "replied": False, "hired": False, "reply_text": None}

    def list_messages(self, job_id: str) -> list[dict[str, Any]]:
        return list(self.messages.get(job_id, []))

    def send_message(
        self,
        user_id: str,
        job_id: str,
        text: str,
        idempotency_key: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        if idempotency_key in self.idempotency_cache and not dry_run:
            return self.idempotency_cache[idempotency_key]

        preview = {
            "job_id": job_id,
            "user_id": user_id,
            "text": text,
            "dry_run": dry_run,
            "status": "preview" if dry_run else "sent",
        }
        if dry_run:
            return preview

        msg = {
            "message_id": f"msg-{len(self.messages[job_id])+1}",
            "job_id": job_id,
            "sender": "freelancer",
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.messages[job_id].append(msg)
        self.idempotency_cache[idempotency_key] = msg
        return msg


_GLOBAL_STORE: GigSimStore | None = None


def get_gigsim_store() -> GigSimStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = GigSimStore()
    return _GLOBAL_STORE
