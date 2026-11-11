"""Tenant-scoped persistent state store for jobs, pipeline board, runs, and approvals."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from gigsim.store import get_gigsim_store

STATE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "api_state.json"


class ApiStateStore:
    def __init__(self) -> None:
        self.job_runs: dict[str, dict[str, Any]] = {}  # key: f"{user_id}::{job_id}"
        self.pipeline_stages: dict[str, str] = {}  # key: f"{user_id}::{job_id}" -> drafted|submitted|viewed|replied|interview|hired|lost
        self.saved_searches: dict[str, list[str]] = {}
        self.rejection_reasons: list[str] = []
        self._load()

    def _load(self) -> None:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            self.job_runs = data.get("job_runs", {})
            self.pipeline_stages = data.get("pipeline_stages", {})
            self.saved_searches = data.get("saved_searches", {})
            self.rejection_reasons = data.get("rejection_reasons", [])

    def save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(
                {
                    "job_runs": self.job_runs,
                    "pipeline_stages": self.pipeline_stages,
                    "saved_searches": self.saved_searches,
                    "rejection_reasons": self.rejection_reasons,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def get_run(self, user_id: str, job_id: str) -> dict[str, Any] | None:
        return self.job_runs.get(f"{user_id}::{job_id}")

    def set_run(self, user_id: str, job_id: str, run_data: dict[str, Any]) -> None:
        self.job_runs[f"{user_id}::{job_id}"] = run_data
        self.save()

    def list_runs(self, user_id: str) -> list[dict[str, Any]]:
        prefix = f"{user_id}::"
        return [v for k, v in self.job_runs.items() if k.startswith(prefix)]

    def set_stage(self, user_id: str, job_id: str, stage: str) -> None:
        self.pipeline_stages[f"{user_id}::{job_id}"] = stage
        self.save()

    def get_stage(self, user_id: str, job_id: str) -> str:
        return self.pipeline_stages.get(f"{user_id}::{job_id}", "inbox")


_API_STORE: ApiStateStore | None = None


def get_api_store() -> ApiStateStore:
    global _API_STORE
    if _API_STORE is None:
        _API_STORE = ApiStateStore()
    return _API_STORE
