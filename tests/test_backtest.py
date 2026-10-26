import pandas as pd
import pytest

from aulens.backtest import Params, add_signals, walk_forward
from aulens.data.loader import tidy
from aulens.data.sample import make_sample
from aulens.normalize import pair_panel


def _df():
    return tidy(make_sample(start="2025-04-01", end="2026-01-31"))


def test_no_lookahead_in_zscore():
    df = _df()
    p = add_signals(pair_panel(df, "GOLDTEN", "GOLDGUINEA"), "GOLDTEN", "GOLDGUINEA", Params())
    # Changing today's spread must not change today's rolling mean/std inputs:
    q = p.copy()
    last = q.index[q["expiry"] == q["expiry"].iloc[0]][-1]
    q.loc[last, "spread"] += 1e6
    q2 = add_signals(q.drop(columns=["expected", "residual", "z", "days_left", "can_hold", "liquid"]),
                     "GOLDTEN", "GOLDGUINEA", Params())
    assert (p["z"].drop(index=last).fillna(0) == q2["z"].drop(index=last).fillna(0)).all()


def test_trades_close_before_tender():
    res = walk_forward(_df(), "GOLDTEN", "GOLDGUINEA", Params(min_train_months=2))
    t = res["trades"]
    if len(t):
        p = res["panel"].set_index(["expiry", "date"])
        for _, tr in t.iterrows():
            assert p.loc[(tr.expiry, tr.exit_date), "days_left"] >= 0
            assert tr.exit_date >= tr.entry_date


def test_capacity_cap_blocks_thin_days():
    df = _df()
    p = pair_panel(df, "GOLDTEN", "GOLDGUINEA")
    loose = add_signals(p, "GOLDTEN", "GOLDGUINEA", Params(min_volume=0, capacity_pct=1.0))
    tight = add_signals(p, "GOLDTEN", "GOLDGUINEA", Params(min_volume=0, capacity_pct=0.01))
    # 5 GOLDGUINEA lots at 1% needs >= 500 lots traded on that leg
    assert not (tight["liquid"] & (tight["volume_b"] < 500)).any()
    assert tight["liquid"].sum() < loose["liquid"].sum()


def test_net_sharpe_and_latest_signals():
    from aulens.backtest import latest_signals
    from aulens.verdict import net_sharpe
    t = pd.DataFrame({"net": [100.0, -50.0, 80.0, 20.0],
                      "entry_date": pd.to_datetime(["2025-01-01"] * 4), "exit_date": pd.to_datetime(["2026-01-01"] * 4)})
    assert net_sharpe(t) == pytest.approx(t["net"].mean() / t["net"].std() * (4 / (365 / 365.25)) ** 0.5)
    res = walk_forward(_df(), "GOLDTEN", "GOLDGUINEA", Params(min_train_months=2))
    sig = latest_signals(res)
    assert (sig["date"] == res["panel"]["date"].max()).all() and sig["clears"].dtype == bool


def test_check_gap_normalizes_then_compares_to_the_hurdle():
    from aulens.backtest import check_gap
    res = walk_forward(_df(), "GOLDTEN", "GOLDGUINEA", Params(min_train_months=2))
    p = res["panel"]
    exp = p[(p["date"] == p["date"].max()) & p["can_hold"]]["expiry"].max()
    same = check_gap(res, exp, 140000.0, 112000.0)      # GOLDGUINEA quotes per 8 g: same gold, ₹0 spread
    assert same["quoted_gap"] == 28000 and same["spread"] == pytest.approx(0) and same["status"] == "inside"
    wide = check_gap(res, exp, 140000.0, 111700.0)      # 111700 per 8 g = 139625 per 10 g: ₹375 apart
    assert wide["spread"] == pytest.approx(375) and wide["status"] == "clears" and wide["residual"] > wide["hurdle"]
    assert check_gap(res, exp, 140000.0, 100000.0)["status"] == "implausible"   # 125000 per 10 g: a typo


def test_missing_pair_returns_untestable_instead_of_crashing():
    from aulens.verdict import verdict
    df = _df()
    df = df[df["symbol"] == "GOLDTEN"]
    res = walk_forward(df, "GOLDTEN", "GOLDGUINEA")
    assert res["panel"].empty and res["trades"].empty
    assert verdict(res)["verdict"] == "UNTESTABLE"


def test_walk_forward_evidence_uses_only_prior_months():
    df = _df()
    res = walk_forward(df, "GOLDTEN", "GOLDGUINEA")
    folds = res["z_choices"]
    assert len(folds) == 7
    assert folds.iloc[0]["month"] == "2025-07"
    for row in folds.itertuples():
        train = res["panel"][res["panel"]["date"].dt.to_period("M") < pd.Period(row.month)]
        test = res["panel"][res["panel"]["date"].dt.to_period("M") == pd.Period(row.month)]
        assert row.train_start == train["date"].min()
        assert row.train_end == train["date"].max() < row.test_start
        assert row.test_start == test["date"].min() and row.test_end == test["date"].max()
        assert row.train_days == train["date"].nunique() and row.test_days == test["date"].nunique()
        assert row.z_entry in Params().z_grid
    shocked = df.copy()
    shocked.loc[shocked["date"] >= "2026-01-01", "close"] *= 2
    # Even January's threshold must be frozen before the January shock.
    pd.testing.assert_frame_equal(folds, walk_forward(shocked, "GOLDTEN", "GOLDGUINEA")["z_choices"])


def test_simulated_trade_uses_next_observation_and_deducts_model_costs():
    from aulens.backtest import _trades_for_expiry
    prm = Params(slippage_per_leg=2)
    days = pd.to_datetime(["2025-07-01", "2025-07-03", "2025-07-04", "2025-07-07"])
    panel = pd.DataFrame({"date": days, "expiry": pd.Timestamp("2025-07-31"),
                          "spread": [20, 30, 25, 10], "px10_a": [110, 120, 115, 100],
                          "px10_b": [90, 90, 90, 90], "z": [2, 2, 0, 0],
                          "residual": 1000, "can_hold": True, "liquid": True})
    trade, = _trades_for_expiry(panel, 1.5, prm, 40)
    assert trade["entry_date"] == days[1] and trade["exit_date"] == days[3]
    assert trade["gross"] == 80  # short spread, (30 - 10) * 40/10
    assert trade["costs"] == pytest.approx(prm.costs.pair_round_trip(120 * 4, 90 * 4))
    assert trade["slippage"] == 4 * 2 * 4
    assert trade["net"] == pytest.approx(80 - trade["costs"] - trade["slippage"])


@pytest.mark.parametrize("direction", [-1, 1])
@pytest.mark.parametrize("observations", [2, 3])
def test_terminal_entry_is_closed_and_charged(direction, observations):
    from aulens.backtest import _trades_for_expiry
    panel = pd.DataFrame({"date": pd.date_range("2025-07-01", periods=3),
                          "expiry": pd.Timestamp("2025-07-31"), "spread": [0, 30, 20],
                          "px10_a": [90, 120, 110], "px10_b": 90, "z": [0, 2 * direction, 2 * direction],
                          "residual": 1000, "can_hold": True, "liquid": True})
    panel = panel.tail(observations)
    prm = Params()
    trade, = _trades_for_expiry(panel, 1.5, prm, 40)
    assert trade["entry_date"] == trade["exit_date"] == panel["date"].iloc[-1]
    assert trade["side"] == ("short_spread" if direction > 0 else "long_spread")
    assert trade["gross"] == trade["gold_move_leg_a"] == 0
    assert trade["costs"] == pytest.approx(prm.costs.pair_round_trip(110 * 4, 90 * 4))
    assert trade["slippage"] == 4 * prm.slippage_per_leg * 4
    assert trade["net"] == pytest.approx(-trade["costs"] - trade["slippage"])
