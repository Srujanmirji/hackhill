# MCX data layer (reconstructed)

How mcxindia.com's own pages fetch the data AuLens uses, reconstructed on 26 Oct 2026 from the
site's shipped JavaScript and checked against live responses. Use it with
[`scripts/mcx_fetch_in_browser.js`](../scripts/mcx_fetch_in_browser.js).

## How it was reconstructed

1. The 15 scripts loaded by the Bhavcopy, DDR, Historical Data and Trading Holidays pages were
   saved from a normal browser session (no code executed outside the page).
2. REA (`analyze_javascript_application`, static, nothing executed) parsed all 15 with no
   failures: 57,023 syntax nodes, 30 module nodes. Evidence `ev_867cb3eb…ce72f`, input digest
   `54a5fabc…30f36`. REA's request model covers `fetch`, not jQuery `$.ajax`, so the endpoint
   calls below were read from the same files at the cited lines.
3. Every endpoint AuLens depends on was then called from a page on mcxindia.com and its output
   compared with the stored dataset (28 Sep – 23 Oct 2026: 562 of 562 Bhavcopy rows and all
   5 DDRs identical).

**Not reproducible from scripts.** Akamai answers 403 to `requests`, `curl` and REA's own
headless Chromium (observed). The endpoints work only inside a real browser session, so the
fetcher runs in your browser's console. AuLens does not try to get around the bot protection.

## URL rule

`GetData(MethodName, type, data, …)` in `assets/customjs/data.js` builds every URL as
`location.origin + location.pathname + MethodName`, so endpoints hang off the page path.
jQuery adds `X-Requested-With: XMLHttpRequest`; without it the endpoints return a 404 HTML page.
Responses are JSON: `{IsSuccess?, Message?, Data: [...], Summary?/Metadata?}`.

## Endpoints AuLens uses

| Endpoint | Source | Params | Notes |
|---|---|---|---|
| `GET /market-data/bhavcopy/GetDateWiseBhavCopy` | `BhavCopy.js:594` | `InstrumentName` (`FUTCOM` for futures, `ALL`), `fromDate` `DD/MM/YYYY` | One day, all commodities. Row `Date` is `MM/DD/YYYY`, `ExpiryDate` `30OCT2026`, `Symbol` space-padded. **Full holidays return an empty `Data` list**, not the nearest day (7 of 7 holidays, Apr 2025 – Oct 2026). Morning-only holidays return the evening session. |
| `GET /market-data/ddr/GetDDR` | `DDR.js:198` | `symbol` (e.g. `GOLDTEN`), `fromDate`, `toDate` `DD/MM/YYYY` | Final settlement prices. `date` is `/Date(ms)/` at IST midnight, `ddrNormal` is in the contract's quote unit, `baseQty` its grams. Empty result: `{"IsSuccess":false,"Message":"No data found."}`. |

## Other endpoints found (not used)

| Endpoint | Source | Params |
|---|---|---|
| `/market-data/bhavcopy/GetCommoditywiseBhavCopy` | `BhavCopy.js:620` | `InstrumentName`, `Symbol`, `Expiry`, `fromDate`, `toDate` |
| `/GetHistoricalDataDetails`, `/GetHistoricalData` | `historicalDataCustom.js:405`, `:469` | `GroupBy`, `Segment`, `CommodityHead`, `Commodity`, `Startdate`, `EndDate` (`YYYYMMDD`), `InstrumentName` |
| `/GetQuote`, `/GetQuoteOption` | `MarketData.js:659`, `:699` | `type`; option strike, type, expiry |
| `/GetFuturePriceFMC` | `FMCFuturePrice.js:144` | `commodity`, `Expiry`, `pageNumber`, `pageSize`, `isExport` |
| `/MCX_Service.asmx/GetSymbolDropDown` | `Developer.js:902` | symbol list for dropdowns |
| `/getFilteredMarketwideData`, `/GetFilteredData`, `/GetFiltered…Summary` | `MarketWideReportInterest.js:57`, `Marketwidepositionlimit.js:67`, `MarketOperation.js` | market-wide reports |

Trading holidays have no data call: the table is part of the page HTML
(`/market-operations/trading-surveillance/trading-holidays`). AuLens copies the full-day closures
into `aulens/specs.py` (`MCX_FULL_HOLIDAYS`).

## Unknowns

- Rate limits are not documented; the fetcher waits 0.8 s between requests and 409 consecutive
  requests completed without errors.
- MCX can change these endpoints without notice (its 2026 redesign already retired the old
  `backpage.aspx` routes). If the fetcher starts returning HTML, re-run the reconstruction.
