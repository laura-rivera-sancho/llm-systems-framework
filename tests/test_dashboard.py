from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_loads_from_synthetic_data_without_exceptions():
    script = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    app = AppTest.from_file(script, default_timeout=30).run()

    assert not app.exception
    assert [item.value for item in app.title] == ["Voice of Customer Analytics"]
    assert len(app.metric) == 11
    assert len(app.get("plotly_chart")) == 7
    metric_labels = [item.label for item in app.metric]
    assert "Net Promoter Score" in metric_labels
    assert "Average rating" in metric_labels
    assert len(app.dataframe) >= 1
