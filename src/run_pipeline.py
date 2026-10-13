"""Command-line entry point for low-volume, cache-aware Gemini classification."""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path

from src.classification import classify_records
from src.config import ROOT, settings
from src.evaluation import create_review_sample


def read_feedback(path: Path) -> list[dict[str, str | None]]:
    with path.open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    required = {"feedback_id", "customer_comment"}
    if not records or not required.issubset(records[0]):
        raise ValueError("Input CSV must contain feedback_id and customer_comment columns.")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "synthetic" / "feedback.csv")
    parser.add_argument("--limit", type=int, default=None, help="Maximum records to process; use a small value for a quota-conscious first run.")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "processed" / "classifications.json")
    parser.add_argument("--make-review-sample", action="store_true", help="Create the blank human-review sample CSV.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    records = read_feedback(args.input)
    if args.make_review_sample:
        path = create_review_sample(args.input, ROOT / "data" / "evaluation" / "human_review_sample.csv")
        print(f"Refreshed human-review sample while preserving existing labels: {path}")
    if args.limit == 0:
        print(f"Loaded {len(records)} feedback records; no model calls requested.")
        return
    if settings.model != "gemini-3.1-flash-lite":
        raise SystemExit("This run is pinned to gemini-3.1-flash-lite. Update GEMINI_MODEL only if the user explicitly authorizes a model change.")
    results = classify_records(records, args.output, limit=args.limit)
    processed_ids = {str(record.get("feedback_id")) for record in results}
    successful_ids = {str(record.get("feedback_id")) for record in results if "classification_error" not in record}
    failed = [record for record in results if "classification_error" in record]
    expected = records[:args.limit] if args.limit is not None else records
    unprocessed = [str(record["feedback_id"]) for record in expected if str(record["feedback_id"]) not in processed_ids]
    print(f"Saved {len(successful_ids)}/{len(expected)} classifications. Model: {settings.model}. Output: {args.output}")
    if failed:
        print("Failed records: " + ", ".join(str(record["feedback_id"]) for record in failed))
        for record in failed:
            print(f"  {record['feedback_id']}: {record['classification_error']}")
    if unprocessed:
        print(f"Unprocessed records: {len(unprocessed)} (" + ", ".join(unprocessed) + ")")
    if len(successful_ids) != len(expected):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
