"""Parse raw MCX Bhavcopy rows into a tidy, validated table.

Handles the known MCX quirks:
  * response Date is MM/DD/YYYY (requests use DD/MM/YYYY)
  * ExpiryDate is compact, e.g. 04SEP2026
  * Symbol values may be space-padded
  * a request for a holiday returns no rows (observed); assert_requested_date() still guards
    against a response for a different day
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
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


def apply_ddr(df: pd.DataFrame, ddr: pd.DataFrame) -> pd.DataFrame:
    """On each contract's final day, use MCX's Due Date Rate (final settlement price) as close.

    The Bhavcopy close on expiry day is the last trade of a thin, tender-window session, not
    the price the contract settles at. The original value is kept in `bhav_close`.
    `ddr` has columns Date (YYYY-MM-DD), Symbol, DDR (per the contract's own quote unit).
    """
    d = ddr.rename(columns={"Date": "date", "Symbol": "symbol", "DDR": "ddr"})[["date", "symbol", "ddr"]]
    d = d.assign(date=pd.to_datetime(d["date"]), symbol=d["symbol"].str.strip().str.upper())
    d = d.drop_duplicates(["date", "symbol"], keep="last")  # overlapping DDR downloads
    # The expiring contract is the nearest expiry still listed on the DDR date.
    front = (df.groupby(["symbol", "date"], as_index=False)["expiry"].min()
               .merge(d, on=["symbol", "date"]))
    out = df.merge(front, on=["symbol", "date", "expiry"], how="left")
    out["bhav_close"] = out["close"]
    out["close"] = out["ddr"].fillna(out["close"])
    return out.drop(columns="ddr")


def assert_requested_date(raw: pd.DataFrame, requested: pd.Timestamp) -> bool:
    """True only if MCX returned the day we asked for (it may return the nearest day)."""
    dates = pd.to_datetime(raw["Date"].astype(str).str.strip(), format="%m/%d/%Y").unique()
    return len(dates) == 1 and pd.Timestamp(dates[0]).normalize() == pd.Timestamp(requested).normalize()


PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "gold_futures.parquet"


def load_processed(path: str | Path = PROCESSED) -> pd.DataFrame:
    df = pd.read_parquet(path)
    required = {"date", "symbol", "expiry", "close", "volume", "oi", "source"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}.")
    if df.empty:
        raise ValueError("Dataset contains no contract rows.")
    for col in ("date", "expiry"):
        df[col] = pd.to_datetime(df[col], errors="raise")
        if df[col].dt.tz is not None:
            raise ValueError(f"Dataset {col} must contain local trading dates without a timezone.")
    for col in ("close", "volume", "oi"):
        df[col] = pd.to_numeric(df[col], errors="raise")
        if not np.isfinite(df[col]).all():
            raise ValueError(f"Dataset has missing or non-finite {col} values.")
    if df[list(required)].isna().any().any():
        raise ValueError("Dataset has missing required values.")
    if not df["symbol"].isin(SPECS).all() or not df["source"].isin(["MCX", "SYNTHETIC"]).all():
        raise ValueError("Dataset contains unsupported symbols or sources.")
    if ((df["close"] <= 0) | (df["volume"] < 0) | (df["oi"] < 0) | (df["date"] > df["expiry"])).any():
        raise ValueError("Dataset contains invalid prices, volumes, open interest or contract dates.")
    if df.duplicated(["date", "symbol", "expiry"]).any():
        raise ValueError("Dataset contains duplicate contract dates.")
    return df
