"""Human-review sampling and evaluation helpers."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Iterable

from src.classification import CATEGORIES, SENTIMENTS
from src.config import ROOT

REVIEW_FIELDS = (
    "feedback_id", "date", "customer_segment", "product_area", "feedback_source",
    "customer_comment", "human_sentiment", "human_category", "reviewer_notes",
)
PREDICTION_FIELDS = (
    "feedback_id", "prediction_status", "sentiment", "primary_category", "theme",
    "potential_root_cause", "priority", "suggested_follow_up", "supporting_evidence", "classification_error",
)


def _representative_sample(rows: list[dict[str, str]], sample_size: int, seed: int) -> list[dict[str, str]]:
    """Select balanced source/segment strata with seeded random selection within each stratum."""
    if sample_size < 1:
        raise ValueError("sample_size must be at least 1.")
    sample_size = min(sample_size, len(rows))
    sources = sorted({row.get("feedback_source", "Unknown") for row in rows})
    rng = random.Random(seed)
    source_quotas = {source: sample_size // len(sources) for source in sources}
    for source in sources[: sample_size % len(sources)]:
        source_quotas[source] += 1

    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    for source_index, source in enumerate(sources):
        quota = source_quotas[source]
        source_rows = [row for row in rows if row.get("feedback_source", "Unknown") == source]
        available_segments = sorted({row.get("customer_segment", "Unknown") for row in source_rows})
        base, remainder = divmod(quota, len(available_segments))
        for segment_index, segment in enumerate(available_segments):
            stratum_quota = base + int((segment_index - source_index) % len(available_segments) < remainder)
            bucket = [row for row in source_rows if row.get("customer_segment", "Unknown") == segment]
            rng.shuffle(bucket)
            for row in bucket[:stratum_quota]:
                selected.append(row)
                selected_ids.add(row["feedback_id"])

    if len(selected) < sample_size:
        remaining = [row for row in rows if row["feedback_id"] not in selected_ids]
        rng.shuffle(remaining)
        selected.extend(remaining[: sample_size - len(selected)])
    return selected


def create_review_sample(source_csv: Path, destination_csv: Path, sample_size: int = 30, seed: int = 42) -> Path:
    """Create a stratified, repeatable worksheet with no model predictions."""
    with source_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("The source CSV contains no feedback rows.")

    previous_rows: dict[str, dict[str, str]] = {}
    if destination_csv.exists():
        with destination_csv.open(newline="", encoding="utf-8") as handle:
            previous_rows = {row["feedback_id"]: row for row in csv.DictReader(handle) if row.get("feedback_id")}

    sample = _representative_sample(rows, sample_size, seed)
    destination_csv.parent.mkdir(parents=True, exist_ok=True)
    with destination_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for row in sample:
            prior = previous_rows.get(row["feedback_id"], {})
            output = {field: row.get(field, "") for field in REVIEW_FIELDS}
            output["human_sentiment"] = prior.get("human_sentiment", "")
            output["human_category"] = prior.get("human_category", "")
            output["reviewer_notes"] = prior.get("reviewer_notes", "")
            writer.writerow(output)
    return destination_csv


def export_predictions(classifications_path: Path, review_path: Path, destination_path: Path) -> Path:
    """Export model predictions separately from the blind human-label worksheet."""
    with review_path.open(newline="", encoding="utf-8") as handle:
        review_ids = {row["feedback_id"] for row in csv.DictReader(handle)}
    records = json.loads(classifications_path.read_text(encoding="utf-8"))
    predictions = {str(row.get("feedback_id", "")): row for row in records if isinstance(row, dict)}
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with destination_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        writer.writeheader()
        for feedback_id in sorted(review_ids):
            row = predictions.get(feedback_id, {})
            status = "failed" if row.get("classification_error") else "classified" if row.get("sentiment") else "pending"
            output = {field: row.get(field, "") for field in PREDICTION_FIELDS}
            output["feedback_id"] = feedback_id
            output["prediction_status"] = status
            writer.writerow(output)
    return destination_path


def classification_metrics(actual: Iterable[str], predicted: Iterable[str], labels: tuple[str, ...]) -> dict[str, object]:
    actual_values = list(actual)
    predicted_values = list(predicted)
    if len(actual_values) != len(predicted_values):
        raise ValueError("Actual and predicted labels must have the same number of rows.")
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("The label set must be non-empty and contain unique values.")

    pairs = [(actual_label, predicted_label) for actual_label, predicted_label in zip(actual_values, predicted_values) if actual_label in labels and predicted_label in labels]
    matrix = {label: {column: 0 for column in labels} for label in labels}
    class_support = {label: 0 for label in labels}
    for actual_label, predicted_label in pairs:
        matrix[actual_label][predicted_label] += 1
        class_support[actual_label] += 1
    accuracy = sum(actual_label == predicted_label for actual_label, predicted_label in pairs) / len(pairs) if pairs else None
    f1_values = []
    for label in labels:
        true_positive = matrix[label][label]
        false_positive = sum(matrix[other][label] for other in labels if other != label)
        false_negative = sum(matrix[label][other] for other in labels if other != label)
        denominator = 2 * true_positive + false_positive + false_negative
        f1_values.append(2 * true_positive / denominator if denominator else 0.0)
    return {
        "n": len(pairs),
        "excluded_rows": len(actual_values) - len(pairs),
        "class_support": class_support,
        "class_coverage": sum(count > 0 for count in class_support.values()),
        "accuracy": accuracy,
        "macro_f1": sum(f1_values) / len(f1_values) if pairs else None,
        "confusion_matrix": matrix,
    }


def evaluate_review_file(review_path: Path, predictions_path: Path, disagreements_path: Path | None = None) -> dict[str, object]:
    """Score only completed human labels and optionally write item-level disagreements."""
    with review_path.open(newline="", encoding="utf-8") as handle:
        review_rows = list(csv.DictReader(handle))
    with predictions_path.open(newline="", encoding="utf-8") as handle:
        predictions = {row["feedback_id"]: row for row in csv.DictReader(handle)}

    sentiment_actual: list[str] = []
    sentiment_predicted: list[str] = []
    category_actual: list[str] = []
    category_predicted: list[str] = []
    disagreements: list[dict[str, str]] = []
    for row in review_rows:
        prediction = predictions.get(row["feedback_id"], {})
        for human_field, prediction_field, labels, actual_list, predicted_list, metric in (
            ("human_sentiment", "sentiment", SENTIMENTS, sentiment_actual, sentiment_predicted, "sentiment"),
            ("human_category", "primary_category", CATEGORIES, category_actual, category_predicted, "category"),
        ):
            actual = row.get(human_field, "").strip()
            predicted = prediction.get(prediction_field, "").strip()
            if not actual:
                continue
            if actual not in labels:
                raise ValueError(f"Invalid {metric} label {actual!r} for {row['feedback_id']}.")
            if predicted not in labels:
                continue
            actual_list.append(actual)
            predicted_list.append(predicted)
            if actual != predicted:
                disagreements.append({
                    "feedback_id": row["feedback_id"],
                    "field": metric,
                    "human_label": actual,
                    "model_label": predicted,
                    "customer_comment": row.get("customer_comment", ""),
                    "supporting_evidence": prediction.get("supporting_evidence", ""),
                    "reviewer_notes": row.get("reviewer_notes", ""),
                })

    sentiment = classification_metrics(sentiment_actual, sentiment_predicted, SENTIMENTS) if sentiment_actual else None
    category = classification_metrics(category_actual, category_predicted, CATEGORIES) if category_actual else None
    reviewed_pairs = (sentiment["n"] if sentiment else 0) + (category["n"] if category else 0)
    if disagreements_path is not None and reviewed_pairs:
        disagreements_path.parent.mkdir(parents=True, exist_ok=True)
        fields = ("feedback_id", "field", "human_label", "model_label", "customer_comment", "supporting_evidence", "reviewer_notes")
        with disagreements_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(disagreements)

    labeled_count = sum(bool(row.get("human_sentiment", "").strip() or row.get("human_category", "").strip()) for row in review_rows)
    if not labeled_count:
        status = "No human labels provided; metrics are withheld."
    elif not reviewed_pairs:
        status = "Human labels exist, but no matching model predictions are available; metrics are withheld."
    else:
        status = f"Scored {sentiment['n'] if sentiment else 0} sentiment and {category['n'] if category else 0} category label pairs."
    return {"status": status, "sentiment": sentiment, "category": category, "disagreements": len(disagreements)}


def ensure_review_file() -> Path:
    source = ROOT / "data" / "synthetic" / "feedback.csv"
    destination = ROOT / "data" / "evaluation" / "human_review_sample.csv"
    return create_review_sample(source, destination, sample_size=30, seed=42)
