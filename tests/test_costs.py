import pytest

from aulens.costs import CostModel


def test_brokerage_cap():
    c = CostModel()
    # ₹14.6 lakh order: 0.03% = ₹438 -> capped at ₹20
    assert c.order(1_460_000, "buy") < c.order(1_460_000, "sell")    # CTT only on sell


def test_breakeven_matches_research_table():
    c = CostModel()
    assert c.breakeven_per_10g(146_000, 40) == pytest.approx(74, abs=4)    # 4 TEN vs 5 GUINEA
    assert c.breakeven_per_10g(146_000, 10) == pytest.approx(145, abs=6)   # 1 TEN vs 10 PETAL
