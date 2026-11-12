# Data Card (`docs/DATA_CARD.md`)

## 1. Real vs. Synthetic Data Distinction
- **Market Pricing & Skill Distributions (Real Reference)**: Historical job budget bands, Connects costs, and skill co-occurrence distributions in `data/historical_jobs.json` (1,500 records) are modeled after public Kaggle Upwork job posting datasets (`asaniczka/upwork-job-postings-dataset-2024-50k-records`, `ahmedmyalo/upwork-freelance-jobs-60k`).
- **Synthetic Corpora (Clearly Labelled)**:
  - **Three Freelancer Personas (`data/personas/`)**: `ai_ml_engineer` (Tariq Mahmood), `fullstack_web_dev` (Sana Siddiqui), and `data_analyst` (Bilal Qureshi). Each contains a CV, 16 Markdown case studies (mixing prose, metrics, code blocks, and implied skills), 4 repo READMEs + Python modules, 8 client reviews, and 150 outcome-labelled past proposals (`won`, `replied`, `ignored`).
  - **Dev Evaluation Set (`evals/datasets/dev_jobs.json`)**: 600 synthetic jobs (200 per persona) with gold labels (`gold_decision`, `is_scam`, `is_injection`, `gold_evidence_ids`, `fair_price_min/max`). Includes 60 scam posts and 45 planted prompt-injection posts.
  - **Simulated Clients (`data/gigsim_clients.json`)**: 120 synthetic clients with hidden preferences (`must_have_skills`, `budget_ceiling`, `dislike_generic_openings`).

## 2. Preprocessing, Attribution & Licensing
- All synthetic records are generated reproducibly with `random.Random(42)` via `scripts/generate_data.py`.
- No real client PII, private Upwork data, or hidden test set items are stored in the repository.
- Kaggle reference datasets are used strictly for aggregate statistical calibration under their respective CC0 / public dataset terms.

## 3. Limitations
- Synthetic client reply simulation (`gigsim/store.py`) evaluates evidence citations, generic opening avoidance, and budget alignment deterministically; real-world Upwork clients exhibit higher variance in response latency and subjective tone preferences.
