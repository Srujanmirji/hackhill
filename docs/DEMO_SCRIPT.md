# Demo video script (≈ 2 minutes)

Record on **real MCX data**. Screen-record the dashboard at 1080p; one voice, calm pace.

| Time | On screen | Say |
|---|---|---|
| 0:00–0:15 | Title slide / team | "We're CodeWick. MCX lists gold in five sizes. Their prices never match — and traders keep asking whether that's free money. AuLens answers that honestly." |
| 0:15–0:35 | Contract rules in sidebar | "Most of the gap is in the rulebook: purity 995 vs 999, quote units, Ahmedabad vs Mumbai settlement, different expiries. We normalize everything to rupees per 10 grams at 999 using MCX's own formulas." |
| 0:35–1:00 | Spread chart, control pair (Sep 2026 expiry, the default) | "This is our control pair, GOLDTEN vs GOLDGUINEA. Same city, purity and expiry, so the spread must reach zero at final settlement — and on all 18 expiries it lands within one rupee. But look at the last week: the gap often widens before it snaps shut, and that snap happens after a trader must exit for the delivery window." |
| 1:00–1:25 | Verdict card + metrics | "We backtest walk-forward: signals use only past data, trades fill the next day, every position exits before the tender window. After every cost, the verdict for this pair is NO EDGE — 62 trades, net minus ₹17,100." |
| 1:25–1:45 | Slippage chart + regime table | "Bhavcopy can't see the order book, so we show how the result changes with slippage — this pair breaks even at under three rupees of slippage per 10 grams, about two ticks. And we split results around the April 2026 SEBI change and the May 2026 duty hike: none of our six pairs is profitable in every regime." |
| 1:45–2:00 | GitHub repo | "Everything is open source: repo link below. AuLens — five contracts, one metal, one honest verdict." |

**Rules:** don't show the synthetic-data banner. Don't claim profits the verdict card doesn't
show. If the verdict is NO EDGE, say it proudly — the track explicitly accepts it.
