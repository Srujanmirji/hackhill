# Finale Q&A

Short, honest answers backed by the real-data run (MCX, 1 Apr 2025 – 23 Oct 2026, default
assumptions: ₹20 slippage per display unit per leg (gold /10 g, silver /kg), 50-lot minimum volume). Every number here comes from
`python scripts/run_backtest.py` or `tests/test_real_data.py`; re-check them if the data changes.

## "Where's the edge?"

This test does not establish an edge after modelled costs. It is not proof that no opportunity can exist.

- **The gap is real.** GOLDGUINEA trades about 0.4% above GOLDTEN in calm months and up to ~2.7%
  above it in the Dec 2025 – Mar 2026 rally, even though both settle on the same price.
- **It closes only at final settlement.** On all 18 expiries the control-pair spread lands within
  ₹1 at the DDR, but in six of them the gap over the last five trading days was *wider* than in
  the first half of the contract's life. A trader has to be out before the delivery window, so
  the snap-back can't be collected.
- **Costs eat what's left.** Control pair: average gross ₹337 per trade against ₹609 of costs and
  slippage per trade. 62 trades, net −₹16,883, net Sharpe −0.37; it breaks even at only ₹3.0 of
  slippage per 10 g per leg.
- **The one positive pair fails the robustness test.** GOLDTEN vs GOLDPETAL nets ₹35,653, but almost
  all of it comes from one regime (22 Sep 2025 – 1 Apr 2026), 57% from a single trade closed on
  30 Jan 2026, and it loses after the May 2026 duty hike. Its 90% confidence interval for the
  average trade is −₹527 to ₹2,044: it straddles zero.
- **Same story in silver.** SILVERM vs SILVERMIC settle at exactly ₹0 on all 8 expiries, yet
  15 trades net −₹2,783 and break even at ₹10.7 per kg per leg. SILVER vs SILVERM loses
  ₹3.42 lakh, and its whole 90% interval sits below zero. All six pairs: NO EDGE.

One line: *"The spread is real; the trade isn't. That's the answer a trader needs before risking money."*

## "Why not live data?"

- Bhavcopy is the exchange's official, free, public end-of-day record, the source the track names.
  Final-day prices come from MCX's published Due Date Rates, not from thin last trades.
- Live bid/ask needs a broker API and weeks of capture to measure real slippage. Instead we show
  **break-even slippage**, the slippage at which the strategy stops making money, so anyone can
  compare it to the spreads they see on their own screen. For the control pair it is ₹3.0 per 10 g
  per leg, about two GOLDGUINEA ticks: almost any real fill erases it.
- Executable-price data is needed to validate fill assumptions. Within the current simulation,
  lowering slippage alone cannot rescue negative pre-slippage P&L; different executable
  prices could change the measured result.

## "How is this different from other teams?"

- **It is built to say no.** Verdicts are EDGE, NO EDGE or UNTESTABLE, and EDGE needs a 90%
  confidence interval above zero *and* profit in every regime.
- **It checks itself.** The control pair (same city, purity and expiry) must converge, and a test
  enforces it against MCX's own settlement prices. That check found the real data problem: the
  expiry-day Bhavcopy close is a thin last trade, which left the control-pair spread up to ₹3,560
  per 10 g away from where it actually settled.
- **Auditable monthly selection.** Signals use day *t* data and simulated fills use the next
  available observation. Entry thresholds are selected on earlier months; the app exports
  actual training/test boundaries and thresholds. Tests cover shifted z-scores/carry and
  threshold stability under later-price shocks. No final untouched holdout is claimed.
- **The rulebook is in the maths.** Purity (995 vs 999), quote units, settlement city and expiry
  rules are normalized with MCX's own formulas before anything is compared.

## Likely follow-ups

**"Could a bigger trader do better?"**
We cannot establish that from Bhavcopy. The default cap is 2% of each leg's signal-day
volume (adjustable 1–5%). That is a capacity assumption, not evidence of fill-day depth or
executable size. Larger trades may face additional market impact, which is not measured.

**"Why is GUINEA richer than TEN if they settle on the same price?"**
We measure it; we don't claim to know the cause. A plausible reading is retail demand for
small-ticket contracts during rallies. It matters less than the fact that it is not collectable
before the delivery window.

**"Why not hold to expiry and collect the convergence?"**
Holding into the tender window means taking or making physical delivery, with delivery and making
charges and broker cut-offs. AuLens models what a trader without a vault can do: exit
`tender days + 2` trading days early.

**"Is 62 trades enough?"**
The control pair's 90% trade-bootstrap interval is −₹1,305 to ₹845, so it does not establish
a positive average net trade. That is a NO EDGE classification under the model, not proof
that the true edge is absent. The bootstrap treats trades as independent despite possible overlap.

**"What is gold beta?"**
The slope of net trade P&L against leg A's gram-scaled rupee metal move over the same holding
period. Near zero (0.07 for the gold control) is a diagnostic, not proof of market neutrality
or alpha. Samples are small, trades can overlap and outliers matter; no beta interval or
significance test is reported. GOLDM vs GOLDTEN is 0.25, heavily affected by 30 Jan 2026.

**"What would change your mind?"**
A pair whose confidence interval sits above zero and that makes money in every regime, at a
break-even slippage above the real bid/ask. AuLens runs that test the moment new data is loaded.

**"Are the contract specs right?"**
Yes, checked field by field against the current MCX spec PDFs (log in `docs/CONTRACT_SPECS.md`).
The check caught one error, GOLD/GOLDM's tender window was 3 days, not 5, and we fixed it. The
normalization is also confirmed by MCX's own settlement prices: GUINEA × 10/8 equals TEN within
₹1 on all 18 expiries.


## "Is this an untouched out-of-sample test?"

Only the monthly threshold selection uses strictly earlier months. We have inspected the
history during development, so we do not claim a final untouched holdout for the whole
research process. Each replay closes existing positions at its expiry slice's last observation and omits
entries filled on that final observation, rather than carrying a continuous portfolio. The app's validation table makes the date boundaries visible.

## "Are those actual fills, and are all costs included?"

No. Fills are next-available settlement observations with assumed slippage. Daily volume is
not order-book depth. Reported P&L deducts configured fees, taxes, brokerage and slippage;
it excludes margin/funding costs and measured market impact. Delivery/storage costs are
excluded because the model exits before tender. GOLDM averaging remains incomplete.
See [VALIDATION.md](VALIDATION.md) for the full boundary of the claims.
