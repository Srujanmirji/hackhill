"""Walk-forward pair backtest on settlement prices, with no look-ahead.

Rules
  * Signal on day t uses only data up to t (rolling stats are shifted).
  * Trades execute at day t+1's settlement price plus a slippage penalty per leg.
  * Every position is closed before the broker cut-off ahead of the tender window.
  * Entry needs: |z| > z_entry, |residual| > cost hurdle + slippage, both legs above
    a minimum volume, and each leg's lots within `capacity_pct` of that leg's daily volume.
  * z_entry is chosen walk-forward: for each test month, pick the value that did best
    on all PRIOR months only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from aulens.costs import CostModel
from aulens.specs import MCX_FULL_HOLIDAYS
from aulens.normalize import gram_matched_lots, pair_panel, to_rs_per_10g_999
from aulens.specs import REGIME_BREAKS, SPECS


@dataclass
class Params:
    lookback: int = 20               # days for rolling mean / std of the residual
    z_exit: float = 0.3
    z_grid: tuple = (1.5, 2.0, 2.5)
    slippage_per_leg: float = 20.0   # ₹ per 10 g per leg per crossing (ASSUMPTION — see docs)
    min_volume: int = 50             # lots, both legs
    capacity_pct: float = 0.02       # each leg's lots <= this share of that leg's daily volume (1-5%)
    exit_buffer_days: int = 2        # extra trading days before the tender window
    lot_scale: int = 1
    min_train_months: int = 3
    costs: CostModel = field(default_factory=CostModel)


def expected_spread(p: pd.DataFrame, a: str, b: str, lookback: int) -> pd.Series:
    """Convergence target E. Same city + purity + expiry -> 0. Different expiry (GOLDM 5th vs
    GOLDTEN month-end) -> carry over the expiry gap, from the past-only curve carry. Otherwise
    the trailing median basis (e.g. Mumbai vs Ahmedabad), using past data only."""
    sa, sb = SPECS[a], SPECS[b]
    if sa.expiry_rule != sb.expiry_rule:
        return p["px10_b"] * np.expm1(p["carry"] * p["gap_days"] / 365)
    if sa.settle_city == sb.settle_city:
        return pd.Series(0.0, index=p.index)
    basis = p.groupby("expiry")["spread"].transform(lambda s: s.shift(1).rolling(lookback * 3, min_periods=lookback).median())
    return basis


def add_signals(p: pd.DataFrame, a: str, b: str, prm: Params) -> pd.DataFrame:
    p = p.copy()
    p["expected"] = expected_spread(p, a, b, prm.lookback)
    p["residual"] = p["spread"] - p["expected"]
    g = p.groupby("expiry")["residual"]
    mu = g.transform(lambda s: s.shift(1).rolling(prm.lookback, min_periods=prm.lookback // 2).mean())
    sd = g.transform(lambda s: s.shift(1).rolling(prm.lookback, min_periods=prm.lookback // 2).std())
    p["z"] = (p["residual"] - mu) / sd
    tender = max(SPECS[a].tender_days, SPECS[b].tender_days) + prm.exit_buffer_days
    # trading days still to come before expiry: rows left in the data, plus (for contracts still live
    # on the last data day) the weekdays after it that are not MCX full-day holidays
    last = p["date"].max()
    future = {e: len(pd.bdate_range(last + pd.Timedelta(days=1), e, freq="C", holidays=MCX_FULL_HOLIDAYS)) if e > last else 0
              for e in p["expiry"].unique()}
    p["days_left"] = (p.groupby("expiry")["date"].transform(lambda d: len(d) - 1 - np.arange(len(d)))
                      + p["expiry"].map(future))
    p["can_hold"] = p["days_left"] > tender
    lots_a, lots_b, _ = gram_matched_lots(a, b, prm.lot_scale)
    p["liquid"] = ((p["volume_a"] >= prm.min_volume) & (p["volume_b"] >= prm.min_volume)
                   & (lots_a <= prm.capacity_pct * p["volume_a"])     # capacity: our size stays a small
                   & (lots_b <= prm.capacity_pct * p["volume_b"]))    # share of what traded on day t
    return p


def _trades_for_expiry(e: pd.DataFrame, z_entry: float, prm: Params, grams: float) -> list[dict]:
    trades, pos, entry = [], 0, None
    rows = list(e.itertuples(index=False))
    for i in range(len(rows) - 1):
        r, nxt = rows[i], rows[i + 1]             # decide on day i, fill on day i+1
        if pos == 0:
            if not (r.can_hold and r.liquid and np.isfinite(r.z) and abs(r.z) > z_entry):
                continue
            hurdle = prm.costs.breakeven_per_10g(r.px10_a, grams) + 4 * prm.slippage_per_leg
            if abs(r.residual) <= hurdle:
                continue
            pos = -1 if r.z > 0 else 1        # spread rich -> short A / long B
            entry = nxt
            entry_date = nxt.date
        else:
            exit_now = (abs(r.z) < prm.z_exit) or (not nxt.can_hold) or (i + 1 == len(rows) - 1)
            if exit_now:
                gross = pos * (nxt.spread - entry.spread) * grams / 10
                cost = prm.costs.pair_round_trip(entry.px10_a * grams / 10, entry.px10_b * grams / 10)
                slip = 4 * prm.slippage_per_leg * grams / 10
                gold_move = (nxt.px10_a - entry.px10_a) * grams / 10
                trades.append({"entry_date": entry_date, "exit_date": nxt.date, "expiry": r.expiry,
                               "side": "long_spread" if pos > 0 else "short_spread",
                               "gross": gross, "costs": cost, "slippage": slip,
                               "net": gross - cost - slip, "gold_move_leg_a": gold_move,
                               "grams": grams})
                pos = 0
    return trades


def run_trades(p: pd.DataFrame, z_entry: float, prm: Params, grams: float) -> pd.DataFrame:
    out = []
    for _, e in p.groupby("expiry"):
        out += _trades_for_expiry(e, z_entry, prm, grams)
    return pd.DataFrame(out)


def walk_forward(df: pd.DataFrame, a: str, b: str, prm: Params | None = None) -> dict:
    prm = prm or Params()
    lots_a, lots_b, grams = gram_matched_lots(a, b, prm.lot_scale)
    p = pair_panel(df, a, b)
    if not p.empty:
        p = add_signals(p, a, b, prm)
    months = sorted(p["date"].dt.to_period("M").unique())
    all_trades, chosen = [], []
    for k in range(prm.min_train_months, len(months)):
        train = p[p["date"].dt.to_period("M") < months[k]]
        best_z, best_pnl = prm.z_grid[0], -np.inf
        for z in prm.z_grid:
            t = run_trades(train, z, prm, grams)
            pnl = t["net"].sum() if len(t) else 0.0
            if pnl > best_pnl:
                best_z, best_pnl = z, pnl
        test_trades = run_trades(p[p["date"].dt.to_period("M") <= months[k]], best_z, prm, grams)
        if len(test_trades):
            test_trades = test_trades[test_trades["entry_date"].dt.to_period("M") == months[k]]
            all_trades.append(test_trades.assign(z_entry=best_z))
        test = p[p["date"].dt.to_period("M") == months[k]]
        chosen.append({"month": str(months[k]), "z_entry": best_z,
                       "train_start": train["date"].min(), "train_end": train["date"].max(),
                       "test_start": test["date"].min(), "test_end": test["date"].max(),
                       "train_days": train["date"].nunique(), "test_days": test["date"].nunique()})
    trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame(
        columns=["entry_date", "exit_date", "expiry", "side", "gross", "costs", "slippage", "net",
                 "gold_move_leg_a", "grams", "z_entry"])
    return {"pair": (a, b), "lots": (lots_a, lots_b), "grams": grams, "panel": p,
            "trades": trades, "z_choices": pd.DataFrame(chosen), "params": prm}


def regime_of(d: pd.Timestamp) -> str:
    label = "Before 23 Jul 2024"
    for k, v in REGIME_BREAKS.items():
        if d >= pd.Timestamp(k):
            label = f"From {pd.Timestamp(k):%d %b %Y}"
    return label


def latest_signals(res: dict) -> pd.DataFrame:
    """Each contract's state on the last data day: does its residual clear the cost + slippage
    hurdle under the same entry rules the backtest uses (z_entry = the latest walk-forward choice)?"""
    p, prm = res["panel"], res["params"]
    z_entry = res["z_choices"]["z_entry"].iloc[-1] if len(res["z_choices"]) else prm.z_grid[0]
    last = p[p["date"] == p["date"].max()].copy()
    last["hurdle"] = [prm.costs.breakeven_per_10g(px, res["grams"]) + 4 * prm.slippage_per_leg for px in last["px10_a"]]
    last["clears"] = (last["can_hold"] & last["liquid"] & (last["z"].abs() > z_entry)
                      & (last["residual"].abs() > last["hurdle"]))
    return last[["date", "expiry", "residual", "hurdle", "z", "clears"]].reset_index(drop=True)


PLAUSIBLE_GAP = 0.05   # normalized prices further apart than this are almost surely a typo or the wrong contract


def check_gap(res: dict, expiry: pd.Timestamp, price_a: float, price_b: float) -> dict:
    """Judge two prices a trader sees for one contract of the pair with the backtest's own rules:
    convert both to ₹ per 10 g at 999, subtract the rules' expected spread (as of the last data day)
    and compare what is left with the cost + slippage hurdle. z-score and volume need history, so
    they are not part of a single-quote check."""
    a, b = res["pair"]
    prm = res["params"]
    row = res["panel"][res["panel"]["expiry"] == expiry].iloc[-1]
    px_a, px_b = to_rs_per_10g_999(price_a, a), to_rs_per_10g_999(price_b, b)
    spread = px_a - px_b
    residual = spread - row["expected"]
    hurdle = prm.costs.breakeven_per_10g(px_a, res["grams"]) + 4 * prm.slippage_per_leg
    if abs(spread) > PLAUSIBLE_GAP * px_a:
        status = "implausible"
    elif pd.isna(row["expected"]):
        status = "no_estimate"
    elif not row["can_hold"]:
        status = "late"
    elif abs(residual) <= hurdle:
        status = "inside"
    else:
        status = "clears"
    return {"as_of": row["date"], "quoted_gap": price_a - price_b, "spread": spread, "expected": row["expected"],
            "residual": residual, "hurdle": hurdle, "status": status}
