# Limitations

AuLens is honest about what it cannot see. Show this list when asked "is this real money?"

1. **Settlement price is not a fill price.** Thin contracts (especially GOLDGUINEA) may not
   trade at the settlement price in size.
2. **Volume is not depth.** Bhavcopy has no order book. Slippage is assumed, and the
   break-even slippage is reported so users can judge.
3. **Short history.** GOLDTEN exists only from 1 Apr 2025, so TEN pairs have ~18 months.
4. **Regime breaks shrink samples further.** A split after 13 May 2026 leaves ~5 months.
5. **The Petal basis is estimated** from past spreads, not from polled Mumbai/Ahmedabad spot
   prices. Adding the MCX polled-spot series would replace the estimate.
6. **Contract specs are verified** against the current MCX PDFs (26 Oct 2026); MCX revises them, so re-check before relying on them.
7. **Margin and funding are not modelled.** Margin capital, opportunity cost and variation-margin
   financing are omitted, as is measured market impact beyond assumed slippage. Net P&L is
   net of configured model costs, not all possible costs; return on margin is not reported.
8. **Broker cut-offs vary.** We exit `tender_days + 2` trading days early; your broker may
   force exits earlier.
9. **Convergence happens only at the DDR, after we must exit.** On real data the control pair's
   spread is ±₹1 at the DDR on all 18 expiries, but in Aug 2025 and Oct 2025 – Feb 2026 it
   *widened* in the last week (GOLDGUINEA up to ~₹5,000/10 g rich in Jan 2026) before snapping
   back. GOLDTEN also sits ~0.4% below the coin contracts in calm months and up to ~2% below in
   the Dec 2025 – Mar 2026 rally. A strategy that must exit before tender cannot collect that
   snap-back.
10. **Crash days break cross-expiry pairs.** On 30 Jan 2026 GOLDM (Apr 2026) closed 17.5% lower
    while GOLDTEN (Mar 2026) closed 12% lower, moving the GOLDM–GOLDTEN spread by ~₹10,000 per
    10 g in a day. Three trades closed that day for a net −₹1.26 lakh, 74% of the pair's loss;
    its NO EDGE verdict and 0.25 gold beta are mostly that day. The same day supplies 57% of
    GOLDTEN vs GOLDPETAL's profit.
11. **Silver settlement prints can be far apart on thin days.** SILVERM vs SILVERMIC share an
    expiry and DDR and settle at exactly ₹0 on all 8 expired contracts. But on 30 Jan 2026 the
    Aug 2026 contracts closed ₹21,870/kg apart (SILVERM 989 lots, SILVERMIC 10,437), and on
    12 Feb 2026 ₹15,045/kg apart (SILVERM 60 lots). These are MCX's published closes, kept as-is.
    The volume filter and capacity cap limit what can trade on them, but such prints are not fills.
12. **SILVER100 is not included.** It has only four expiries in the window, and its DDR is quoted
    per 10 g rather than per kg, so it cannot support a walk-forward test yet.

13. **No final untouched holdout.** Monthly entry thresholds use earlier months, but the history
    has already been inspected during development. Other research choices are not independently
    validated by that procedure. Monthly replays close existing positions at the last observation of each expiry slice,
    omit final-observation entries and do not carry positions between months; see [VALIDATION.md](VALIDATION.md).
14. **Beta is diagnostic.** A low slope of net trade P&L against leg A's metal move is not proof
    of market neutrality or alpha. Small samples, overlapping trades and outliers matter; no
    beta confidence interval is reported. The trade bootstrap assumes independent trades.
15. **GOLDM averaging is incomplete.** The GOLDM vs GOLDTEN expected spread does not yet model
    GOLDM's three-day-average DDR adjustment.
16. **Execution uses the next available observation.** Missing sessions can delay a simulated
    fill beyond T+1. Filters use signal-day volume; fill-day capacity, partial fills and legging
    risk are not simulated.

## Not financial advice

AuLens is an analytical prototype built for Hack in Hills '26. It is not a recommendation to
trade.
