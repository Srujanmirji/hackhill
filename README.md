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

![AuLens dashboard (synthetic data)](docs/dashboard.png)

## Quick start

```bash
git clone <repo-url> aulens && cd aulens
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. Build a dataset
python scripts/build_dataset.py --sample                # synthetic, to develop the UI
python scripts/build_dataset.py --raw data/raw          # real MCX downloads (see docs/DATA.md)

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
| Pair | `aulens/normalize.py` | Gram-matched lots (e.g. 4 GOLDTEN vs 5 GOLDGUINEA = 40 g), same expiry only |
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
| [docs/CONTRACT_SPECS.md](docs/CONTRACT_SPECS.md) | The rulebook, with what still needs verifying |
| [docs/COSTS.md](docs/COSTS.md) | Transaction-cost model and worked examples |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | What AuLens cannot tell you |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 2-minute demo video script |
| [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md) | Before every round |

## Status

- [x] Contract rulebook, normalizer, gram matching
- [x] Cost engine (configurable)
- [x] Walk-forward backtest with T+1 fills, tender exits, volume filter
- [x] Verdicts with bootstrap CI, regime split and gold beta
- [x] Streamlit dashboard, tests, synthetic data generator
- [ ] **Real MCX history loaded** ← the most important open item
- [ ] Contract specs verified against July 2026 MCX PDFs
- [ ] GOLDM vs GOLDTEN pair (needs carry adjustment for the 5th vs month-end expiry gap)
- [ ] Carry decomposition panel, measured slippage from live bid/ask

## License

MIT
