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
