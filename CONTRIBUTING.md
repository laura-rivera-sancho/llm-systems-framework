# Contributing

Contributions should improve analytical correctness, reproducibility, responsible operation, or reviewer clarity.

## Case-study standard

Changes should preserve the project's boundaries and make evidence inspectable:

1. Keep synthetic inputs deterministic and clearly identified.
2. Keep model predictions separate from initial human labels.
3. Validate schemas and source-grounded evidence; do not infer unsupported causes.
4. Report evaluation sample size, class coverage, and limitations with every metric.
5. Add or update offline tests for changes, and do not require API access in automated tests.
6. Document operational risks, privacy boundaries, and manual fallback behavior.

Do not add challenge notebooks unless the owner explicitly requests them. Use synthetic data only; never commit credentials, personal data, or confidential records.

## Local checks

```powershell
python -m pytest
python -m src.validate_results
python -m src.qualitative_review
```
