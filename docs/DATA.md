# Data

## Source

MCX Daily Bhavcopy — public, no API key: <https://www.mcxindia.com/market-data/bhavcopy>
Fields used: Date, Symbol, ExpiryDate, Open, High, Low, Close, Volume, OpenInterest.

## How to get it

| Route | Reliability | How |
|---|---|---|
| **Browser console fetcher** | Used for the current dataset | Open the MCX Bhavcopy page, paste [`scripts/mcx_fetch_in_browser.js`](../scripts/mcx_fetch_in_browser.js) into the console, run `await aulensFetch({start, end})`; move the CSVs into `data/raw/` and `data/raw/ddr/` |
| Manual download | Works, slower | Historical Data / Bhavcopy pages, max **365 days per query**; save files in `data/raw/` |
| Python / headless browser | Blocked | Akamai answers 403 to `requests`, `curl` and headless Chromium (observed Oct 2026) |

Endpoint map, parameters and how they were reconstructed: [docs/MCX_DATA_API.md](MCX_DATA_API.md).

Old Python libraries (`mcxlib`, `mcxpy`) used `backpage.aspx` routes that MCX retired in its
2026 redesign; they were reported broken in Sep 2026. Don't depend on them.

## Known quirks (all handled in `aulens/data/loader.py`)

| Quirk | Handling |
|---|---|
| Requests use DD/MM/YYYY; response Date is MM/DD/YYYY | Parsed with an explicit format |
| ExpiryDate is compact (`04SEP2026`) | `%d%b%Y` |
| Symbols are space-padded | `.str.strip()` |
| Full holidays return an empty response (7 of 7 observed); other days are checked against the requested date | Day skipped; `assert_requested_date()` and the browser fetcher drop mismatches |
| Options rows mixed in | Keep `InstrumentName` starting with `FUT` |
| GOLDTEN starts 1 Apr 2025 | All TEN pairs have a shorter history — stated on screen |

## Processed schema (`data/processed/gold_futures.parquet`)

| Column | Type | Notes |
|---|---|---|
| date | date | trading day |
| symbol | str | GOLD, GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL |
| expiry | date | contract expiry — the contract key |
| open, high, low, close | float | in the contract's own quote unit |
| volume, oi | int | lots |
| source | str | `MCX` or `SYNTHETIC` |

## Validation log (fill this in)

Raw file: `data/raw/gold_bhavcopy_20250401_20261023.csv`, fetched from the Bhavcopy page's
`GetDateWiseBhavCopy` endpoint (`InstrumentName=FUTCOM`, `fromDate=DD/MM/YYYY`, needs the
`X-Requested-With: XMLHttpRequest` header) inside a real browser session; plain scripts get
Akamai 403. Gold futures rows only. MCX's own field names match `COLMAP`, so no mapping changes.

| Check | Result | Who / when |
|---|---|---|
| Date range loaded | 01 Apr 2025 → 23 Oct 2026, 402 trading days, 10,768 rows (GOLD 2,343 · GOLDM 2,046 · GOLDTEN 2,045 · GOLDGUINEA 2,167 · GOLDPETAL 2,167). No duplicate (date, symbol, expiry) keys; every symbol present on every trading day. | Claude, 26 Oct 2026 |
| Expiries per symbol | GOLD 16 · GOLDM 25 · GOLDTEN 24 · GOLDGUINEA 24 · GOLDPETAL 24 (includes contracts still listed on 23 Oct 2026). Every expired contract trades until its expiry date, except the 31 Mar 2026 TEN/GUINEA/PETAL contracts and the 3 Apr 2026 GOLDM contract, whose last row is one day earlier (holiday at expiry). | Claude, 26 Oct 2026 |
| Silver (added 26 Oct 2026) | `data/raw/silver_bhavcopy_20250401_20261023.csv`, same endpoint and window: 5,401 rows over the same 402 trading days (SILVER 1,954 · SILVERM 1,972 · SILVERMIC 1,475), 8 expired contracts each. DDRs from `data/raw/ddr/mcx_ddr_silver.csv` (MCX `GetDDR`) replace the expiry-day close. Zero-volume rows: SILVER 579 · SILVERM 119 · SILVERMIC 0. Total parquet: 16,169 rows. | Claude, 26 Oct 2026 |
| 3 closes checked by hand against MCX | **TODO (by hand)** — e.g. GOLDTEN 30OCT2026 on 22 Oct 2026 = 142223, GOLDGUINEA 30OCT2026 = 114285, GOLDM 05NOV2026 = 141802. Check these on the MCX Bhavcopy page. | |
| Days dropped as holiday mismatches | 7 weekdays returned no rows (none returned a different date): 18 Apr 2025, 15 Aug 2025, 2 Oct 2025, 25 Dec 2025, 26 Jan 2026, 3 Apr 2026, 2 Oct 2026. | Claude, 26 Oct 2026 |
| Zero-volume rows | GOLD 897 (far months) · GOLDGUINEA 6 · GOLDM 8 · GOLDTEN 1 · GOLDPETAL 0. Kept; the backtest's volume filter excludes them from trading. | Claude, 26 Oct 2026 |

## Synthetic data

`python scripts/build_dataset.py --sample` writes MCX-shaped synthetic rows so the pipeline
and UI can be built before real data arrives. The dashboard shows a warning banner whenever
`source == SYNTHETIC`. **Never present synthetic output as a result.**
