# GigBid Portfolio MCP Server

A read-only Model Context Protocol (MCP) server exposing verified freelancer case studies, GitHub repository summaries, client reviews, and outcome-labelled past proposals. Plug it into Claude Desktop, Cursor, or LangGraph via `langchain-mcp-adapters`.

## Tools
- `search_evidence(requirement, k=5, filters=None, persona="ai_ml_engineer")` (`readOnlyHint=True`)
- `get_case_study(id, persona="ai_ml_engineer")` (`readOnlyHint=True`)
- `list_skills(persona="ai_ml_engineer")` (`readOnlyHint=True`)

## Resources
- `portfolio://case/{id}` — Full Markdown case study
- `portfolio://proposal/{id}` — Outcome-labelled past proposal JSON

## Prompts
- `answer_screening_question` — "Answer a screening question from my portfolio"
- `draft_evidence_opening` — Evidence-backed 2-sentence opening

## Install & Run (uvx / Docker / Python)
```bash
# Local Python
python -m mcp_servers.portfolio.server

# Claude Desktop / Cursor config (~/.cursor/mcp.json)
{
  "mcpServers": {
    "gigbid-portfolio": {
      "command": "python",
      "args": ["-m", "mcp_servers.portfolio.server"],
      "cwd": "/path/to/gigbid"
    }
  }
}
```
