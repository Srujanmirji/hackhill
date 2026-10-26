# Methodology

## 1. Normalization

Every price becomes **₹ per 10 g at 999 purity**:

```
px10 = close × (10 / quote_grams) × (999 / purity)
```

| Contract | Quote | Purity | Factor |
|---|---|---|---|
| GOLDM | ₹/10 g | 995 | × 999/995 |
| GOLDTEN | ₹/10 g | 999 | × 1 |
| GOLDGUINEA | ₹/8 g | 999 | × 10/8 |
| GOLDPETAL | ₹/1 g | 999 | × 10 |

The 999/995 factor is the same conversion MCX uses to set GOLDTEN/GUINEA/PETAL settlement
prices, so it is a rule, not an estimate. It accounts for a fixed ~0.40% gap (≈ ₹590 per
10 g at ₹1.46 lakh) that must never be reported as an opportunity.

**Expiry-day price = DDR.** On each contract's final day the Bhavcopy close is the last trade of a
thin tender-window session (often < 100 lots), not the settlement price. `build_dataset.py`
replaces it with MCX's published Due Date Rate (`data/raw/ddr/mcx_ddr.csv`) and keeps the original
in `bhav_close`. Check on real data: GOLDGUINEA DDR × 10/8 equals GOLDTEN DDR within ₹1 on all 18
expiries (Apr 2025 – Sep 2026), which confirms the normalization formula above.

## 2. Pairs and position sizing

Pairs are formed **only between contracts with the same expiry date**, so no artificial roll
jumps enter the spread. Lots are matched by grams so a pair is gold-neutral by construction:

| Pair | Lots | Grams |
|---|---|---|
| GOLDTEN vs GOLDGUINEA (control) | 4 vs 5 | 40 |
| GOLDTEN vs GOLDPETAL | 4 vs 40 (scaled) | 40 |
| GOLDM vs GOLDTEN (stretch) | 1 vs 10 | 100 |

Spread `S = px10_A − px10_B`.

## 3. Expected spread (the convergence target)

At expiry each contract settles on a polled spot price (its DDR). So:

- **Same city, purity and expiry (GOLDTEN vs GOLDGUINEA):** both settle on the same Ahmedabad
  999-converted spot → `E = 0`. This is the **control pair**.
- **Different city (GOLDTEN vs GOLDPETAL):** Petal settles on Mumbai spot → `E` = trailing
  median of the spread over past days only (an estimate of the Mumbai–Ahmedabad basis).
- **Different expiry (GOLDM vs GOLDTEN, stretch):** GOLDM expires on the 5th and GOLDTEN at
  month-end, so GOLDM month *M+1* is paired with GOLDTEN month *M* (gap 3–7 days). The 995→999
  purity gap is removed by normalization. `E = px10_TEN × (e^(c·gap/365) − 1)`, where `c` is the
  annual carry implied by the two nearest GOLDTEN expiries, as a 60-day trailing median shifted one
  day (past data only). On real data `c` ranges 4–21% a year (median ≈ 10%). Not modelled: GOLDM's
  DDR is a 3-day spot average, GOLDTEN's a single poll. Positions close `max(tender) + buffer`
  trading days before the GOLDTEN expiry, which is earlier than GOLDM's tender window.

Residual `R = S − E`. Only `R` can be an edge.

## 4. Signal

For each expiry, `z = (R − mean) / std` over the previous `lookback` days. The window is
shifted by one day so today's value is never used to score itself. A trade is opened when:

1. `|z| > z_entry`,
2. `|R|` is larger than the round-trip cost per 10 g **plus** 4 × assumed slippage per leg,
3. both legs traded at least `min_volume` lots that day, and our lots on each leg are at most
   `capacity_pct` (default 2%, 1–5% on the dashboard) of that leg's volume that day, and
4. the contract is not inside (tender days + buffer) of expiry.

Direction: `z > 0` → spread rich → sell A, buy B; `z < 0` → the reverse.

## 5. Execution and exits

- The decision on day *t* fills at day *t+1*'s settlement price (T+1). This removes the
  look-ahead of trading at the same price that produced the signal.
- Exit when `|z| < z_exit`, or on the last tradable day before the tender window.
- P&L = position × ΔS × grams / 10, minus costs, minus slippage.

## 6. Walk-forward

For each month *M* (after a minimum training period), `z_entry` is chosen from a small grid
by the net P&L it would have earned on **all months before M**, then applied to trades
entered in *M*. Results from all test months are concatenated. No parameter ever sees the
month it is tested on.

## 7. Verdict

| Verdict | Rule |
|---|---|
| **UNTESTABLE** | No trades, or fewer than 10 trades |
| **EDGE** | 90% bootstrap CI of mean trade P&L is above zero **and** net P&L is positive in every regime that has trades |
| **NO EDGE** | Anything else |

Also reported:
- **Break-even slippage** — the slippage per 10 g per leg at which net P&L reaches zero.
  This is the honest headline, because slippage is the cost we cannot measure from Bhavcopy.
- **Gold beta** — slope of trade P&L on the gold move over the holding period. Near zero
  means the result is not just gold going up.
- **Net Sharpe** — mean net trade / its standard deviation × √(trades per year). Trades are
  irregular, so this is a per-trade Sharpe scaled by how often the pair traded, not a daily one.
- **Carry panel** — annual carry implied by the two nearest GOLDTEN contracts, against the RBI
  repo rate in `specs.py`. Descriptive only; it does not feed the verdict.
- **Quiet alerts** — on the last data day, a pair alerts only if its verdict is EDGE *and* a
  contract passes every entry rule above. With no EDGE verdicts, the dashboard stays silent.
- **By regime** — results split at 23 Jul 2024, 1 Apr 2025, 22 Sep 2025, 1 Apr 2026 and
  13 May 2026 (see `aulens/specs.py`).

## 8. What would make us change our mind

- If the control pair's spread does not converge near expiry, normalization is wrong.
- If results flip sign across regimes, any "edge" is a regime artefact.
- If break-even slippage is below a realistic bid/ask spread, the edge is not tradable.
