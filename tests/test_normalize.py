import pandas as pd
import pytest

from aulens.data.loader import tidy
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
