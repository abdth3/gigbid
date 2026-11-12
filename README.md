# GigBid — Multi-Agent Freelancer Copilot

> **AI-4016 Agentic AI Assignment 2** · **Author:** Abdullah Razzaq (`23i-0057`, Section B)  
> **Repository:** `https://github.com/abdth3/gigbid`

GigBid is a full-stack, human-in-the-loop multi-agent copilot that discovers freelance jobs, assesses client risk and prompt-injection threats, retrieves verified portfolio evidence via Advanced RAG + MCP, drafts claim-verified proposals, and pauses at durable LangGraph `interrupt()` gates before any proposal, message, or Connects spend leaves the system.

## Architecture

- **MCP Tool Layer (`mcp_servers/`)**: Read-only `portfolio` server (`search_evidence`, `get_case_study`, `list_skills`, `portfolio://case/{id}`), `marketplace` server (wrapping `GigSim` or official `Upwork MCP` over Streamable HTTP via a single `MarketplacePort`, with Pydantic schemas, `idempotency_key`, `dry_run`, bearer auth, rate limiter, and append-only audit log), and `workspace` server (calendar slots, interview holds, email drafts).
- **Advanced RAG (`rag/`)**: 8 configurable retrieval variants (`V0`–`V9`) + deterministic sentence-level Claim Verifier (`rag/verify.py`) that strips unsupported claims before Critique.
- **LangGraph Orchestration (`agent/graphs/`)**:
  - **Bid Graph**: `Scout` → Parallel `Send()` (`Job Analyst`, `Risk Assessor`, `Fit Matcher`) → `Decision` → `Pricing Strategist` → `Proposal Writer` → `Claim Verifier` → `Critic` (max 2 loops) → `Compliance Guard` → `interrupt()` Human Approval → Idempotent Submission.
  - **Conversation Graph**: `Client Liaison` → `interrupt()` Human Approval → Interview Hold & Reply.
- **Full-Stack Web UI (`apps/web/` + `apps/api/`)**: React + TypeScript + FastAPI with SSE live run streaming, hoverable `[evidence_id]` citations, Kanban pipeline, Memory Viewer, and Degraded Mode banner.

## Key Evaluation Results (from `evals/results/`)

### RAG Retrieval & Claim Verification (`evals/results/rag_eval.json`, 120 dev jobs)
| Variant | Recall@5 | MRR | nDCG@10 | Unsupported (Before → After) | GigSim Reply Rate | p95 Latency (s) | Cost/Proposal |
|---|---:|---:|---:|---:|---:|---:|---:|
| `v0_naive` (Baseline) | 0.000 | 0.058 | 0.166 | 1.000 → 0.000 | 0.000 | 0.0197 | \$0.00 |
| `v1_decomp` | 0.000 | 0.059 | 0.169 | 1.000 → 0.000 | 0.000 | 0.0797 | \$0.00 |
| `v2_hybrid` (BM25 + Dense RRF) | 0.008 | 0.114 | 0.283 | 1.000 → 0.000 | 0.005 | 0.0391 | \$0.00 |
| **`v3_rerank` (Shipped)** | **1.000** | **1.000** | **1.000** | **1.000 → 0.000** | **0.650** | **0.0258** | **\$0.00** |
| `v4_outcome` | 0.767 | 0.558 | 0.661 | 1.000 → 0.000 | 0.498 | 0.0274 | \$0.00 |
| `v5_multivector` | 0.708 | 0.327 | 0.486 | 1.000 → 0.000 | 0.460 | 0.0252 | \$0.00 |
| `v8_corrective` | 1.000 | 1.000 | 1.000 | 1.000 → 0.000 | 0.650 | 0.0257 | \$0.00 |
| `v9_skill_graph` | 0.008 | 0.114 | 0.283 | 1.000 → 0.000 | 0.005 | 0.0257 | \$0.00 |

*Judge Calibration (`n=30`): Cohen's $\kappa = 0.841$, agreement = 93.3%.*

### Multi-Agent Comparison (`evals/results/multi_agent_eval.json`, 50 dev jobs)
| Architecture | Bid/Skip Acc | Unsupported Claims | GigSim Reply Rate | Avg Tokens/Job | p95 Latency (s) |
|---|---:|---:|---:|---:|---:|
| Single ReAct Agent | 0.780 | 0.680 | 0.420 | 3,850.0 | 0.850 |
| Prebuilt Supervisor | 0.840 | 0.310 | 0.560 | 5,420.0 | 1.350 |
| **Hand-Built LangGraph (Ours)** | **0.900** | **0.000** | **0.467** | **894.5** | **0.141** |

### Signature Extension X2: Proposal A/B Experiment (`evals/results/x2_ab_results.json`, n=60)
- `evidence_first` (Arm A): **16/30 (53.3%)** reply rate
- `outcome_led` (Arm B): **20/30 (66.7%)** reply rate ($z = 1.054, p = 0.2918$, not significant at $\alpha = 0.05$)

## Quick Start
```bash
# 1. Install dependencies
make install

# 2. Run all unit, contract & integration tests
make test

# 3. Run all evaluations & regenerate evals/results/
make eval

# 4. Launch full-stack app (FastAPI + built React UI on http://127.0.0.1:8000)
make demo
```
Reviewer credentials (preloaded with AI/ML Engineer persona): `reviewer` / `gigbid-reviewer-2026`.
