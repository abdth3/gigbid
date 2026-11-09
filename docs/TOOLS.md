# MCP Tool Surface (`docs/TOOLS.md`)

## 1. Own MCP Servers

| Tool Name | Server | Read / Write | Annotations | Auth |
|---|---|---|---|---|
| `search_evidence` | `portfolio` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Local / stdio |
| `get_case_study` | `portfolio` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Local / stdio |
| `list_skills` | `portfolio` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Local / stdio |
| `search_jobs` | `marketplace` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Bearer + RPM limit |
| `get_job` | `marketplace` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Bearer + RPM limit |
| `get_client_history` | `marketplace` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Bearer + RPM limit |
| `get_connects_balance` | `marketplace` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Bearer + RPM limit |
| `list_messages` | `marketplace` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Bearer + RPM limit |
| `create_proposal_draft` | `marketplace` | Write | `readOnlyHint=False, destructiveHint=False, idempotentHint=True` | Bearer + Idempotency + `dry_run` |
| `submit_proposal` | `marketplace` | Write | `readOnlyHint=False, destructiveHint=True, idempotentHint=True` | Bearer + Idempotency + Human `interrupt()` |
| `send_message` | `marketplace` | Write | `readOnlyHint=False, destructiveHint=True, idempotentHint=True` | Bearer + Idempotency + Human `interrupt()` |
| `get_free_slots` | `workspace` | Read | `readOnlyHint=True, destructiveHint=False, idempotentHint=True` | Local / OAuth |
| `create_interview_hold` | `workspace` | Write | `readOnlyHint=False, destructiveHint=False, idempotentHint=True` | Local / OAuth + Idempotency |
| `create_email_draft` | `workspace` | Write | `readOnlyHint=False, destructiveHint=False, idempotentHint=True` | Local / OAuth |

## 2. Third-Party MCP Servers & Trust Rationale
- **Official Upwork MCP Server (`https://mcp.upwork.com/mcp`)**: Official vendor-hosted Streamable HTTP server with OAuth 2.1; write tools create drafts only and require explicit user confirmation on Upwork.com.
- **GitHub MCP Server (`@modelcontextprotocol/server-github`)**: Read-only scoped repository access used during portfolio ingestion (`rag/ingest/loader.py`) to fetch READMEs and source files without storing raw credentials in agent prompts.
