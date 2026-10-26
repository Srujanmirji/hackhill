import pandas as pd
import pytest

from app.report import report


@pytest.mark.parametrize("sources", [["MCX"], ["SYNTHETIC"], ["MCX", "SYNTHETIC"]])
def test_report_uses_actual_sources(sources):
    df = pd.DataFrame({"source": sources, "date": pd.to_datetime(["2025-04-01"] * len(sources))})
    v = {"pair": "GOLDTEN vs GOLDGUINEA", "lots": "4 vs 5", "trades": 0,
         "verdict": "UNTESTABLE", "reason": "No trades."}
    text = report(v, df, "GOLDTEN", 20, 50, 1, 2)
    assert f"Data: {', '.join(sorted(sources))} settlement data" in text
    if sources == ["SYNTHETIC"]:
        assert "MCX settlement data" not in text
