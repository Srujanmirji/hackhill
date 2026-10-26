"""Downloadable verdict summary, including the actual dataset source."""
from aulens.specs import UNITS, metal


def report(v, df, a, slip, min_vol, scale, cap_pct):
    """Plain-text summary of the verdict and the assumptions it was made under."""
    lo, hi = v.get("mean_trade_ci90", (float("nan"), float("nan")))
    reg = v["by_regime"].to_string() if "by_regime" in v else "no trades"
    return f"""AuLens verdict report
Pair: {v['pair']} ({v['lots']})
Data: {", ".join(sorted(df["source"].unique()))} settlement data {df['date'].min():%d %b %Y} to {df['date'].max():%d %b %Y}
Verdict: {v['verdict']}. {v['reason']}

Assumptions
  Slippage per {UNITS[metal(a)][1]} per leg: Rs {slip}
  Minimum daily volume, both legs: {min_vol} lots
  Capacity cap: {cap_pct}% of each leg's daily volume
  Size multiplier: {scale}

Results
  Trades (walk-forward): {v['trades']}
  Gross P&L: Rs {v.get('gross_pnl', 0):,.0f}   Costs: Rs {v.get('costs', 0):,.0f}   Slippage: Rs {v.get('slippage', 0):,.0f}
  Net P&L: Rs {v.get('net_pnl', 0):,.0f}   Win rate: {v.get('hit_rate', 0):.0%}
  Net Sharpe: {v.get('net_sharpe', float('nan')):.2f}   {metal(a).title()} beta: {v.get('gold_beta', float('nan')):.3f}
  Break-even slippage: Rs {v.get('breakeven_slippage_per_leg', float('nan')) * UNITS[metal(a)][0]:.1f} per {UNITS[metal(a)][1]} per leg
  90% CI of the mean trade: Rs {lo:,.0f} to Rs {hi:,.0f}

By regime
{reg}

Method: walk-forward z_entry, signals on day t, fills at t+1 settlement, exits before the tender window.
Not financial advice. https://github.com/Srujanmirji/hackhill
"""

