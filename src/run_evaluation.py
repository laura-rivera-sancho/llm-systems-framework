"""Prepare the blinded review worksheet and score only human-completed labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import ROOT
from src.evaluation import create_review_sample, ensure_review_file, evaluate_review_file, export_predictions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=ROOT / "data" / "evaluation" / "human_review_sample.csv")
    parser.add_argument("--predictions", type=Path, default=ROOT / "data" / "evaluation" / "model_predictions.csv")
    parser.add_argument("--disagreements", type=Path, default=ROOT / "data" / "evaluation" / "disagreements.csv")
    parser.add_argument("--refresh-sample", action="store_true", help="Recreate the deterministic sample while preserving any existing human labels.")
    args = parser.parse_args()

    default_review = ROOT / "data" / "evaluation" / "human_review_sample.csv"
    if args.review == default_review:
        review_path = ensure_review_file()
    elif args.refresh_sample or not args.review.exists():
        review_path = create_review_sample(ROOT / "data" / "synthetic" / "feedback.csv", args.review, 30, 42)
    else:
        review_path = args.review
    classifications_path = ROOT / "data" / "processed" / "classifications.json"
    predictions_path = export_predictions(classifications_path, review_path, args.predictions)
    report = evaluate_review_file(review_path, predictions_path, args.disagreements)

    print(report["status"])
    print(f"Blind human worksheet: {review_path}")
    print(f"Separate model predictions: {predictions_path}")
    if report["sentiment"] is not None or report["category"] is not None:
        print(json.dumps({"sentiment": report["sentiment"], "category": report["category"], "disagreements": report["disagreements"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
