"""Validate complete saved classifications without making Gemini requests."""

from __future__ import annotations

import json
from pathlib import Path

from src.classification import ClassificationError, _validate_result
from src.config import ROOT
from src.run_pipeline import read_feedback


def validate_results(source_path: Path, results_path: Path) -> dict[str, object]:
    source = read_feedback(source_path)
    results = json.loads(results_path.read_text(encoding="utf-8"))
    if not isinstance(results, list):
        raise ValueError("Classification output must be a JSON array.")
    source_by_id = {str(row["feedback_id"]): row for row in source}
    result_ids = [str(row.get("feedback_id", "")) for row in results if isinstance(row, dict)]
    duplicates = sorted({feedback_id for feedback_id in result_ids if result_ids.count(feedback_id) > 1})
    missing = sorted(set(source_by_id) - set(result_ids))
    extra = sorted(set(result_ids) - set(source_by_id))
    errors: list[str] = []
    valid_count = 0
    for row in results:
        feedback_id = str(row.get("feedback_id", "")) if isinstance(row, dict) else "<non-object>"
        if not isinstance(row, dict) or "classification_error" in row:
            errors.append(feedback_id)
            continue
        source_row = source_by_id.get(feedback_id)
        if not source_row:
            continue
        try:
            _validate_result(row, str(source_row.get("customer_comment") or ""))
            valid_count += 1
        except ClassificationError:
            errors.append(feedback_id)
    report = {
        "source_records": len(source),
        "output_rows": len(results),
        "valid_classifications": valid_count,
        "failed_or_invalid": sorted(set(errors)),
        "missing_ids": missing,
        "extra_ids": extra,
        "duplicate_ids": duplicates,
    }
    return report


def main() -> None:
    report = validate_results(ROOT / "data" / "synthetic" / "feedback.csv", ROOT / "data" / "processed" / "classifications.json")
    print(json.dumps(report, indent=2))
    if report["valid_classifications"] != report["source_records"] or any(report[key] for key in ("failed_or_invalid", "missing_ids", "extra_ids", "duplicate_ids")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
