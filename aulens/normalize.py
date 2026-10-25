"""Exchange-rule normalization: every contract -> ₹ per 10 g at 999 purity."""
from __future__ import annotations

from math import gcd

import pandas as pd

from aulens.specs import SPECS


def to_rs_per_10g_999(price: float | pd.Series, symbol: str):
    s = SPECS[symbol]
    return price * (10 / s.quote_grams) * (999 / s.purity)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["px10"] = [to_rs_per_10g_999(p, s) for p, s in zip(out["close"], out["symbol"])]
    return out


def gram_matched_lots(a: str, b: str, scale: int = 1) -> tuple[int, int, float]:
    """Smallest lot counts with equal grams on both legs, e.g. TEN/GUINEA -> (4, 5, 40 g)."""
    ga, gb = int(SPECS[a].lot_grams), int(SPECS[b].lot_grams)
    lcm = ga * gb // gcd(ga, gb)
    return scale * lcm // ga, scale * lcm // gb, float(scale * lcm)


def pair_panel(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Same-date, same-expiry rows for legs a and b. Never a continuous near-month series."""
    n = normalize(df)
    cols = ["date", "expiry", "close", "px10", "volume", "oi"]
    left = n[n.symbol == a][cols].rename(columns={c: f"{c}_a" for c in cols[2:]})
    right = n[n.symbol == b][cols].rename(columns={c: f"{c}_b" for c in cols[2:]})
    p = left.merge(right, on=["date", "expiry"], how="inner")
    p["spread"] = p["px10_a"] - p["px10_b"]   # ₹ per 10 g @ 999
    return p.sort_values(["expiry", "date"]).reset_index(drop=True)
