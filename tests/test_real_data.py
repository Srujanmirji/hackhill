"""Sanity checks on the real MCX dataset. Skipped until the parquet has been built."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aulens.normalize import implied_carry, pair_panel  # noqa: E402

PARQUET = Path(__file__).resolve().parents[1] / "data" / "processed" / "gold_futures.parquet"
pytestmark = pytest.mark.skipif(not PARQUET.exists(), reason="data/processed/gold_futures.parquet not built")


@pytest.fixture(scope="module")
def df():
    d = pd.read_parquet(PARQUET)
    if (d["source"] != "MCX").any():
        pytest.skip("parquet holds SYNTHETIC data")
    return d


def test_one_row_per_contract_day(df):
    assert not df.duplicated(["date", "symbol", "expiry"]).any()


def test_prices_positive_and_before_expiry(df):
    assert (df["close"] > 0).all()
    assert (df["date"] <= df["expiry"]).all()


def test_control_pair_converges_into_expiry(df):
    """GOLDTEN vs GOLDGUINEA share city, purity and expiry, so the normalized spread must
    be smaller in the last 5 trading days than in the first half of each contract's life,
    and ~0 at the final settlement (DDR)."""
    p = pair_panel(df, "GOLDTEN", "GOLDGUINEA")
    p = p[p["expiry"] <= df["date"].max()]           # expired contracts only
    first_half, last5, final = [], [], []
    for _, g in p.groupby("expiry"):
        s = g.sort_values("date")["spread"]
        first_half.append(s.abs().iloc[: len(s) // 2])
        last5.append(s.abs().iloc[-5:])
        final.append(s.iloc[-1])
    assert len(final) > 0
    assert pd.concat(last5).median() < pd.concat(first_half).median()
    assert max(abs(x) for x in final) <= 2.0          # ₹ per 10 g: tick rounding on the DDR


def test_goldm_pairs_with_previous_month_goldten(df):
    p = pair_panel(df, "GOLDM", "GOLDTEN")
    assert ((p["expiry_a"].dt.to_period("M") - p["expiry"].dt.to_period("M")).map(lambda d: d.n) == 1).all()
    assert p["gap_days"].between(1, 10).all()


def test_carry_uses_past_data_only(df):
    last = df["date"].max()
    shocked = df.copy()
    shocked.loc[(shocked["date"] == last) & (shocked["symbol"] == "GOLDTEN"), "close"] *= 2
    assert implied_carry(df)[last] == implied_carry(shocked)[last]


def test_curve_carry_is_annualized_front_to_next(df):
    from aulens.normalize import curve_carry
    c = curve_carry(df)
    assert c.notna().all() and c.between(-1, 1).all()   # annual rate; Jan 2026 rally peaks near 51%
