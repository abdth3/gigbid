# Signature Extension X2: Proposal Experiments (`docs/EXTENSION.md`)

## What Was Built
We implemented **X2: Proposal Experiments** — an end-to-end A/B testing harness inside `agent/nodes/writer.py` and `evals/runners/x2_ab_experiment.py` that evaluates two distinct proposal framing strategies on GigSim's hidden-preference client simulator:
- **Arm A (`evidence_first`)**: Opens with job title alignment followed by the primary verified case study and `[evidence_id]` citation.
- **Arm B (`outcome_led`)**: Opens immediately with the quantified metric/outcome achieved in the most similar past project before introducing the stack.

## Measurement & Statistical Significance
Executed via `python -m evals.runners.x2_ab_experiment` across 60 `bid` jobs (30 per arm) using a two-proportion z-test (`evals/results/x2_ab_results.json`). Results are surfaced in the `/analytics` UI screen and cited in Section 7 of the R&D Report.
