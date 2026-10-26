# AuLens

**Is this MCX gold spread real — and is it tradable after costs?**

AuLens is an *edge validator* for India's MCX gold futures. MCX lists the same metal in five
contract sizes (GOLD, GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL). Their prices never line up
exactly, and most of the gap is written into the contract rules: purity (995 vs 999),
quotation unit, settlement city (Ahmedabad vs Mumbai), expiry date and tender window.

AuLens removes everything the rulebook explains, tests whether the residual survives real
costs, walk-forward and across 2024–26 regime breaks, and returns one honest verdict per pair:
**EDGE**, **NO EDGE** or **UNTESTABLE**.

Team **CodeWick** · Hack in Hills '26 · Track 03: Commodity Derivatives Intelligence

**Live demo:** <https://hackhill-wikhjmugah4iqupyf4nlh4.streamlit.app/> · real MCX data, 1 Apr 2025 – 23 Oct 2026

![AuLens dashboard on real MCX data, 1 Apr 2025 – 23 Oct 2026](docs/dashboard.png)

## Quick start

```bash
git clone <repo-url> aulens && cd aulens
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. Build a dataset
python scripts/build_dataset.py --sample                # synthetic, to develop the UI
python scripts/build_dataset.py --raw data/raw          # real MCX data; refresh it with scripts/mcx_fetch_in_browser.js

# 2. Verdicts in the terminal
python scripts/run_backtest.py

# 3. Dashboard
streamlit run app/streamlit_app.py

# 4. Tests
pytest -q
```

## What it does

| Step | Module | What happens |
|---|---|---|
| Normalize | `aulens/normalize.py` | Every contract → ₹ per 10 g at 999 purity using MCX's own formulas |
| Pair | `aulens/normalize.py` | Gram-matched lots (e.g. 4 GOLDTEN vs 5 GOLDGUINEA = 40 g), same expiry only (GOLDM month M+1 vs GOLDTEN month M) |
| Expect | `aulens/backtest.py` | Convergence target from settlement rules (0 for the control pair) |
| Validate | `aulens/backtest.py` | Walk-forward, T+1 fills, exits before tender, volume filter |
| Cost | `aulens/costs.py` | CTT, MCX fee, SEBI fee, stamp duty, GST, brokerage, slippage |
| Decide | `aulens/verdict.py` | Net P&L, bootstrap CI, results by regime, gold beta → verdict |

## Documentation

| Doc | For |
|---|---|
| [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) | Step-by-step: how to build and finish the prototype |
| [docs/TEAM_TASKS.md](docs/TEAM_TASKS.md) | Who does what, day by day |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and data flow |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | The maths: normalization, convergence, walk-forward, verdicts |
| [docs/DATA.md](docs/DATA.md) | Getting real MCX data, and its quirks |
| [docs/MCX_DATA_API.md](docs/MCX_DATA_API.md) | MCX endpoints, reconstructed from the site's own scripts |
| [docs/CONTRACT_SPECS.md](docs/CONTRACT_SPECS.md) | The rulebook, with what still needs verifying |
| [docs/COSTS.md](docs/COSTS.md) | Transaction-cost model and worked examples |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | What AuLens cannot tell you |
| [docs/QA.md](docs/QA.md) | Finale Q&A: honest answers backed by the real-data numbers |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 2-minute demo video script |
| [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md) | Before every round |

## Results (real MCX data, 1 Apr 2025 – 23 Oct 2026)

**No pair shows an edge after costs.** Default assumptions: ₹20 slippage per 10 g per leg,
50-lot minimum volume, each leg capped at 2% of its daily volume, walk-forward `z_entry`.

| Pair | Verdict | Trades | Net P&L | Net Sharpe | 90% CI, mean trade | Break-even slippage (₹/10 g/leg) | Gold beta |
|---|---|---|---|---|---|---|---|
| GOLDTEN vs GOLDGUINEA (control) | **NO EDGE** | 62 | −₹17,140 | −0.38 | −₹1,309 to ₹838 | ₹2.7 | 0.07 |
| GOLDTEN vs GOLDPETAL | **NO EDGE** | 49 | ₹35,653 | 0.83 | −₹527 to ₹2,044 | ₹65.5 | 0.14 |
| GOLDM vs GOLDTEN (stretch) | **NO EDGE** | 32 | −₹1,69,597 | −1.24 | −₹12,236 to ₹404 | −₹112.5 | 0.25 |

- **Control pair:** breaks even at only ₹2.7 of slippage per 10 g per leg, about two GOLDGUINEA
  ticks, so any real fill cost turns it negative. Its spread is ±₹1
  at the final settlement price on all 18 expiries, which validates the normalization, but it
  converges only after the tender-window exit.
- **GOLDTEN vs GOLDPETAL:** net positive, but the profit comes from one regime (22 Sep 2025 –
  1 Apr 2026), 57% of it from a single trade closed on 30 Jan 2026, and it loses after 13 May
  2026, so it fails the every-regime test.
- **GOLDM vs GOLDTEN:** most of the loss is one crash day (30 Jan 2026), when the two expiries
  fell 17.5% and 12%. See [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

Exact output of `python scripts/run_backtest.py`:

```
Data source: MCX

== GOLDTEN vs GOLDGUINEA  [NO EDGE]  4 x GOLDTEN  vs  5 x GOLDGUINEA  (40 g)
   Does not survive costs, slippage and regime splits with confidence.
   trades 62  gross ₹20,618  costs ₹17,918  slippage ₹19,840  net ₹-17,140  hit 42%
   break-even slippage ₹2.7/10 g/leg   gold beta 0.070
   net Sharpe -0.38   90% CI of mean trade ₹-1,309 to ₹838
                  count           sum
regime                               
From 01 Apr 2025      4   -343.373494
From 22 Sep 2025     30 -10825.918032
From 01 Apr 2026      2  -1932.232955
From 13 May 2026     26  -4038.245302 

== GOLDTEN vs GOLDPETAL  [NO EDGE]  4 x GOLDTEN  vs  40 x GOLDPETAL  (40 g)
   Does not survive costs, slippage and regime splits with confidence.
   trades 49  gross ₹65,556  costs ₹14,223  slippage ₹15,680  net ₹35,653  hit 41%
   break-even slippage ₹65.5/10 g/leg   gold beta 0.135
   net Sharpe 0.83   90% CI of mean trade ₹-527 to ₹2,044
                  count           sum
regime                               
From 01 Apr 2025      4   2671.647840
From 22 Sep 2025     27  33195.824266
From 01 Apr 2026      3    247.194325
From 13 May 2026     15   -462.137796 

== GOLDM vs GOLDTEN  [NO EDGE]  1 x GOLDM  vs  10 x GOLDTEN  (100 g)
   Does not survive costs, slippage and regime splits with confidence.
   trades 32  gross ₹-125,825  costs ₹18,172  slippage ₹25,600  net ₹-169,597  hit 34%
   break-even slippage ₹-112.5/10 g/leg   gold beta 0.249
   net Sharpe -1.24   90% CI of mean trade ₹-12,236 to ₹404
                  count            sum
regime                                
From 01 Apr 2025      5   -2119.383105
From 22 Sep 2025     18 -151123.302862
From 01 Apr 2026      2   -6371.217480
From 13 May 2026      7   -9983.303016
```

## Status

- [x] Contract rulebook, normalizer, gram matching
- [x] Cost engine (configurable)
- [x] Walk-forward backtest with T+1 fills, tender exits, volume filter
- [x] Verdicts with bootstrap CI, regime split and gold beta
- [x] Streamlit dashboard, tests, synthetic data generator
- [x] Real MCX history loaded (402 trading days, 10,768 contract-days; see [docs/DATA.md](docs/DATA.md))
- [x] Expiry-day closes replaced by MCX's published final settlement prices (DDR)
- [x] Control-pair convergence verified on real data (`tests/test_real_data.py`)
- [x] Contract calendar, chart captions, cached sensitivity (page loads in < 5 s)
- [x] GOLDM vs GOLDTEN pair, carry-adjusted for the 5th vs month-end expiry gap
- [x] Liquidity capacity caps (1–5% of each leg's daily volume), net Sharpe, confidence interval on the verdict
- [x] Carry panel (GOLDTEN curve vs RBI repo) and quiet alerts (only for EDGE pairs that clear the hurdle)
- [x] Contract specs verified against the current MCX PDFs (GOLD/GOLDM tender window corrected to 3 days)
- [ ] GOLDM 3-day-average DDR modelled in the GOLDM vs GOLDTEN expected spread
- [ ] COMEX carry comparison, measured slippage from live bid/ask

## License

MIT
