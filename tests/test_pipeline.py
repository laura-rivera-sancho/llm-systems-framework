import csv
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from src.classification import ClassificationError, _parse_response, _record_usage, classify_records
from src.evaluation import classification_metrics, create_review_sample, evaluate_review_file, export_predictions
from src.generate_synthetic import build_records


class PipelineTests(unittest.TestCase):
    def test_synthetic_dataset_is_deterministic_and_complete(self):
        first = build_records()
        self.assertEqual(first, build_records())
        self.assertEqual(len(first), 120)
        self.assertEqual(len({row["feedback_id"] for row in first}), 120)
        self.assertEqual({row["feedback_source"] for row in first}, {"Support ticket", "NPS survey", "CSAT survey", "Product request", "Onboarding", "Customer success"})

    def test_synthetic_survey_scores_are_reproducible_and_use_full_scales(self):
        records = build_records()
        csat_scores = [row["survey_score"] for row in records if row["feedback_source"] == "CSAT survey"]
        nps_scores = [row["survey_score"] for row in records if row["feedback_source"] == "NPS survey"]
        self.assertEqual(len(csat_scores), 20)
        self.assertEqual(len(nps_scores), 20)
        self.assertEqual(csat_scores, [row["survey_score"] for row in build_records() if row["feedback_source"] == "CSAT survey"])
        self.assertEqual(nps_scores, [row["survey_score"] for row in build_records() if row["feedback_source"] == "NPS survey"])
        self.assertEqual({score: csat_scores.count(score) for score in range(1, 6)}, {1: 1, 2: 2, 3: 4, 4: 7, 5: 6})
        self.assertTrue(all(1 <= score <= 5 for score in csat_scores))
        self.assertTrue(all(0 <= score <= 10 for score in nps_scores))
        promoters = sum(score >= 9 for score in nps_scores)
        detractors = sum(score <= 6 for score in nps_scores)
        self.assertEqual(100 * (promoters - detractors) / len(nps_scores), 20)

    def test_response_requires_verbatim_evidence(self):
        payload = {"sentiment": "Negative", "primary_category": "Performance", "theme": "Slow loading", "potential_root_cause": "Not stated", "priority": "Medium", "suggested_follow_up": "Ask when this occurs", "supporting_evidence": "20 seconds to load"}
        self.assertEqual(_parse_response(json.dumps(payload), "The dashboard takes 20 seconds to load.")["priority"], "Medium")
        payload["supporting_evidence"] = "The database is overloaded"
        with self.assertRaises(ClassificationError):
            _parse_response(json.dumps(payload), "The dashboard takes 20 seconds to load.")

    def test_review_sample_is_reproducibly_balanced_and_blind(self):
        with TemporaryDirectory(dir=Path.cwd()) as tmp:
            root = Path(tmp)
            records = build_records()
            source = root / "input.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(records[0]))
                writer.writeheader()
                writer.writerows(records)
            destination = root / "review.csv"
            create_review_sample(source, destination, sample_size=30, seed=42)
            first = list(csv.DictReader(destination.open(newline="", encoding="utf-8")))
            first_ids = [row["feedback_id"] for row in first]
            create_review_sample(source, destination, sample_size=30, seed=42)
            second = list(csv.DictReader(destination.open(newline="", encoding="utf-8")))
            self.assertEqual(first_ids, [row["feedback_id"] for row in second])
            second[0]["human_sentiment"] = "Negative"
            second[0]["human_category"] = "Performance"
            with destination.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(second[0]))
                writer.writeheader()
                writer.writerows(second)
            create_review_sample(source, destination, sample_size=30, seed=42)
            refreshed = list(csv.DictReader(destination.open(newline="", encoding="utf-8")))
            self.assertEqual(refreshed[0]["human_sentiment"], "Negative")
            self.assertEqual(refreshed[0]["human_category"], "Performance")
            self.assertEqual(len(first), 30)
            self.assertEqual(set(first[0]), {"feedback_id", "date", "customer_segment", "product_area", "feedback_source", "customer_comment", "human_sentiment", "human_category", "reviewer_notes"})
            self.assertTrue(all("survey_score" not in row and "csat_context_proxy" not in row for row in first))
            self.assertTrue(all(not row["human_sentiment"] and not row["human_category"] for row in first))
            source_counts = {}
            segment_counts = {}
            for row in first:
                source_counts[row["feedback_source"]] = source_counts.get(row["feedback_source"], 0) + 1
                segment_counts[row["customer_segment"]] = segment_counts.get(row["customer_segment"], 0) + 1
            self.assertEqual(set(source_counts.values()), {5})
            self.assertEqual(set(segment_counts.values()), {10})

    def test_checkpoint_reuses_existing_valid_output_without_calling_api(self):
        with TemporaryDirectory(dir=Path.cwd()) as tmp:
            root = Path(tmp)
            row = build_records(1)[0]
            prediction = {"sentiment": "Negative", "primary_category": "Usability", "theme": "Navigation", "potential_root_cause": "Not stated", "priority": "Low", "suggested_follow_up": "Ask the customer to describe the path", "supporting_evidence": "the layout is confusing"}
            checkpoint = root / "classifications.json"
            checkpoint.write_text(json.dumps([{**row, **prediction}]), encoding="utf-8")
            with patch("src.classification.classify_feedback", side_effect=AssertionError("API should not be called")):
                results = classify_records([row], checkpoint)
            self.assertEqual(results[0]["sentiment"], "Negative")

    def test_metrics_and_confusion_matrix(self):
        result = classification_metrics(["Positive", "Negative", "Negative"], ["Positive", "Positive", "Negative"], ("Positive", "Negative"))
        self.assertEqual(result["n"], 3)
        self.assertEqual(result["accuracy"], 2 / 3)
        self.assertEqual(result["confusion_matrix"]["Negative"]["Positive"], 1)

    def test_evaluation_withholds_metrics_then_reports_disagreements(self):
        with TemporaryDirectory(dir=Path.cwd()) as tmp:
            root = Path(tmp)
            review = root / "review.csv"
            predictions = root / "predictions.csv"
            disagreements = root / "disagreements.csv"
            fields = ["feedback_id", "date", "customer_segment", "product_area", "feedback_source", "customer_comment", "human_sentiment", "human_category", "reviewer_notes"]
            row = dict.fromkeys(fields, "")
            row.update({"feedback_id": "A", "customer_comment": "The dashboard is slow.", "human_sentiment": "", "human_category": ""})
            with review.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(row)
            classifications = root / "classifications.json"
            classifications.write_text(json.dumps([{"feedback_id": "A", "sentiment": "Positive", "primary_category": "Performance", "theme": "Slow dashboard", "potential_root_cause": "Not stated", "priority": "Medium", "suggested_follow_up": "Investigate load time", "supporting_evidence": "dashboard is slow"}]), encoding="utf-8")
            export_predictions(classifications, review, predictions)
            blank_report = evaluate_review_file(review, predictions, disagreements)
            self.assertIsNone(blank_report["sentiment"])
            self.assertIn("withheld", blank_report["status"])
            with review.open("r", newline="", encoding="utf-8") as handle:
                review_row = next(csv.DictReader(handle))
            review_row["human_sentiment"] = "Negative"
            review_row["human_category"] = "Performance"
            review_row["reviewer_notes"] = "Explicitly says slow"
            with review.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(review_row)
            report = evaluate_review_file(review, predictions, disagreements)
            self.assertEqual(report["sentiment"]["n"], 1)
            self.assertEqual(report["sentiment"]["accuracy"], 0.0)
            self.assertEqual(report["category"]["accuracy"], 1.0)
            with disagreements.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["field"], "sentiment")

    def test_usage_ledger_estimates_cost_only_with_configured_rates(self):
        with TemporaryDirectory(dir=Path.cwd()) as tmp:
            test_settings = SimpleNamespace(data_dir=Path(tmp), model="test-model", input_usd_per_million_tokens=1.0, output_usd_per_million_tokens=2.0)
            usage = SimpleNamespace(prompt_token_count=500, candidates_token_count=100, total_token_count=600)
            with patch("src.classification.settings", test_settings):
                _record_usage("VOC-TEST", 1.25, "response_received", usage)
            ledger = Path(tmp) / "processed" / "api_usage.jsonl"
            event = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual(event["total_tokens"], 600)
            self.assertEqual(event["estimated_cost_usd"], 0.0007)


if __name__ == "__main__":
    unittest.main()
