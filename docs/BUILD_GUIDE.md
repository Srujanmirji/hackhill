# Build guide: from this repo to a demo-ready prototype

This is the order to build in. Each phase ends with something you can show. Don't start a
phase until the one before it works on **real** data.

## Phase 0 — Set up (30 min, everyone)

1. Create the GitHub repo (public), push this code, add all three teammates as collaborators.
2. Everyone runs the Quick start in the README and sees the dashboard on synthetic data.
3. Agree the branch rule: `main` always runs. Work on `feature/<name>` branches, merge by PR.

**Done when:** all three laptops show the dashboard and `pytest -q` passes.

## Phase 1 — Real data (the critical path)

Nothing else matters until real MCX prices are in `data/processed/gold_futures.parquet`.

1. **Fastest route — manual download.** Open
   <https://www.mcxindia.com/market-data/historical-data>, choose Futures → GOLDTEN, GOLDGUINEA,
   GOLDPETAL (and GOLDM), Date-wise, 1 Apr 2025 → today. MCX allows **365 days per query**,
   so download in two chunks. Save every file into `data/raw/`.
2. Run `python scripts/build_dataset.py --raw data/raw`.
3. If the column names differ from what `aulens/data/loader.py` expects, add them to `COLMAP`.
   Do not rename columns by hand in Excel.
4. **Automated route (for daily updates).** In Chrome open the Bhavcopy page → DevTools →
   Network → pick a date → copy the request URL. Replace the date with `{date}` and run
   `python scripts/build_dataset.py --endpoint "<url>" --start 2025-04-01`.
   If MCX's bot protection blocks it, use TinyFish (the hackathon sponsor) or Playwright to
   drive a real browser and save the JSON into `data/raw/json/`.

**Checks before moving on** (write them down in `docs/DATA.md`):
- Row counts per symbol per month look sane; no month missing.
- Spot-check 3 closes against the MCX website by hand.
- The returned date always equals the requested date (holidays are dropped, not duplicated).

**Done when:** `run_backtest.py` prints `Data source: MCX`.

## Phase 2 — Verify the rulebook (half a day, Aryan)

Download the latest MCX contract-specification PDFs for each gold contract and check every
value in `aulens/specs.py`: unit, quote unit, purity, DDR city, DDR averaging, tender days.
Record the PDF name and page in `docs/CONTRACT_SPECS.md`. If anything differs, fix `specs.py`
and re-run the tests.

## Phase 3 — Make the core analysis credible

1. **Control pair first.** Run GOLDTEN vs GOLDGUINEA on real data. Its normalized spread
   must shrink toward zero near expiry. If it doesn't, there is a normalization bug — fix it
   before anything else.
2. Look at the spread chart for 5–6 expiries. Note anything odd (tender-week jumps, zero-volume
   days) in `docs/LIMITATIONS.md`.
3. Tune only these, and only on the **training** part of the walk-forward:
   `lookback`, `z_grid`, `min_volume`. Never tune on the full history.
4. Run the slippage sensitivity. The break-even slippage is your headline number.

## Phase 4 — Polish the dashboard (Satvik)

- Verdict card at the top, spread chart, sensitivity chart, regime table — already there.
- Add: a one-line plain-English explanation under each chart.
- Add: a "Contract calendar" view (listing date, tender window, expiry) per pair.
- Remove the synthetic-data banner only when the data really is MCX.
- Deploy to Streamlit Community Cloud (free): connect the GitHub repo, set the main file to
  `app/streamlit_app.py`, commit the processed parquet (or a small sample of it) so the hosted
  app has data.

## Phase 5 — Demo and submission

Follow `docs/DEMO_SCRIPT.md` and `docs/SUBMISSION_CHECKLIST.md`. Record the demo on real data.

## Stretch goals (only after phases 1–5)

| Feature | Why | Effort |
|---|---|---|
| GOLDM vs GOLDTEN pair | Biggest, most liquid leg | Add carry adjustment for the expiry gap (5th vs month-end) and the 3-day-average DDR |
| Carry panel | Implied annual carry vs RBI repo (5.50% since 7 Oct 2026) — built | done |
| Measured slippage | Replace the slippage assumption with real bid/ask from a broker API | 1–2 days + a week of capture |
| Quiet alerts | Telegram/email only when a verdict is EDGE and the residual clears the hurdle | Half a day |
| Daily auto-update | GitHub Action that fetches yesterday's Bhavcopy | Half a day |

## Rules that protect the result

- Never build a continuous near-month series. Always pair contracts with the **same expiry**.
- Signals use data up to day *t*; fills happen at day *t+1*.
- Close every position before the tender window (and the broker's earlier cut-off).
- Settlement price ≠ fill price; volume ≠ depth. Say so on screen.
- A clean **NO EDGE** is a valid result. Don't tune until something looks profitable.
