# Operations Runbook (`docs/RUNBOOK.md`)

## 1. Live Mode Polling Interval Justification
- `live_poll_interval_minutes: 30` in `agent/config.yaml` (maximum 48 polls/day per saved search).
- **Rationale**: Upwork's official automation guidance prohibits high-frequency polling that resembles scraping. A 30-minute interval stays well under `max_requests_per_minute: 30` while catching new high-fit jobs within a competitive window.

## 2. Degraded Mode & Recovery
- If the Marketplace MCP server becomes unreachable (or is toggled offline in `/runs`), `agent/mcp_client.py` raises `MarketplaceDegradedError`.
- The API surfaces a `Degraded Mode` banner in `/inbox` and queues incoming `analyze_job` requests in `mcp.queued_jobs` rather than dropping them or crashing.
- Once restored, queued jobs are re-processed idempotently via `worker/tasks.py`.

## 3. Crash-and-Resume Durability
- Both `bid_graph` and `conversation_graph` use `AsyncSqliteSaver` (`data/processed/gigbid_checkpoints.db`) / `PostgresSaver` in Docker Compose.
- If the API process is killed while a thread is paused at `human_approval`, restarting the API and calling `POST /api/proposals/{job_id}/approve` resumes the exact `thread_id` with `Command(resume=...)`.
- Every `create_proposal_draft` and `submit_proposal` call passes a deterministic `idempotency_key` (`submit-{job_id}-{user_id}`), guaranteeing Connects are never spent twice.

## 4. Secrets & Environment
- Never commit `.env`. Copy `.env.example` to `.env` and set `APP_SECRET_KEY`, `GROQ_API_KEY` (optional), and `UPWORK_OAUTH_TOKEN` (optional).
