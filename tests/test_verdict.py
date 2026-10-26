import pandas as pd
import pytest

from aulens.verdict import verdict


def result(net, dates=None):
    n = len(net)
    return {
        "pair": ("GOLDTEN", "GOLDGUINEA"), "lots": (4, 5), "grams": 40,
        "panel": pd.DataFrame({"date": [pd.Timestamp("2025-04-01")]}),
        "trades": pd.DataFrame({
            "net": net, "gross": net, "costs": [0] * n, "slippage": [0] * n,
            "grams": [40] * n, "gold_move_leg_a": range(n),
            "entry_date": pd.to_datetime(dates or ["2025-05-01"] * n),
            "exit_date": pd.to_datetime(dates or ["2025-05-02"] * n),
        }),
    }


def test_no_edge_lists_each_failed_check():
    v = verdict(result([-100] * 10))
    assert v["verdict"] == "NO EDGE"
    assert "Total net P&L is not positive" in v["reason"]
    assert "90% confidence interval" in v["reason"]
    assert "From 01 Apr 2025" in v["reason"]


def test_positive_pnl_only_reports_failed_confidence_check():
    v = verdict(result([-10] * 9 + [100]))
    assert v["net_pnl"] > 0 and v["verdict"] == "NO EDGE"
    assert "90% confidence interval" in v["reason"]
    assert "Total net" not in v["reason"] and "tested regime" not in v["reason"]


def test_regime_failure_can_fail_despite_positive_confidence_interval():
    v = verdict(result([100] * 19 + [-1], ["2025-05-01"] * 19 + ["2026-06-01"]))
    assert v["verdict"] == "NO EDGE" and v["mean_trade_ci90"][0] > 0
    assert "From 13 May 2026" in v["reason"]
    assert "90% confidence interval" not in v["reason"]


def test_edge_threshold_and_minimum_sample_unchanged():
    assert verdict(result(list(range(1, 11))))["verdict"] == "EDGE"
    v = verdict(result([10] * 9))
    assert v["verdict"] == "UNTESTABLE" and "need at least 10" in v["reason"]


@pytest.mark.parametrize("empty_panel", [False, True])
def test_no_trades_distinguishes_missing_pair_from_filters(empty_panel):
    res = result([])
    if empty_panel:
        res["panel"] = pd.DataFrame()
    v = verdict(res)
    assert v["verdict"] == "UNTESTABLE"
    assert ("No overlapping contract dates" in v["reason"]) == empty_panel
