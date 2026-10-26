"""Exchange-rule normalization: every contract -> ₹ per 10 g at 999 purity."""
from __future__ import annotations

from math import gcd

import numpy as np
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


def curve_carry(df: pd.DataFrame, symbol: str = "GOLDTEN") -> pd.Series:
    """Annualized carry implied by the futures curve on each day: ln(next / front) per year
    between the two nearest listed expiries of `symbol`."""
    c = df[df.symbol == symbol].sort_values(["date", "expiry"]).groupby("date").head(2)
    g = c.groupby("date")
    years = (g["expiry"].last() - g["expiry"].first()).dt.days / 365
    return (np.log(g["close"].last() / g["close"].first()) / years).rename("carry")


def implied_carry(df: pd.DataFrame, symbol: str = "GOLDTEN", window: int = 60) -> pd.Series:
    """`curve_carry` as a trailing median over `window` days, shifted one day so the value on
    day t uses only days before t."""
    return curve_carry(df, symbol).shift(1).rolling(window, min_periods=window // 3).median().rename("carry")


def pair_panel(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Same-date rows for legs a and b. Never a continuous near-month series.

    Same expiry rule -> pair identical expiries. Different rules (GOLDM on the 5th vs GOLDTEN
    at month-end) -> pair a's month M+1 contract with b's month M contract; `expiry` is then b's
    (earlier) expiry and `expiry_a` a's, and `carry` / `gap_days` are added for the expected spread.
    """
    n = normalize(df)
    cols = ["date", "expiry", "close", "px10", "volume", "oi"]
    left = n[n.symbol == a][cols].rename(columns={c: f"{c}_a" for c in cols[2:]})
    right = n[n.symbol == b][cols].rename(columns={c: f"{c}_b" for c in cols[2:]})
    if SPECS[a].expiry_rule == SPECS[b].expiry_rule:
        p = left.merge(right, on=["date", "expiry"], how="inner")
    else:
        left = left.rename(columns={"expiry": "expiry_a"})
        left["month"] = (left["expiry_a"].dt.to_period("M") - 1)
        right["month"] = right["expiry"].dt.to_period("M")
        p = left.merge(right, on=["date", "month"], how="inner").drop(columns="month")
        p["gap_days"] = (p["expiry_a"] - p["expiry"]).dt.days
        p = p.merge(implied_carry(df, b), left_on="date", right_index=True, how="left")
    p["spread"] = p["px10_a"] - p["px10_b"]   # ₹ per 10 g @ 999
    return p.sort_values(["expiry", "date"]).reset_index(drop=True)
