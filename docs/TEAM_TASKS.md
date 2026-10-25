# Team tasks

| | Srujan Mirji | Satvik Pandurangi | Aryan Budke |
|---|---|---|---|
| Role | Team Lead & Full-Stack | Frontend / UI | Data & Research |
| Owns | `aulens/data/`, `aulens/backtest.py`, deployment, integration | `app/`, screenshots, demo video edit | `aulens/specs.py`, `aulens/costs.py`, `docs/METHODOLOGY.md`, result checks |

## Day plan (adjust to the live deadline)

| Day | Srujan | Satvik | Aryan |
|---|---|---|---|
| 1 | Real MCX data into `data/raw/`, build parquet | Repo + README + deploy skeleton to Streamlit Cloud | Verify every value in `specs.py` against MCX PDFs |
| 2 | Run control pair on real data, fix bugs | Contract-calendar view, chart explanations | Verify cost rates against a broker charges page; update `COSTS.md` |
| 3 | Walk-forward sanity checks, regime split | Mobile layout, verdict card polish | Read the results: is the verdict defensible? Write LIMITATIONS |
| 4 | Integration, final deploy | Record + edit demo video | Q&A prep: "where's the edge?", "why not live data?" |

## Definition of done for any task

1. Runs from a clean clone with `pip install -r requirements.txt`.
2. `pytest -q` passes.
3. Anything that changes a number on screen is explained in `docs/METHODOLOGY.md`.
