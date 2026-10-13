# Human evaluation protocol

## Blind review workflow

`human_review_sample.csv` is generated as 30 records sampled with seed `42`, stratified across feedback source and customer segment. With this dataset, the sample has five records per source and ten per segment. The record IDs are stable when the source dataset and sampling code remain unchanged. Survey ratings are omitted so they cannot bias sentiment or category judgments. Reviewers should label from the customer comment and taxonomy. Model predictions remain in their separate file.

Label `human_sentiment` and `human_category` in the worksheet without opening `model_predictions.csv`. The prediction export is intentionally stored separately under `data/evaluation/`. Once the human labels are complete and reviewed, run `python -m src.run_evaluation` to compare them with the model outputs and produce item-level disagreements. The script preserves existing labels when it refreshes the deterministic sample.

`codex_ai_category_review.csv` is an independent AI-generated category annotation of the same sample, created only as a secondary review aid. It is not human ground truth and must not be used to claim human evaluation metrics. The original human worksheet and Gemini predictions remain separate.

Do not fill labels from generator scenarios, model predictions, or assumptions about the intended category. Leave a label blank if the comment does not provide enough evidence; explain ambiguity in `reviewer_notes`. For a production study, use two independent reviewers and resolve disagreements before treating a label as ground truth.

## Sentiment taxonomy

- `Positive`: the comment is predominantly favorable.
- `Neutral`: the comment is mainly factual or has no clear positive or negative evaluation.
- `Negative`: the comment is predominantly unfavorable or describes a problem without meaningful favorable counter-signal.
- `Mixed`: the comment contains meaningful positive and negative signals.

## Primary category taxonomy

Choose the single category that best describes the main issue or request.

- `Usability`: interface, workflow, navigation, or discoverability difficulty.
- `Reliability`: failures, errors, outages, lost work, or inconsistent behavior.
- `Performance`: slowness, latency, or resource responsiveness.
- `Billing`: invoices, charges, seats, plans, or payment concerns.
- `Integrations`: third-party connection, synchronization, or data exchange.
- `Onboarding`: initial setup, implementation, or early product guidance.
- `Support`: service quality, responsiveness, or case handling.
- `Feature Request`: a requested product capability that is not primarily a defect in an existing feature.
- `Documentation`: help content, API references, examples, or instructions.
- `Security & Access`: authentication, permissions, roles, or data protection.

## Scoring and interpretation

`src/run_evaluation.py` scores only nonblank, valid human labels that have matching model predictions. It calculates accuracy, macro-F1, class support/coverage, and confusion matrices separately for sentiment and category. It writes disagreement rows with the original comment, model evidence excerpt, and reviewer notes for qualitative analysis. If there are no reviewed pairs, it reports that metrics are withheld and does not create a disagreement file.

Report the number of reviewed pairs and class coverage with every metric. This 30-record synthetic sample is for workflow demonstration, not a statistically representative estimate of production model quality.
