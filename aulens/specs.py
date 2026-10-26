"""Contract rulebook for MCX gold and silver futures.

Every number here should be checked against the latest MCX contract-specification
PDFs before a pitch (see docs/CONTRACT_SPECS.md). Verified 26 Oct 2026 against the current
MCX spec PDFs (MCX/TRD/040-044/2026); GOLD/GOLDM tender window corrected from 5 to 3 days.
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
    "GOLD":       ContractSpec("GOLD",       1000, 10, 995, "Ahmedabad", "5th",       3, 3),
    "GOLDM":      ContractSpec("GOLDM",       100, 10, 995, "Ahmedabad", "5th",       3, 3),
    "GOLDTEN":    ContractSpec("GOLDTEN",      10, 10, 999, "Ahmedabad", "month_end", 1, 3),
    "GOLDGUINEA": ContractSpec("GOLDGUINEA",    8,  8, 999, "Ahmedabad", "month_end", 1, 3),
    "GOLDPETAL":  ContractSpec("GOLDPETAL",     1,  1, 999, "Mumbai",    "month_end", 1, 3),
    # Silver: MCX spec PDFs (Silver Sep-2026/Mar-2027, Silver Mini and Micro Aug-2026/Feb-2027 onwards), read 26 Oct 2026.
    # Quoted per kg; DDR = simple average of the last 3 polled Ahmedabad spot prices; tender = last 3 trading days.
    "SILVER":     ContractSpec("SILVER",    30000, 1000, 999, "Ahmedabad", "5th",       3, 3),
    "SILVERM":    ContractSpec("SILVERM",    5000, 1000, 999, "Ahmedabad", "month_end", 3, 3),
    "SILVERMIC":  ContractSpec("SILVERMIC",  1000, 1000, 999, "Ahmedabad", "month_end", 3, 3),
}


def metal(symbol: str) -> str:
    return "silver" if symbol.startswith("SILVER") else "gold"


# Display unit per metal (internally every price is ₹ per 10 g at 999): factor to multiply by, and its name.
UNITS = {"gold": (1, "10 g"), "silver": (100, "kg")}
# Default slippage per leg per display unit. ASSUMPTION: ₹20 is ~0.014% of price for both metals at 2026 levels.
DEFAULT_SLIPPAGE = {"gold": 20, "silver": 20}

# Pairs the prototype analyses. The first is the control pair: same city, purity,
# expiry and tender schedule, so its normalized spread must converge to zero at DDR.
PAIRS = [
    ("GOLDTEN", "GOLDGUINEA"),   # control pair
    ("GOLD", "GOLDM"),           # second control: same purity, city, 3-day DDR and expiry; settles on one DDR
    ("GOLDTEN", "GOLDPETAL"),    # adds Mumbai vs Ahmedabad basis
    ("GOLDM", "GOLDTEN"),        # stretch: GOLDM (5th of M+1) vs GOLDTEN (end of M), carry-adjusted
    ("SILVERM", "SILVERMIC"),    # silver control: same purity, city, 3-day DDR and expiry
    ("SILVER", "SILVERM"),       # silver carry pair: SILVER (5th of M+1) vs SILVERM (end of M)
]

# RBI policy repo rate, the benchmark for the carry panel. 5.50% per rbi.org.in, read 26 Oct 2026
# (raised from 5.25% on 7 Oct 2026). Only the current rate is verified; earlier changes are not plotted.
RBI_REPO_RATE = 0.055
RBI_REPO_SINCE = "2026-10-07"

# Full-day MCX closures (morning AND evening closed), from mcxindia.com "Trading Holidays",
# read 26 Oct 2026. Morning-only closures still trade in the evening and are not listed.
# TODO: add 2027 once MCX publishes it.
MCX_FULL_HOLIDAYS = ["2026-01-26", "2026-04-03", "2026-10-02", "2026-12-25"]

# Pre-set structural breaks used to split every backtest.
REGIME_BREAKS = {
    "2024-07-23": "Import duty cut 15% -> 6%",
    "2025-04-01": "GOLDTEN launches",
    "2025-09-22": "Six listed expiries per small contract",
    "2026-04-01": "SEBI: gold ETFs valued on exchange polled spot",
    "2026-05-13": "Import duty hike 6% -> 15%",
}
