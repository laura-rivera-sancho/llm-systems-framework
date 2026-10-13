# Roadmap

This roadmap distinguishes implemented workflow components from evidence needed for stronger portfolio claims. The data is synthetic, so completion does not imply production readiness.

| Milestone | Status | Completion evidence / next action |
|---|---|---|
| Deterministic synthetic dataset and dashboard | Complete | 120 fictional records; dashboard runs without Gemini |
| Gemini classification pipeline | Complete | 120/120 outputs validate; 120/120 evidence excerpts match source comments |
| Blind evaluation workflow | Implemented; pilot only | Five human-labeled rows. Label a broader, varied sample and review disagreement cases before reporting quality estimates |
| Full case study and stakeholder readout | Not started | A business-case/value-hypothesis draft exists; complete a decision narrative grounded in reviewable evaluation evidence and explicit limitations, without portraying synthetic data as business outcomes |
| Public-repository packaging | Prepared locally; publication pending | README banner and portfolio review path, citation metadata, and community guidance are present. Still requires Git setup, an explicit file allowlist, final secret scan, and approval before the first push |
| Push project files | Waiting for explicit user approval | Push only after the user reviews the final evaluation, case-study framing, and proposed commit contents |

## Before making quality claims

- Increase the human-reviewed sample and ensure adequate representation of the declared sentiment and category labels.
- Keep the reviewer blind to model predictions; record the review protocol and any adjudication.
- Report sample size, per-class support/coverage, and disagreement analysis alongside metrics.
- Interpret the separately generated CSAT (1–5) and NPS (0–10) fields as synthetic survey responses, not scores inferred from comment context or observed customer outcomes. Keep their provenance visible in documentation and report sample size and distributions with any dashboard summary.

## Publication packaging

The project folder currently has no `.git` directory, so there is no branch, commit history, configured remote, or tracked-file view to audit. The confirmed destination is `https://github.com/laura-rivera-sancho/llm-systems-framework`; its default branch `main` is currently empty. Do not initialize or push until the final file allowlist and first publication are approved. The local `.env` must remain excluded; the provided `.env.example` is the shareable template.
