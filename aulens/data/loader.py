"""Parse raw MCX Bhavcopy rows into a tidy, validated table.

Handles the known MCX quirks:
  * response Date is MM/DD/YYYY (requests use DD/MM/YYYY)
  * ExpiryDate is compact, e.g. 04SEP2026
  * Symbol values may be space-padded
  * MCX may silently return a different (nearest) trading day -> caller must check
"""
from __future__ import annotations

import pandas as pd

from aulens.specs import SPECS

GOLD_SYMBOLS = set(SPECS)

COLMAP = {  # lower-cased raw header -> tidy name
    "date": "date", "symbol": "symbol", "expirydate": "expiry",
    "open": "open", "high": "high", "low": "low", "close": "close",
    "previousclose": "prev_close", "volume": "volume", "openinterest": "oi",
    "instrumentname": "instrument",
}


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    """Return one row per (date, symbol, expiry) for MCX gold futures only."""
    df = raw.rename(columns={c: COLMAP.get(c.replace(" ", "").lower(), c) for c in raw.columns})
    missing = {"date", "symbol", "expiry", "close", "volume", "oi"} - set(df.columns)
    if missing:
        raise ValueError(f"Bhavcopy is missing columns: {sorted(missing)}")

    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df = df[df["symbol"].isin(GOLD_SYMBOLS)].copy()
    if "instrument" in df.columns:  # keep futures only (drop options)
        df = df[df["instrument"].astype(str).str.strip().str.upper().str.startswith("FUT")]

    df["date"] = pd.to_datetime(df["date"].astype(str).str.strip(), format="%m/%d/%Y")
    df["expiry"] = pd.to_datetime(df["expiry"].astype(str).str.strip().str.upper(), format="%d%b%Y")
    for c in ["open", "high", "low", "close", "prev_close", "volume", "oi"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df[(df["close"] > 0) & (df["date"] <= df["expiry"])]
    df = df.drop_duplicates(["date", "symbol", "expiry"], keep="last")
    return df.sort_values(["symbol", "expiry", "date"]).reset_index(drop=True)


def assert_requested_date(raw: pd.DataFrame, requested: pd.Timestamp) -> bool:
    """True only if MCX returned the day we asked for (it may return the nearest day)."""
    dates = pd.to_datetime(raw["Date"].astype(str).str.strip(), format="%m/%d/%Y").unique()
    return len(dates) == 1 and pd.Timestamp(dates[0]).normalize() == pd.Timestamp(requested).normalize()


def load_processed(path: str = "data/processed/gold_futures.parquet") -> pd.DataFrame:
    return pd.read_parquet(path)
