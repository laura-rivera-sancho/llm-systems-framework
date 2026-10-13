# Roadmap

This roadmap distinguishes implemented workflow components from evidence needed for stronger portfolio claims. The data is synthetic, so completion does not imply production readiness.

| Milestone | Status | Completion evidence / next action |
|---|---|---|
| Deterministic synthetic dataset and dashboard | Complete | 120 fictional records; dashboard runs without Gemini |
| Gemini classification pipeline | Complete | 120/120 outputs validate; 120/120 evidence excerpts match source comments |
| Blind evaluation workflow | Implemented; pilot only | Five human-labeled rows. Label a broader, varied sample and review disagreement cases before reporting quality estimates |
| Full case study and stakeholder readout | Draft; validation pending | `docs/stakeholder_readout.md` summarizes the prototype and explicit limits. Representative human evaluation and a real-process baseline are still needed before quality or value claims |
| Public-repository packaging | Published; CI passed | Initial commit `a988fd4` is on `main`, followed by documentation updates; all three Python CI jobs passed, the final credential-pattern scan found no hits, and `.env`, per-record caches, and the local API-usage ledger were excluded |
| Push project files | Complete | Published to `https://github.com/laura-rivera-sancho/llm-systems-framework` after explicit approval; hosted tests passed on Python 3.11, 3.12, and 3.13 |

## Before making quality claims

- Increase the human-reviewed sample and ensure adequate representation of the declared sentiment and category labels.
- Keep the reviewer blind to model predictions; record the review protocol and any adjudication.
- Report sample size, per-class support/coverage, and disagreement analysis alongside metrics.
- Interpret the separately generated CSAT (1–5) and NPS (0–10) fields as synthetic survey responses, not scores inferred from comment context or observed customer outcomes. Keep their provenance visible in documentation and report sample size and distributions with any dashboard summary.

## Publication packaging

The local repository is on `main` and tracks `origin/main`. The initial public commit is `a988fd4`, followed by documentation updates. The initial 36-file publication allowlist excluded `.env`, `.venv`, per-record caches, Python caches, and `data/processed/api_usage.jsonl`; `.env.example` is the shareable template. A final credential-pattern scan reported no hits. Keep future commits limited to reviewed files and rerun this scan before publication.
