"""Portfolio MCP Server (read-only) built with the official MCP Python SDK."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from mcp_servers.portfolio.prompts import (
    answer_screening_question_prompt,
    draft_evidence_opening_prompt,
)
from mcp_servers.portfolio.resources import read_case_resource, read_proposal_resource
from mcp_servers.portfolio.tools import (
    get_case_study_impl,
    list_skills_impl,
    search_evidence_impl,
)

mcp = FastMCP("gigbid-portfolio")


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
    )
)
def search_evidence(
    requirement: str,
    k: int = 5,
    filters: dict[str, Any] | None = None,
    persona: str = "ai_ml_engineer",
) -> list[dict[str, Any]]:
    """Search verified freelancer portfolio evidence (case studies, repos, reviews, past proposals)."""
    return search_evidence_impl(requirement=requirement, k=k, filters=filters, persona=persona)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
    )
)
def get_case_study(id: str, persona: str = "ai_ml_engineer") -> dict[str, Any]:
    """Load a full case study or repository summary by evidence ID."""
    return get_case_study_impl(id=id, persona=persona)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
    )
)
def list_skills(persona: str = "ai_ml_engineer") -> dict[str, Any]:
    """List verified core skills for the given freelancer persona."""
    return list_skills_impl(persona=persona)


@mcp.resource("portfolio://case/{id}")
def portfolio_case_resource(id: str) -> str:
    """Load full markdown case study by ID."""
    return read_case_resource(id)


@mcp.resource("portfolio://proposal/{id}")
def portfolio_proposal_resource(id: str) -> str:
    """Load past proposal JSON with outcome label by ID."""
    return read_proposal_resource(id)


@mcp.prompt()
def answer_screening_question(question: str, persona: str = "ai_ml_engineer") -> str:
    """Answer a screening question from my portfolio."""
    return answer_screening_question_prompt(question=question, persona=persona)


@mcp.prompt()
def draft_evidence_opening(job_title: str, key_skill: str) -> str:
    """Draft an evidence-grounded 2-sentence proposal opening."""
    return draft_evidence_opening_prompt(job_title=job_title, key_skill=key_skill)


if __name__ == "__main__":
    mcp.run()
