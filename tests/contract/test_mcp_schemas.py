"""Contract tests: MCP tool schemas, annotations, and snapshot stability (A7)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp_servers.marketplace.server import mcp as marketplace_mcp
from mcp_servers.portfolio.server import mcp as portfolio_mcp
from mcp_servers.workspace.server import mcp as workspace_mcp

SNAPSHOT_PATH = Path(__file__).resolve().parent / "mcp_schema_snapshot.json"


async def _collect_tools() -> dict[str, dict]:
    out = {}
    for srv_name, srv in [
        ("portfolio", portfolio_mcp),
        ("marketplace", marketplace_mcp),
        ("workspace", workspace_mcp),
    ]:
        tools = await srv.list_tools()
        for t in tools:
            out[f"{srv_name}.{t.name}"] = {
                "readOnlyHint": t.annotations.readOnlyHint if t.annotations else None,
                "destructiveHint": t.annotations.destructiveHint if t.annotations else None,
                "idempotentHint": t.annotations.idempotentHint if t.annotations else None,
                "required_params": t.inputSchema.get("required", []),
            }
    return out


def test_mcp_tool_contracts_and_snapshot():
    current = asyncio.run(_collect_tools())
    expected_tools = {
        "portfolio.search_evidence",
        "portfolio.get_case_study",
        "portfolio.list_skills",
        "marketplace.search_jobs",
        "marketplace.get_job",
        "marketplace.get_client_history",
        "marketplace.get_connects_balance",
        "marketplace.list_messages",
        "marketplace.create_proposal_draft",
        "marketplace.submit_proposal",
        "marketplace.send_message",
        "workspace.get_free_slots",
        "workspace.create_interview_hold",
        "workspace.create_email_draft",
    }
    assert expected_tools.issubset(set(current.keys()))
    assert current["portfolio.search_evidence"]["readOnlyHint"] is True
    assert current["marketplace.submit_proposal"]["destructiveHint"] is True
    assert current["marketplace.submit_proposal"]["idempotentHint"] is True

    if not SNAPSHOT_PATH.exists():
        SNAPSHOT_PATH.write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
    else:
        saved = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        assert current == saved, "MCP tool schema snapshot changed unintentionally!"
