"""SSE streaming bridge for LangGraph node-by-node progress (Part D)."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator


async def stream_graph_events(graph, initial_state: dict, config: dict) -> AsyncGenerator[str, None]:
    """Yield Server-Sent Events from LangGraph astream(stream_mode='updates')."""
    yield f"data: {json.dumps({'event': 'run_started', 'thread_id': config['configurable']['thread_id']})}\n\n"
    async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
        for node_name, update in chunk.items():
            payload = {
                "event": "node_update",
                "node": node_name,
                "keys": list(update.keys()) if isinstance(update, dict) else [],
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.01)
    yield f"data: {json.dumps({'event': 'run_paused_or_finished', 'thread_id': config['configurable']['thread_id']})}\n\n"
