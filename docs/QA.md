# Finale Q&A

Short, honest answers backed by the real-data run (MCX, 1 Apr 2025 – 23 Oct 2026, default
assumptions: ₹20 slippage per 10 g per leg, 50-lot minimum volume). Every number here comes from
`python scripts/run_backtest.py` or `tests/test_real_data.py`; re-check them if the data changes.

## "Where's the edge?"

There isn't one after costs, and AuLens can show exactly why.

- **The gap is real.** GOLDGUINEA trades about 0.4% above GOLDTEN in calm months and up to ~2.7%
  above it in the Dec 2025 – Mar 2026 rally, even though both settle on the same price.
- **It closes only at final settlement.** On all 18 expiries the control-pair spread lands within
  ₹1 at the DDR, but in six of them the gap over the last five trading days was *wider* than in
  the first half of the contract's life. A trader has to be out before the delivery window, so
  the snap-back can't be collected.
- **Costs eat what's left.** Control pair: average gross ₹191 per trade against ₹612 of costs and
  slippage per trade. 61 trades, net −₹25,726, and it loses even at zero slippage.
- **The one positive pair fails the robustness test.** GOLDTEN vs GOLDPETAL nets ₹34,450, but almost
  all of it comes from one regime (22 Sep 2025 – 1 Apr 2026) and it loses after the May 2026 duty
  hike. Its 90% confidence interval for the average trade is −₹514 to ₹2,077: it straddles zero.

One line: *"The spread is real; the trade isn't. That's the answer a trader needs before risking money."*

## "Why not live data?"

- Bhavcopy is the exchange's official, free, public end-of-day record, the source the track names.
  Final-day prices come from MCX's published Due Date Rates, not from thin last trades.
- Live bid/ask needs a broker API and weeks of capture to measure real slippage. Instead we show
  **break-even slippage**, the slippage at which the strategy stops making money, so anyone can
  compare it to the spreads they see on their own screen. For the control pair it is negative: no
  fill quality saves it.
- Live data is the natural next step, not a missing piece. It would refine the slippage number; it
  cannot rescue a strategy that loses before slippage.

## "How is this different from other teams?"

- **It is built to say no.** Verdicts are EDGE, NO EDGE or UNTESTABLE, and EDGE needs a 90%
  confidence interval above zero *and* profit in every regime.
- **It checks itself.** The control pair (same city, purity and expiry) must converge, and a test
  enforces it against MCX's own settlement prices. That check found the real data problem: the
  expiry-day Bhavcopy close is a thin last trade, which left the control-pair spread up to ₹3,560
  per 10 g away from where it actually settled.
- **No look-ahead.** Signals use data up to day *t*, fills happen at *t+1*, parameters are chosen
  walk-forward on earlier months only, and every position exits before the tender window. Tests
  cover the z-score and the carry estimate.
- **The rulebook is in the maths.** Purity (995 vs 999), quote units, settlement city and expiry
  rules are normalized with MCX's own formulas before anything is compared.

## Likely follow-ups

**"Why is GUINEA richer than TEN if they settle on the same price?"**
We measure it; we don't claim to know the cause. A plausible reading is retail demand for
small-ticket contracts during rallies. It matters less than the fact that it is not collectable
before the delivery window.

**"Why not hold to expiry and collect the convergence?"**
Holding into the tender window means taking or making physical delivery, with delivery and making
charges and broker cut-offs. AuLens models what a trader without a vault can do: exit
`tender days + 2` trading days early.

**"Is 61 trades enough?"**
Enough to say NO EDGE with confidence for the control pair: its 90% interval for the average trade
is −₹1,484 to ₹715. It is not enough to claim an edge, which is why the bar for EDGE is high.

**"What is gold beta?"**
The slope of trade P&L against the gold price move over the same holding period. Near zero (0.06
for the control pair) means results are not just a bet on gold going up. GOLDM vs GOLDTEN is 0.25,
driven mostly by the 30 Jan 2026 crash day.

**"What would change your mind?"**
A pair whose confidence interval sits above zero and that makes money in every regime, at a
break-even slippage above the real bid/ask. AuLens runs that test the moment new data is loaded.

**"Are the contract specs right?"**
They follow MCX/TRD/456/2025, and the normalization is confirmed by MCX's own settlement prices
(GUINEA × 10/8 equals TEN within ₹1 on all 18 expiries). Checking each field against the July 2026
spec PDFs is still open (`docs/CONTRACT_SPECS.md`).
