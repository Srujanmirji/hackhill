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
6. **Contract specs are not yet verified** against the July 2026 MCX PDFs.
7. **Margin and funding are not modelled.** The two legs block margin; that cost is ignored.
8. **Broker cut-offs vary.** We exit `tender_days + 2` trading days early; your broker may
   force exits earlier.

## Not financial advice

AuLens is an analytical prototype built for Hack in Hills '26. It is not a recommendation to
trade.
