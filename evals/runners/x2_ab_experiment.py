"""Signature Extension X2: A/B test of Proposal Strategies in GigSim with z-test."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
from typing import Any

from agent.graphs.bid_graph import build_bid_graph
from gigsim.store import get_gigsim_store

ROOT = Path(__file__).resolve().parent.parent.parent
DEV_JOBS_PATH = ROOT / "evals" / "datasets" / "dev_jobs.json"
RESULTS_DIR = ROOT / "evals" / "results"


def _two_prop_z_test(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    p1 = x1 / max(1, n1)
    p2 = x2 / max(1, n2)
    p_pool = (x1 + x2) / max(1, n1 + n2)
    se = math.sqrt(max(1e-9, p_pool * (1 - p_pool) * (1 / max(1, n1) + 1 / max(1, n2))))
    z = (p2 - p1) / se
    # Approximate two-sided p-value using complementary error function
    p_val = math.erfc(abs(z) / math.sqrt(2.0))
    return round(z, 3), round(p_val, 4)


async def run_x2_ab_experiment() -> dict[str, Any]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dev_jobs = json.loads(DEV_JOBS_PATH.read_text(encoding="utf-8"))
    bid_jobs = [j for j in dev_jobs if j["gold_decision"] == "bid"][:60]
    half = len(bid_jobs) // 2
    arm_a_jobs = bid_jobs[:half]
    arm_b_jobs = bid_jobs[half:]

    graph = build_bid_graph(checkpointer=None)
    gigsim = get_gigsim_store()

    async def eval_arm(jobs: list[dict], strategy: str) -> tuple[int, int]:
        replied = 0
        for j in jobs:
            res = await graph.ainvoke({
                "thread_id": f"x2-{strategy}-{j['job_id']}",
                "trace_id": f"x2-trace-{j['job_id']}",
                "user_id": "x2-eval",
                "persona": j["persona_target"],
                "strategy": strategy,
                "job": j,
                "revision_count": 0,
            })
            draft = res.get("proposal_draft")
            if draft:
                out = gigsim.simulate_client_outcome(
                    j["job_id"],
                    draft["cover_letter"],
                    (res.get("price_quote") or {}).get("bid_amount_usd", 450),
                )
                if out["replied"]:
                    replied += 1
        return replied, len(jobs)

    rep_a, n_a = await eval_arm(arm_a_jobs, "evidence_first")
    rep_b, n_b = await eval_arm(arm_b_jobs, "outcome_led")
    z_stat, p_val = _two_prop_z_test(rep_a, n_a, rep_b, n_b)

    out = {
        "arm_a": {"strategy": "evidence_first", "n": n_a, "replies": rep_a, "reply_rate": round(rep_a / max(1, n_a), 3)},
        "arm_b": {"strategy": "outcome_led", "n": n_b, "replies": rep_b, "reply_rate": round(rep_b / max(1, n_b), 3)},
        "z_statistic": z_stat,
        "p_value": p_val,
        "significant_at_0_05": p_val < 0.05,
    }
    (RESULTS_DIR / "x2_ab_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(asyncio.run(run_x2_ab_experiment()))
