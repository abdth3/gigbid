"""Analytics dashboard routes (reply/hire rates, Connects spent, cost/latency, X2 A/B results)."""

from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter, Depends

from apps.api.auth.security import get_current_user
from apps.api.state_store import get_api_store
from gigsim.store import get_gigsim_store

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "evals" / "results"


@router.get("")
def get_analytics(user: dict = Depends(get_current_user)):
    api_store = get_api_store()
    runs = api_store.list_runs(user["user_id"])
    gigsim = get_gigsim_store()

    total_runs = len(runs)
    submitted = [r for r in runs if r.get("approval_status") in {"approve", "edit", "approved", "edited"}]
    replied = [r for r in submitted if (r.get("submission_result") or {}).get("status") == "replied"]
    connects_spent = sum((r.get("submission_result") or {}).get("connects_spent", 0) for r in submitted)
    total_tokens = sum(r.get("tokens_used", 0) for r in runs)

    eval_summary = {}
    for fname in ("rag_eval.json", "multi_agent_eval.json", "x2_ab_results.json", "hidden_budget_summary.json"):
        fpath = RESULTS_DIR / fname
        if fpath.exists():
            eval_summary[fname.replace(".json", "")] = json.loads(fpath.read_text(encoding="utf-8"))

    return {
        "live_metrics": {
            "total_jobs_analyzed": total_runs,
            "proposals_submitted": len(submitted),
            "client_replies": len(replied),
            "reply_rate": round(len(replied) / max(1, len(submitted)), 3),
            "connects_spent": connects_spent,
            "connects_balance": gigsim.get_connects_balance(user["user_id"])["connects_balance"],
            "avg_tokens_per_job": round(total_tokens / max(1, total_runs), 1),
            "top_rejection_reasons": api_store.rejection_reasons[-5:],
        },
        "eval_results": eval_summary,
    }
