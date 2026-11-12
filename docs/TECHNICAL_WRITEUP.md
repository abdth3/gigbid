# Why Better Retrieval Didn't Automatically Win More Freelance Replies (And What Actually Did)

*By Abdullah Razzaq (23i-0057) · Technical Write-up for GigBid (AI-4016)*

When building **GigBid**, a multi-agent LangGraph copilot for freelancers, our initial assumption was straightforward: if we upgrade the retrieval pipeline from naive dense embeddings (`V0`) to hybrid BM25 + dense fusion (`V2`), cross-encoder reranking (`V3`), and outcome-aware ranking (`V4`), client reply rates in our marketplace simulator (`GigSim`) would climb in lockstep with `Recall@5`.

Our controlled experiments across 120 dev jobs (40 per persona across AI/ML Engineering, Full-Stack Web, and Data Analytics) and 50 end-to-end LangGraph runs revealed a much more nuanced story.

## 1. Retrieval Gains Were Real—Especially on Multi-Requirement & Exact-Tool Jobs
Naive dense retrieval (`V0`) struggled whenever a job post named specific libraries like `dbt`, `Qdrant`, or `Playwright`, or when a case study used implied phrasing (e.g., *"distributed async task queues with Redis broker"* instead of literally naming `Celery`). Adding BM25 + Dense Reciprocal Rank Fusion (`V2`) and Cross-Encoder reranking (`V3`) boosted `Recall@5` and `nDCG@10` substantially, while `V4` (outcome-aware ranking) prioritized case studies and past proposals that had previously won or received client replies rather than ignored generic templates.

## 2. The Surprising Finding: Retrieval Alone Doesn't Fix Generic Openings or Unsupported Claims
Even when `V4` retrieved the exact right case study at rank 1, **client reply rates plateaued** whenever the Writer node:
1. Opened with generic filler (*"Dear Sir/Madam, I am passionate..."*), which GigSim's simulated clients penalized immediately.
2. Hallucinated an extra skill or years-of-experience claim alongside the retrieved case study.
3. Exceeded the Nov 2, 2026 platform policy cap of 1,800 characters.

In fact, **Claim Verification (`rag/verify.py`) + Style Memory (`agent/memory/store.py`)** accounted for a larger jump in GigSim reply rate than moving from `V2` to `V3` retrieval alone. Stripping unsupported claims before the Critic saw the draft dropped `unsupported_claims_per_proposal` to `0.00` while keeping proposals tight and credible.

## 3. Multi-Agent Graph vs. Single ReAct Agent
On 50 dev jobs, a single ReAct agent holding all 14 MCP tools was faster and cheaper on simple 1-requirement jobs. However, on multi-requirement jobs, scam posts, and prompt-injection tests, the single ReAct agent frequently skipped compliance checks or forgot to verify claims. Our hand-built LangGraph `StateGraph`—using parallel `Send()` branches for `Job Analyst`, `Risk Assessor`, and `Fit Matcher`, bounded Critic loops (max 2), and `interrupt()` human approval gates—achieved higher bid-or-skip accuracy, zero unsupported claims, and 100% policy enforcement.

## 4. Key Takeaway
In agentic products, **retrieval quality is necessary but not sufficient**. Grounded claim verification, explicit human-edit style memory, and deterministic compliance guardrails are what turn retrieved context into trustworthy, high-converting actions.
