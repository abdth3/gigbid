"""Portfolio MCP resource templates (portfolio://case/{id}, portfolio://proposal/{id})."""

from __future__ import annotations

import json
from pathlib import Path

PERSONAS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "personas"


def read_case_resource(case_id: str) -> str:
    for pdir in PERSONAS_DIR.iterdir():
        if not pdir.is_dir():
            continue
        md_file = pdir / "case_studies" / f"{case_id}.md"
        if md_file.exists():
            return md_file.read_text(encoding="utf-8")
    return f"Case study {case_id} not found."


def read_proposal_resource(proposal_id: str) -> str:
    for pdir in PERSONAS_DIR.iterdir():
        if not pdir.is_dir():
            continue
        prop_file = pdir / "past_proposals.json"
        if prop_file.exists():
            for p in json.loads(prop_file.read_text(encoding="utf-8")):
                if p.get("proposal_id") == proposal_id:
                    return json.dumps(p, indent=2)
    return f"Proposal {proposal_id} not found."
