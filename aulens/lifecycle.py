"""Contract lifecycle: how long contracts are listed and when they become liquid enough to trade."""
from __future__ import annotations

import numpy as np
import pandas as pd


def liquidity_profile(df: pd.DataFrame, symbol: str, min_volume: int) -> tuple[pd.DataFrame, dict]:
    """Median daily volume (lots) by trading days to expiry, over contracts whose whole life is in
    the data: listed after the first data day and expired by the last. Trading days are the rows
    MCX published, so holidays are already excluded.

    Only days covered by at least half of those contracts are kept, so the far end of the curve is
    not one long-lived contract. Summary: number of such contracts, median trading days from
    listing to expiry, the day with the highest median volume, and the furthest-from-expiry day at
    which the median volume reaches `min_volume` (None if never)."""
    d = df[df["symbol"] == symbol].sort_values(["expiry", "date"])
    first, last = df["date"].min(), df["date"].max()
    life = d.groupby("expiry")["date"].agg(["min", "size"])
    whole = life[(life["min"] > first) & (life.index <= last)]
    w = d[d["expiry"].isin(whole.index)]
    w = w.assign(days_to_expiry=w.groupby("expiry")["date"].transform(lambda x: len(x) - 1 - np.arange(len(x))))
    prof = (w.groupby("days_to_expiry")["volume"].agg(volume="median", contracts="size")
              .reset_index().sort_values("days_to_expiry"))
    prof = prof[prof["contracts"] >= max(2, -(-len(whole) // 2))].reset_index(drop=True)
    liquid = prof.loc[prof["volume"] >= min_volume, "days_to_expiry"]
    return prof, {"contracts": len(whole), "listed_days": float(whole["size"].median()) if len(whole) else float("nan"),
                  "peak_day": int(prof.loc[prof["volume"].idxmax(), "days_to_expiry"]) if len(prof) else None,
                  "liquid_from": int(liquid.max()) if len(liquid) else None}
