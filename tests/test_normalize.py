import numpy as np
import pandas as pd
import pytest

from aulens.data.loader import apply_ddr, tidy
from aulens.normalize import gram_matched_lots, to_rs_per_10g_999


def test_purity_and_units():
    assert to_rs_per_10g_999(100000, "GOLDTEN") == 100000
    assert to_rs_per_10g_999(80000, "GOLDGUINEA") == 100000          # ₹/8 g -> ₹/10 g
    assert to_rs_per_10g_999(10000, "GOLDPETAL") == 100000           # ₹/1 g -> ₹/10 g
    assert to_rs_per_10g_999(99500, "GOLDM") == pytest.approx(99900)  # 995 -> 999


def test_gram_matching():
    assert gram_matched_lots("GOLDTEN", "GOLDGUINEA") == (4, 5, 40.0)
    assert gram_matched_lots("GOLDTEN", "GOLDPETAL") == (1, 10, 10.0)
    assert gram_matched_lots("GOLDM", "GOLDTEN") == (1, 10, 100.0)


def test_tidy_handles_mcx_quirks():
    raw = pd.DataFrame({
        "Date": ["10/03/2026", "10/03/2026"], "Symbol": ["GOLDTEN     ", "CRUDEOIL  "],
        "ExpiryDate": ["30OCT2026", "19OCT2026"], "Close": [150000, 7000],
        "Volume": [10, 5], "OpenInterest": [100, 50],
    })
    t = tidy(raw)
    assert list(t["symbol"]) == ["GOLDTEN"]                         # padding stripped, non-gold dropped
    assert t["date"].iloc[0] == pd.Timestamp("2026-10-03")           # MM/DD/YYYY parsed
    assert t["expiry"].iloc[0] == pd.Timestamp("2026-10-30")


def test_apply_ddr_ignores_duplicate_ddr_rows():
    df = pd.DataFrame({"date": pd.to_datetime(["2026-09-29", "2026-09-30"]), "symbol": ["GOLDTEN"] * 2,
                       "expiry": pd.to_datetime(["2026-09-30"] * 2), "close": [148000.0, 148500.0]})
    ddr = pd.DataFrame({"Date": ["2026-09-30", "2026-09-30"], "Symbol": ["GOLDTEN", "GOLDTEN"], "DDR": [148206, 148206]})
    out = apply_ddr(df, ddr)
    assert len(out) == 2 and out["close"].tolist() == [148000.0, 148206.0]
    assert out["bhav_close"].tolist() == [148000.0, 148500.0]


def _curve(rate_by_day):
    """Two fixed GOLDTEN expiries priced off a moving spot with F = S·exp(r·τ)."""
    import numpy as np
    days = pd.bdate_range("2026-03-02", periods=len(rate_by_day))
    exps = [pd.Timestamp("2026-04-30"), pd.Timestamp("2026-05-29")]
    spot = 140000 * np.exp(np.linspace(0, 0.03, len(days)))
    return pd.DataFrame([{"date": d, "symbol": "GOLDTEN", "expiry": e,
                          "close": s * np.exp(r * (e - d).days / 365)}
                         for d, s, r in zip(days, spot, rate_by_day) for e in exps])


def test_carry_decomposition_constant_rate_is_all_rolldown():
    from aulens.normalize import carry_decomposition
    dec = carry_decomposition(_curve([0.08] * 15))
    assert len(dec) == 14
    assert dec["curve"].abs().max() < 1e-6                        # the curve never moved
    assert (dec["rolldown"] < 0).all()                            # premium decays toward spot
    # one weekday = 1 calendar day of decay: ≈ r/365 of the next contract's price
    assert dec["rolldown"].iloc[0] == pytest.approx(-0.08 / 365 * 140000 * np.exp(0.08 * 88 / 365), rel=0.01)


def test_carry_decomposition_adds_up_when_the_rate_moves():
    from aulens.normalize import carry_decomposition, curve_carry
    df = _curve([0.06 + 0.002 * i for i in range(10)])
    dec = carry_decomposition(df)
    s = curve_carry(df)
    days = sorted(df["date"].unique())
    tau = [(pd.Timestamp("2026-05-29") - d).days / 365 for d in days]
    nxt = df[df["expiry"] == pd.Timestamp("2026-05-29")].set_index("date")["close"]
    for k in range(1, len(days)):
        total = (s.iloc[k] * tau[k] - s.iloc[k - 1] * tau[k - 1]) * nxt.iloc[k - 1]
        assert dec["rolldown"].iloc[k - 1] + dec["curve"].iloc[k - 1] == pytest.approx(total)
    assert (dec["curve"] > 0).all()
