"""SYNTHETIC Bhavcopy generator — for development and UI work ONLY.

Produces MCX-shaped raw rows (MM/DD/YYYY dates, compact expiries, padded symbols) so the
whole pipeline can be built and tested before real data is in hand. Any chart made from
this data must be labelled "synthetic". Never present these numbers as findings.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from aulens.specs import SPECS


def _month_end_expiries(start, end, months_ahead=6):
    out = set()
    for d in pd.date_range(start, end, freq="MS"):
        for k in range(months_ahead):
            out.add((d + pd.offsets.MonthEnd(k + 1)).normalize())
    return sorted(out)


def make_sample(start="2025-04-01", end="2026-10-23", seed=7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start, end)
    # Ahmedabad 995 spot path (₹/10 g), with a duty-hike jump on 13 May 2026
    ret = rng.normal(0.0006, 0.009, len(days))
    ret[days.get_indexer([pd.Timestamp("2026-05-13")], method="bfill")[0]] += 0.05
    spot995 = 90000 * np.exp(np.cumsum(ret))
    spot999 = spot995 * 999 / 995
    carry = 0.10  # annualized
    mumbai_basis = np.where(days < "2026-05-13", 35.0, 90.0)  # ₹/10 g Mumbai premium

    rows = []
    for sym in ["GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]:
        spec = SPECS[sym]
        base_vol = {"GOLDTEN": 9000, "GOLDGUINEA": 2500, "GOLDPETAL": 150000}[sym]
        for exp in _month_end_expiries(start, end):
            live = (days >= exp - pd.DateOffset(months=6)) & (days <= exp)
            if not live.any():
                continue
            idx = np.where(live)[0]
            noise = np.zeros(len(idx))
            for i in range(1, len(idx)):
                noise[i] = 0.85 * noise[i - 1] + rng.normal(0, 25 if sym == "GOLDGUINEA" else 15)
            t = ((exp - days[idx]).days.values) / 365
            fair = spot999[idx] * np.exp(carry * t)
            if sym == "GOLDPETAL":
                fair = fair + mumbai_basis[idx]
            px10 = fair + noise
            quote = px10 * spec.quote_grams / 10
            quote = np.round(quote / spec.tick) * spec.tick
            months_out = np.clip((exp - days[idx]).days.values / 30, 0, 6)
            vol = (base_vol * np.exp(-0.9 * months_out) * rng.uniform(0.5, 1.5, len(idx))).astype(int)
            for j, i in enumerate(idx):
                c = quote[j]
                rows.append({
                    "Date": days[i].strftime("%m/%d/%Y"),
                    "Symbol": f"{sym:<12}",
                    "ExpiryDate": exp.strftime("%d%b%Y").upper(),
                    "Open": c, "High": c, "Low": c, "Close": c, "PreviousClose": np.nan,
                    "Volume": int(vol[j]), "OpenInterest": int(vol[j] * 3),
                    "InstrumentName": "FUTCOM",
                })
    return pd.DataFrame(rows)
