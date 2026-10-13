"""Create the deterministic, fictional customer feedback sample."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from src.config import ROOT

SCENARIOS = [
    ("Usability", "Navigation and discoverability", "I had to click through three menus to find the usage report; the layout is confusing."),
    ("Reliability", "Intermittent session failure", "The workspace logged me out twice during a customer call, so I had to restart."),
    ("Performance", "Slow dashboard loading", "The dashboard takes about 20 seconds to load each morning, which slows our review."),
    ("Billing", "Unexpected seat charge", "We were charged for two extra seats after removing those users from the workspace."),
    ("Integrations", "CRM sync delay", "The Salesforce sync is several hours behind, and our team is working from stale account data."),
    ("Onboarding", "Setup guidance gap", "We are still unsure how to map our fields after onboarding; the setup guide skips that step."),
    ("Support", "Delayed support response", "I opened a ticket on Monday and still have no response about the export failure."),
    ("Feature Request", "Custom reporting request", "It would help if we could schedule a report and send it to regional leads every week."),
    ("Documentation", "Missing API examples", "The API page does not show a working pagination example, so we had to guess the parameters."),
    ("Security & Access", "Role permission confusion", "A read-only analyst can edit a saved view; we need clearer role permissions."),
]
SOURCES = ("Support ticket", "NPS survey", "CSAT survey", "Product request", "Onboarding", "Customer success")
SEGMENTS = ("SMB", "Mid-market", "Enterprise")
PRODUCT_AREAS = ("Analytics", "Integrations", "Administration", "Reporting", "Core platform")
TONE = (
    "This has been frustrating. ", "Overall, this is manageable. ", "We like the product, but ",
    "Thanks for the recent improvements. ", "This is blocking part of our workflow. ",
    "I am not sure whether this is expected. ", "The team has found a workaround, although ",
    "We are happy with the product overall. ", "Please help us understand why ",
    "This is a small suggestion: ", "We rely on this every day, and ", "So far, the experience is good; ",
)

CSAT_SCORE_PROFILE = (1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5)
NPS_SCORE_PROFILE = (0, 2, 4, 5, 6, 6, 7, 7, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10)


def _shuffled_profile(profile: tuple[int, ...], seed: int) -> list[int]:
    """Return a reproducible score roster independent of feedback wording."""
    scores = list(profile)
    random.Random(seed).shuffle(scores)
    return scores


def build_records(count: int = 120) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    start = date(2025, 1, 3)
    survey_profiles = {
        "CSAT survey": _shuffled_profile(CSAT_SCORE_PROFILE, seed=2401),
        "NPS survey": _shuffled_profile(NPS_SCORE_PROFILE, seed=2402),
    }
    survey_counts = {source: 0 for source in survey_profiles}
    for index in range(count):
        category, theme, base_comment = SCENARIOS[index % len(SCENARIOS)]
        tone = TONE[(index // len(SCENARIOS)) % len(TONE)]
        source = SOURCES[index % len(SOURCES)]
        comment = tone + base_comment
        score = None
        if source in survey_profiles:
            roster = survey_profiles[source]
            score = roster[survey_counts[source] % len(roster)]
            survey_counts[source] += 1
        records.append({
            "feedback_id": f"VOC-{index + 1:04d}",
            "date": (start + timedelta(days=(index * 3) % 540)).isoformat(),
            "customer_segment": SEGMENTS[(index // 2) % len(SEGMENTS)],
            "product_area": PRODUCT_AREAS[index % len(PRODUCT_AREAS)],
            "feedback_source": source,
            "survey_score": score,
            "customer_comment": comment,
            "synthetic": True,
        })
    return records


def write_dataset(path: Path | None = None, count: int = 120) -> Path:
    destination = path or ROOT / "data" / "synthetic" / "feedback.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    records = build_records(count)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return destination


if __name__ == "__main__":
    print(write_dataset())
