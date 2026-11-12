# AI Coding Assistant Usage Disclosure (`docs/AI_USAGE.md`)

**Author:** Abdullah Razzaq (`23i-0057`, Section B)

## Tools Used & File Coverage
- **Antigravity AI Coding Assistant (Gemini)**:
  - Used for scaffolding `gigsim/`, `mcp_servers/`, `rag/variants/`, `agent/graphs/`, `apps/api/`, `apps/web/`, `evals/runners/`, and `tests/`.
  - All generated code, schemas, evaluation scripts, and documentation were reviewed, executed, and verified against `pytest`, `tsc && vite build`, and `evals/runners/run_all_evals.py`.

## Specific Errors Caught & Fixed During Development
1. **Python 3.13 Dependency Resolution Issue**: Initial dependency list included `langgraph-supervisor`, which pulled an older `numpy 1.26.4` source tarball requiring a C compiler on Windows Python 3.13. Caught during `pip install`, removed the unused pin, and used `numpy>=2.0.0` binary wheels cleanly.
2. **Claim Verification Edge Case**: Early `verify_claim` logic treated polite closing sentences ("Proposed bid is $450") as unsupported factual claims unless exempted as non-experience framing. Fixed in `rag/verify.py` and verified with `tests/unit/test_rag_and_verify.py`.
3. **Marketplace Port Separation**: Ensured `MarketplacePort` (`agent/marketplace_port.py`) never leaks `hidden_preferences` from `gigsim/store.py` to agents (`get_client_history` strips `hidden_preferences`).
