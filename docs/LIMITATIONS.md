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
7. **Margin and funding are not modelled.** The two legs block margin; that cost is ignored.
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
    10 g in a day. Four trades closed that day for a net −₹1.56 lakh, 75% of the pair's loss;
    its NO EDGE verdict and 0.32 gold beta are mostly that day.

## Not financial advice

AuLens is an analytical prototype built for Hack in Hills '26. It is not a recommendation to
trade.
