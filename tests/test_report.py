import pandas as pd
import pytest

from app.report import report


@pytest.mark.parametrize("sources", [["MCX"], ["SYNTHETIC"], ["MCX", "SYNTHETIC"]])
def test_report_uses_actual_sources(sources):
    df = pd.DataFrame({"source": sources, "date": pd.to_datetime(["2025-04-01"] * len(sources))})
    v = {"pair": "GOLDTEN vs GOLDGUINEA", "lots": "4 vs 5", "trades": 0,
         "verdict": "UNTESTABLE", "reason": "No trades."}
    text = report(v, {"z_choices": pd.DataFrame()}, df, "GOLDTEN", 20, 50, 1, 2)
    assert f"Data: {', '.join(sorted(sources))} settlement data" in text
    assert "No final untouched holdout" in text
    assert "next available settlement" in text
    assert "margin capital and funding" in text
    assert "not risk-adjusted" in text
    if sources == ["SYNTHETIC"]:
        assert "MCX settlement data" not in text


def test_report_includes_monthly_training_and_test_dates():
    from aulens.backtest import walk_forward
    from aulens.data.loader import tidy
    from aulens.data.sample import make_sample
    from aulens.verdict import verdict
    df = tidy(make_sample(start="2025-04-01", end="2025-08-31")).assign(source="SYNTHETIC")
    res = walk_forward(df, "GOLDTEN", "GOLDGUINEA")
    text = report(verdict(res), res, df, "GOLDTEN", 20, 50, 1, 2)
    assert "train_end" in text and "test_start" in text
    assert "2025-07" in text and "2025-08" in text
