"""Contract rulebook for MCX gold futures.

Every number here should be checked against the latest MCX contract-specification
PDFs before a pitch (see docs/CONTRACT_SPECS.md). Values follow MCX/TRD/456/2025.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ContractSpec:
    symbol: str
    lot_grams: float        # grams per lot
    quote_grams: float      # price is quoted per this many grams
    purity: int             # 995 or 999
    settle_city: str        # city of the polled spot that sets the DDR
    expiry_rule: str        # "5th" or "month_end"
    ddr_days_avg: int       # 3 = simple average of last 3 polled spots; 1 = expiry-day poll
    tender_days: int        # staggered delivery (tender) window, trading days
    tick: float = 1.0       # in quote units


SPECS = {
    "GOLD":       ContractSpec("GOLD",       1000, 10, 995, "Ahmedabad", "5th",       3, 5),
    "GOLDM":      ContractSpec("GOLDM",       100, 10, 995, "Ahmedabad", "5th",       3, 5),
    "GOLDTEN":    ContractSpec("GOLDTEN",      10, 10, 999, "Ahmedabad", "month_end", 1, 3),
    "GOLDGUINEA": ContractSpec("GOLDGUINEA",    8,  8, 999, "Ahmedabad", "month_end", 1, 3),
    "GOLDPETAL":  ContractSpec("GOLDPETAL",     1,  1, 999, "Mumbai",    "month_end", 1, 3),
}

# Pairs the prototype analyses. The first is the control pair: same city, purity,
# expiry and tender schedule, so its normalized spread must converge to zero at DDR.
PAIRS = [
    ("GOLDTEN", "GOLDGUINEA"),   # control pair
    ("GOLDTEN", "GOLDPETAL"),    # adds Mumbai vs Ahmedabad basis
    ("GOLDM", "GOLDTEN"),        # stretch: GOLDM (5th of M+1) vs GOLDTEN (end of M), carry-adjusted
]

# Pre-set structural breaks used to split every backtest.
REGIME_BREAKS = {
    "2024-07-23": "Import duty cut 15% -> 6%",
    "2025-04-01": "GOLDTEN launches",
    "2025-09-22": "Six listed expiries per small contract",
    "2026-04-01": "SEBI: gold ETFs valued on exchange polled spot",
    "2026-05-13": "Import duty hike 6% -> 15%",
}
