# Data

## Source

MCX Daily Bhavcopy — public, no API key: <https://www.mcxindia.com/market-data/bhavcopy>
Fields used: Date, Symbol, ExpiryDate, Open, High, Low, Close, Volume, OpenInterest.

## How to get it

| Route | Reliability | How |
|---|---|---|
| Manual download | Highest | Historical Data page, max **365 days per query**; save files in `data/raw/` |
| JSON endpoint | Good once found | DevTools → Network on the Bhavcopy page; copy URL; replace date with `{date}` |
| Browser automation | Fallback | TinyFish or Playwright, when bot protection blocks plain requests |

Old Python libraries (`mcxlib`, `mcxpy`) used `backpage.aspx` routes that MCX retired in its
2026 redesign; they were reported broken in Sep 2026. Don't depend on them.

## Known quirks (all handled in `aulens/data/loader.py`)

| Quirk | Handling |
|---|---|
| Requests use DD/MM/YYYY; response Date is MM/DD/YYYY | Parsed with an explicit format |
| ExpiryDate is compact (`04SEP2026`) | `%d%b%Y` |
| Symbols are space-padded | `.str.strip()` |
| Holidays / bad dates return the nearest trading day | `assert_requested_date()` drops mismatches |
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

| Check | Result | Who / when |
|---|---|---|
| Date range loaded | | |
| Expiries per symbol | | |
| 3 closes checked by hand against MCX | | |
| Days dropped as holiday mismatches | | |

## Synthetic data

`python scripts/build_dataset.py --sample` writes MCX-shaped synthetic rows so the pipeline
and UI can be built before real data arrives. The dashboard shows a warning banner whenever
`source == SYNTHETIC`. **Never present synthetic output as a result.**
