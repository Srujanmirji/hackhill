# Validation evidence and model limits

## What has been tested

AuLens performs monthly, expanding-window walk-forward selection of `z_entry` from
`Params.z_grid` (default 1.5, 2.0, 2.5). The first three observed pair months train the
first default test month. Each later month selects its threshold using earlier months
only. Other model choices and dashboard assumptions are fixed for a run; they are not
independently validated by this selection step.

The app's monthly evidence table records the actual first/last observed pair dates in
training and testing, distinct trading-date counts, and selected threshold. Months with
no trades are still included. These dates describe available pair rows, not proof of a
complete exchange calendar. Missing sessions can make a next-observation fill later than
the next exchange session.

Each replay stops at the test month's last available observation. Existing positions are
forced closed at the last available observation of their expiry slice if no earlier exit
occurs. An entry filled on that final observation is not recorded as a completed trade.
This terminal-entry omission is a known simulation limitation; these disclosures do not
change it. Only completed trades entered in that month are retained. Positions are not
carried between monthly replays. An incomplete latest month is tested only through its
last observed date.

**No final untouched holdout is claimed.** The available history has already been
inspected during development. Monthly thresholds use earlier data, but the concatenated
results do not establish that the overall research process was free of hindsight or
multiple testing. Reserve new, uninspected dates after freezing the model before making
that stronger claim.

## Bundled MCX validation snapshot

For the bundled MCX data from 1 Apr 2025 to 23 Oct 2026, all six default pair runs have
16 monthly test windows, from 1 Jul 2025 to 23 Oct 2026. The first training window is
1 Apr–30 Jun 2025; later training windows expand. October 2026 is incomplete. The full
dataset range is therefore longer than the test-date range. Default assumptions are
50-lot minimum signal-day volume, 2% capacity cap, ₹20 slippage per display unit per leg,
and size multiplier 4 for GOLDTEN/GOLDPETAL, 1 otherwise. This is a dated snapshot, not a
claim that new data has been held out. The current-run CSV supplies the actual boundaries.

## Execution is simulated

Signals use day t observations; each leg's next available settlement observation is the
simulated entry/exit price, with assumed slippage charged on all four leg crossings.
These are not recorded executions. Official settlement values do not guarantee fills,
simultaneous execution, or available size. Volume and capacity filters use the signal
day's daily volume; next-day depth, fill-day capacity, partial fills and legging risk are
not simulated. Calendar checks describe the model's tender/exit rules, not broker guarantees.

## Included and excluded costs

Reported net P&L deducts the configured CTT, exchange and SEBI fees, stamp duty, GST,
brokerage and assumed slippage. It is **net of modelled costs**, not all possible costs.
The model omits margin capital and funding/opportunity costs, variation-margin cash-flow
financing, measured market impact and bid/ask execution costs beyond assumed slippage.
Delivery/storage costs are excluded because the strategy intends to exit before tender.
There is no margin-based return-on-capital calculation. The GOLDM vs GOLDTEN expected
spread also omits the GOLDM three-day-average DDR adjustment.

## Beta and statistical limits

Metal beta is a simple regression slope of each trade's net rupee P&L against leg A's
same-holding-period, gram-scaled rupee metal move. It is a diagnostic, not risk-adjusted
alpha or proof of market neutrality. Small samples, overlapping trades, differing holding
periods and outliers can affect it; no beta confidence interval or significance test is
reported. Matching grams does not remove cross-expiry, settlement-basis or nonlinear risk.

The 90% bootstrap interval resamples individual trades independently. It does not account
for dependence between overlapping trades, multiple comparisons or research selection.
Regime checks cover only regimes with trades. NO EDGE means this test has not established
an edge under its assumptions; it is not proof that no opportunity can ever exist.

## Reproduce and inspect

Run `python scripts/run_backtest.py` for all six verdicts and `pytest -q` for automated
checks. In the dashboard, select a pair and expand **Validation evidence and model limits**;
download **Monthly validation evidence (.csv)** and the verdict report. Both include the
monthly boundaries for the current run. Inspect the trade-log CSV for contract expiry,
entry/exit dates and the modelled costs deducted.

Tests cover training ending before its test window, threshold choices remaining unchanged
when later prices are shocked, shifted z-score/carry inputs, and next-observation settlement
P&L arithmetic. These are targeted checks, not a comprehensive independent execution audit.
