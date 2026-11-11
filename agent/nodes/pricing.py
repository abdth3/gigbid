"""Pricing Strategist node: computes fair bid and Nov 2 Connects surcharge check."""

from __future__ import annotations

from typing import Any

from agent.handoffs import PriceQuote
from agent.llm_router import call_node_llm, load_config, load_prompt
from agent.marketplace_port import get_marketplace_adapter
from agent.mcp_client import get_mcp_client


async def pricing_node(state: dict[str, Any]) -> dict[str, Any]:
    job = state["job"]
    user_id = state.get("user_id", "default-user")
    trace_id = state.get("trace_id", "")

    mcp = get_mcp_client()
    bal = await mcp.call_tool(
        "pricing",
        "get_connects_balance",
        {"user_id": user_id, "trace_id": trace_id},
    )
    adapter = get_marketplace_adapter()
    stats = await adapter.get_market_stats(job.get("required_skills", []))
    llm_meta = await call_node_llm("pricing", load_prompt("pricing"), str(stats))

    budget = job.get("budget") or {}
    bmin = float(budget.get("min") or stats["p25_bid_usd"])
    bmax = float(budget.get("max") or stats["p75_bid_usd"])
    mid = round((bmin + bmax) / 2.0, 2)
    bid_amount = max(250.0, min(bmax, round(0.6 * mid + 0.4 * stats["median_bid_usd"], 2)))

    cfg = load_config().get("policy_nov2", {})
    base_connects = int(job.get("connects_cost", 8))
    surcharge = int(cfg.get("high_value_connects_surcharge", 4)) if bid_amount > float(cfg.get("high_value_bid_threshold_usd", 500)) else 0
    total_connects = base_connects + surcharge

    worth_it = bal.get("connects_balance", 0) >= total_connects and bid_amount >= 200
    quote = PriceQuote(
        bid_amount_usd=bid_amount,
        fair_band_min=round(bmin * 0.9, 2),
        fair_band_max=round(bmax * 1.05, 2),
        connects_cost=total_connects,
        connects_worth_it=worth_it,
        rationale=(
            f"Proposed ${bid_amount:.0f} (market median ${stats['median_bid_usd']:.0f}, "
            f"job band ${bmin:.0f}-${bmax:.0f}). Connects: {base_connects} + {surcharge} Nov-2 surcharge."
        ),
    )
    return {
        "price_quote": quote.model_dump(),
        "step_count": 1,
        "tokens_used": llm_meta["tokens"],
        "execution_trace": [{
            "node": "pricing",
            "tool": "get_connects_balance",
            "model": llm_meta["model"],
            "tokens": llm_meta["tokens"],
            "cost_usd": llm_meta["cost_usd"],
            "latency_ms": llm_meta["latency_ms"],
            "observation": f"Quoted ${bid_amount:.0f}, Connects={total_connects}",
            "trace_id": trace_id,
        }],
    }
