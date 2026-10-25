"""Indian commodity-futures transaction costs (configurable; defaults = discount broker, 2026).

Verify against your broker's charges page before quoting numbers in a pitch.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostModel:
    brokerage_pct: float = 0.0003     # 0.03% ...
    brokerage_cap: float = 20.0       # ... or ₹20 per order, whichever is lower
    exch_pct: float = 0.000021        # MCX transaction charge, per side
    ctt_sell_pct: float = 0.0001      # CTT, sell side, non-agri
    stamp_buy_pct: float = 0.00002    # stamp duty, buy side
    sebi_per_crore: float = 10.0
    gst_pct: float = 0.18             # on brokerage + exchange + SEBI

    def order(self, notional: float, side: str) -> float:
        brok = min(self.brokerage_pct * notional, self.brokerage_cap)
        exch = self.exch_pct * notional
        sebi = self.sebi_per_crore * notional / 1e7
        gst = self.gst_pct * (brok + exch + sebi)
        ctt = self.ctt_sell_pct * notional if side == "sell" else 0.0
        stamp = self.stamp_buy_pct * notional if side == "buy" else 0.0
        return brok + exch + sebi + gst + ctt + stamp

    def pair_round_trip(self, notional_a: float, notional_b: float) -> float:
        """Each leg is bought once and sold once: 4 orders."""
        return (self.order(notional_a, "buy") + self.order(notional_a, "sell")
                + self.order(notional_b, "buy") + self.order(notional_b, "sell"))

    def breakeven_per_10g(self, px10: float, grams: float) -> float:
        notional = px10 * grams / 10
        return self.pair_round_trip(notional, notional) / (grams / 10)
