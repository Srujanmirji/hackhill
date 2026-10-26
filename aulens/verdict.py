"""Turn a walk-forward result into an honest per-pair verdict."""
from __future__ import annotations

import numpy as np
import pandas as pd

from aulens.backtest import regime_of


def gold_beta(trades: pd.DataFrame) -> tuple[float, float]:
    """Regress trade net P&L on the gold move of leg A over the same holding period."""
    if len(trades) < 5 or trades["gold_move_leg_a"].std() == 0:
        return float("nan"), float("nan")
    beta, alpha = np.polyfit(trades["gold_move_leg_a"], trades["net"], 1)
    return float(alpha), float(beta)


def bootstrap_mean_ci(x: np.ndarray, n: int = 2000, seed: int = 0) -> tuple[float, float]:
    if len(x) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return float(np.percentile(means, 5)), float(np.percentile(means, 95))


def net_sharpe(trades: pd.DataFrame) -> float:
    """Per-trade Sharpe of net P&L, annualized by how often the pair actually traded:
    mean / std * sqrt(trades per year). Trades are irregular, so this is not a daily-returns
    Sharpe; it answers "is the average trade large relative to its noise, at this pace?"."""
    if len(trades) < 2 or trades["net"].std() == 0:
        return float("nan")
    years = max((trades["exit_date"].max() - trades["entry_date"].min()).days / 365.25, 1 / 365.25)
    return float(trades["net"].mean() / trades["net"].std() * np.sqrt(len(trades) / years))


def verdict(res: dict, min_trades: int = 10) -> dict:
    t = res["trades"]
    g = res["grams"]
    size = f"{g / 1000:g} kg" if g >= 1000 else f"{g:.0f} g"
    out = {"pair": f"{res['pair'][0]} vs {res['pair'][1]}",
           "lots": f"{res['lots'][0]} x {res['pair'][0]}  vs  {res['lots'][1]} x {res['pair'][1]}  ({size})",
           "trades": len(t)}
    if len(t) == 0:
        reason = ("No overlapping contract dates for this pair. Load data for both legs with matching contract months."
                  if res["panel"].empty else "No trades cleared the cost hurdle and filters, or there is too little training history.")
        return {**out, "verdict": "UNTESTABLE", "reason": reason}

    net, gross = t["net"].sum(), t["gross"].sum()
    crossings_10g = (4 * t["grams"] / 10).sum()
    pre_slip = net + t["slippage"].sum()
    lo, hi = bootstrap_mean_ci(t["net"].to_numpy())
    alpha, beta = gold_beta(t)
    tt = t.assign(regime=t["entry_date"].map(regime_of), _d=t["entry_date"])
    by_regime = (tt.groupby("regime").agg(count=("net", "size"), sum=("net", "sum"), start=("_d", "min"))
                   .sort_values("start").drop(columns="start"))

    out.update({
        "gross_pnl": gross, "costs": t["costs"].sum(), "slippage": t["slippage"].sum(), "net_pnl": net,
        "hit_rate": float((t["net"] > 0).mean()),
        "mean_trade_ci90": (lo, hi),
        "breakeven_slippage_per_leg": pre_slip / crossings_10g if crossings_10g else float("nan"),
        "gold_beta": beta, "alpha_per_trade": alpha, "net_sharpe": net_sharpe(t),
        "by_regime": by_regime,
    })
    if len(t) < min_trades:
        out.update(verdict="UNTESTABLE", reason=f"Only {len(t)} trades; need at least {min_trades}.")
    elif lo > 0 and (by_regime["sum"] > 0).all():
        out.update(verdict="EDGE", reason="Positive after costs and slippage, in every regime, with the 90% CI above zero.")
    else:
        failed = []
        if net <= 0:
            failed.append("Total net P&L is not positive after costs and slippage.")
        if not lo > 0:
            failed.append("The 90% confidence interval for the average net trade is not entirely above zero.")
        weak = by_regime.index[by_regime["sum"] <= 0].tolist()
        if weak:
            failed.append(f"Net P&L is not positive in {len(weak)} tested {'regime' if len(weak) == 1 else 'regimes'}: {', '.join(weak)}.")
        out.update(verdict="NO EDGE", reason=" ".join(failed))
    return out
