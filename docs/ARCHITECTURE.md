# Architecture

```
            ┌───────────────────────── data/raw/ ─────────────────────────┐
 MCX site ──┤ manual CSV/XLSX  ·  JSON endpoint (DevTools)  ·  TinyFish/Playwright │
            └──────────────────────────────┬───────────────────────────────┘
                                           │ scripts/build_dataset.py
                                           ▼
                        aulens/data/loader.py  (tidy + validate)
                    strip symbols · MM/DD/YYYY · 04SEP2026 · gold futures only
                                           │
                                           ▼
                        data/processed/gold_futures.parquet
                       one row per (date, symbol, expiry)
                                           │
              ┌────────────────────────────┼─────────────────────────────┐
              ▼                            ▼                             ▼
     aulens/normalize.py          aulens/backtest.py             aulens/costs.py
     ₹/10 g @ 999                 expected spread E              CTT, MCX, SEBI,
     gram-matched lots            residual R = S − E             stamp, GST, brokerage
     same-expiry pairs            z (past data only)
                                  walk-forward z_entry
                                  T+1 fills, tender exits
              └────────────────────────────┬─────────────────────────────┘
                                           ▼
                                aulens/verdict.py
                 net P&L · bootstrap CI · by regime · gold beta · break-even slippage
                                           │
                     ┌─────────────────────┴─────────────────────┐
                     ▼                                           ▼
          scripts/run_backtest.py                     app/streamlit_app.py
               (terminal)                               (dashboard)
```

## Repository layout

```
aulens/
  specs.py            contract rulebook, pairs, regime break dates
  normalize.py        ₹/10 g @ 999, gram matching, same-expiry pair panel
  costs.py            CostModel (configurable)
  backtest.py         signals + walk-forward
  verdict.py          EDGE / NO EDGE / UNTESTABLE
  data/
    loader.py         raw Bhavcopy → tidy table, date validation
    mcx_client.py     fetch via JSON endpoint, with caching
    sample.py         SYNTHETIC generator (development only)
app/streamlit_app.py  dashboard
scripts/              build_dataset.py, run_backtest.py
tests/                normalization, costs, look-ahead, tender exits
docs/                 this documentation
```

## Design decisions

| Decision | Why |
|---|---|
| End-of-day Bhavcopy, not live ticks | It is the official, free, public source the track names. Live bid/ask is a stretch goal. |
| Parquet file, not a database | One file, versionable, fast with pandas. Move to Postgres only if alerts need it. |
| Streamlit, not Next.js | One language, ships in hours. Next.js is a post-hackathon rebuild. |
| Rules in one `specs.py` | A single place to verify against MCX PDFs; tests read from it. |
| Walk-forward chooses `z_entry` | Prevents tuning on the future. |
| Verdict can be UNTESTABLE | Small samples must not be reported as edges. |

## Tech stack

Python 3.11+ · pandas · NumPy · PyArrow · Plotly · Streamlit · pytest · requests ·
Playwright/TinyFish (scraping fallback) · GitHub Actions (optional daily update) ·
Streamlit Community Cloud (hosting).
