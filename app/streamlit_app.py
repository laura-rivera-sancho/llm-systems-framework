"""Offline-first Streamlit dashboard for synthetic VoC feedback."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

st.set_page_config(page_title="Voice of Customer | SaaS Analytics", page_icon="🗣️", layout="wide")
st.title("Voice of Customer Analytics")
st.caption("Demo data · B2B SaaS customer feedback")

source = DATA / "synthetic" / "feedback.csv"
classified = DATA / "processed" / "classifications.json"
if not source.exists():
    st.error("Synthetic dataset is missing. Run `python -m src.generate_synthetic` from the project root.")
    st.stop()

feedback = pd.read_csv(source, parse_dates=["date"])
if classified.exists():
    records = json.loads(classified.read_text(encoding="utf-8"))
    predictions = pd.DataFrame(records)
    if "classification_error" in predictions.columns:
        predictions = predictions[predictions["classification_error"].isna()]
    join_columns = ["feedback_id", "sentiment", "primary_category", "theme", "potential_root_cause", "priority", "suggested_follow_up", "supporting_evidence"]
    feedback = feedback.merge(predictions[[column for column in join_columns if column in predictions.columns]], on="feedback_id", how="left")

feedback["sentiment"] = feedback.get("sentiment", pd.Series("Unclassified", index=feedback.index)).fillna("Unclassified")
feedback["primary_category"] = feedback.get("primary_category", pd.Series("Unclassified", index=feedback.index)).fillna("Unclassified")
feedback["theme"] = feedback.get("theme", pd.Series("Pending classification", index=feedback.index)).fillna("Pending classification")
feedback["priority"] = feedback.get("priority", pd.Series("Unclassified", index=feedback.index)).fillna("Unclassified")

segment_options = ["All segments", *sorted(feedback["customer_segment"].dropna().unique())]
selected_segment = st.sidebar.selectbox("Customer segment", segment_options)
if selected_segment != "All segments":
    feedback = feedback[feedback["customer_segment"] == selected_segment]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Feedback records", f"{len(feedback):,}")
c2.metric("Classified", f"{(feedback['sentiment'] != 'Unclassified').sum():,}")
c3.metric("Negative / mixed", f"{feedback['sentiment'].isin(['Negative', 'Mixed']).sum():,}")
c4.metric("High / urgent", f"{feedback['priority'].isin(['High', 'Urgent']).sum():,}")

st.subheader("Survey results")
csat = feedback.loc[feedback["feedback_source"].eq("CSAT survey")].copy()
csat["survey_score"] = pd.to_numeric(csat["survey_score"], errors="coerce")
csat = csat[csat["survey_score"].between(1, 5)]
nps = feedback.loc[feedback["feedback_source"].eq("NPS survey")].copy()
nps["survey_score"] = pd.to_numeric(nps["survey_score"], errors="coerce")
nps = nps[nps["survey_score"].between(0, 10)]

csat_col, nps_col = st.columns(2)
with csat_col:
    st.markdown("**CSAT (1–5)**")
    if csat.empty:
        st.info("No valid CSAT survey responses for this segment.")
    else:
        csat_mean = csat["survey_score"].mean()
        csat_satisfied = csat["survey_score"].ge(4).mean() * 100
        score_col, satisfied_col, responses_col = st.columns(3)
        score_col.metric("Average rating", f"{csat_mean:.1f} / 5")
        satisfied_col.metric("Top-two box (4–5)", f"{csat_satisfied:.0f}%")
        responses_col.metric("Responses", f"{len(csat):,}")
        score_counts = csat["survey_score"].value_counts().sort_index().rename_axis("Rating").reset_index(name="Responses")
        st.plotly_chart(px.bar(score_counts, x="Rating", y="Responses", title="CSAT rating distribution"), width="stretch")

with nps_col:
    st.markdown("**NPS (0–10)**")
    if nps.empty:
        st.info("No valid NPS survey responses for this segment.")
    else:
        nps["respondent_type"] = pd.cut(
            nps["survey_score"], bins=[-1, 6, 8, 10], labels=["Detractor", "Passive", "Promoter"]
        )
        shares = nps["respondent_type"].value_counts(normalize=True)
        nps_value = (shares.get("Promoter", 0) - shares.get("Detractor", 0)) * 100
        nps_metric, promoter_col, passive_col, detractor_col = st.columns(4)
        nps_metric.metric("Net Promoter Score", f"{nps_value:.0f}", help="% Promoters (9–10) minus % Detractors (0–6). Passives score 7–8.")
        promoter_col.metric("Promoters", f"{shares.get('Promoter', 0) * 100:.0f}%")
        passive_col.metric("Passives", f"{shares.get('Passive', 0) * 100:.0f}%")
        detractor_col.metric("Detractors", f"{shares.get('Detractor', 0) * 100:.0f}%")
        st.caption(f"{len(nps):,} valid NPS responses · Promoters 9–10 · Passives 7–8 · Detractors 0–6")
        nps_score_counts = nps["survey_score"].value_counts().sort_index().rename_axis("Score").reset_index(name="Responses")
        st.plotly_chart(px.bar(nps_score_counts, x="Score", y="Responses", title="NPS response distribution"), width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Sentiment distribution")
    sentiment_counts = feedback["sentiment"].value_counts().rename_axis("Sentiment").reset_index(name="Feedback")
    st.plotly_chart(px.bar(sentiment_counts, x="Sentiment", y="Feedback", color="Sentiment", title="Feedback by sentiment"), width="stretch")
with right:
    st.subheader("Most common themes")
    theme_counts = feedback[feedback["theme"] != "Pending classification"]["theme"].value_counts().head(10).rename_axis("Theme").reset_index(name="Feedback")
    if theme_counts.empty:
        st.info("Run classification to populate model-derived themes. The dashboard is usable now with the saved synthetic dataset.")
    else:
        st.plotly_chart(px.bar(theme_counts.sort_values("Feedback"), x="Feedback", y="Theme", orientation="h", title="Top classified themes"), width="stretch")

st.subheader("Feedback volume over time")
monthly = feedback.set_index("date").resample("MS").size().rename("Feedback").reset_index()
st.plotly_chart(px.line(monthly, x="date", y="Feedback", markers=True), width="stretch")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Segment comparison")
    by_segment = feedback.groupby(["customer_segment", "sentiment"], as_index=False).size().rename(columns={"size": "Feedback"})
    st.plotly_chart(px.bar(by_segment, x="customer_segment", y="Feedback", color="sentiment", barmode="group"), width="stretch")
with col2:
    st.subheader("Product and journey pain points")
    by_area = feedback.groupby(["product_area", "primary_category"], as_index=False).size().rename(columns={"size": "Feedback"})
    st.plotly_chart(px.bar(by_area, x="product_area", y="Feedback", color="primary_category", barmode="stack"), width="stretch")

st.subheader("Priority issues and recommended follow-ups")
if "suggested_follow_up" in feedback.columns:
    priorities = feedback[feedback["priority"].isin(["High", "Urgent"])].copy()
    columns = [col for col in ["feedback_id", "customer_segment", "product_area", "priority", "theme", "supporting_evidence", "suggested_follow_up"] if col in priorities]
    if priorities.empty:
        st.caption("No high-priority classified feedback is available yet.")
    else:
        st.dataframe(priorities[columns].sort_values("priority", ascending=False), width="stretch", hide_index=True)
else:
    st.caption("Priority recommendations appear after classification results are saved.")

st.subheader("Illustrative closed-loop action tracker")
tracker_path = DATA / "synthetic" / "action_tracker.csv"
if tracker_path.exists():
    st.dataframe(pd.read_csv(tracker_path), width="stretch", hide_index=True)
else:
    st.caption("Example actions are provided in data/synthetic/action_tracker.csv. Tracker items are illustrative, not customer commitments.")
