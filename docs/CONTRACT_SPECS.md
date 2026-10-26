# Contract specifications

**Verified 26 Oct 2026** against the current MCX contract-specification PDFs (mcxindia.com →
Products → Bullion → Gold). One correction made: GOLD and GOLDM tender window is 3 days, not 5.

| | GOLD | GOLDM | GOLDTEN | GOLDGUINEA | GOLDPETAL |
|---|---|---|---|---|---|
| Lot | 1 kg | 100 g | 10 g | 8 g | 1 g |
| Quote | ₹/10 g | ₹/10 g | ₹/10 g | ₹/8 g | ₹/1 g |
| Tick | ₹1 per 10 g | ₹1 per 10 g | ₹1 per 10 g | ₹1 per 8 g | ₹1 per 1 g |
| Purity | 995 | 995 | 999 | 999 | 999 |
| Price basis | Ex-Ahmedabad | Ex-Ahmedabad | Ex-Ahmedabad | Ex-Ahmedabad | **Ex-Mumbai** |
| DDR | Ahmedabad spot, avg of last 3 polled days | Ahmedabad spot, avg of last 3 polled days | Ahmedabad 995 × 999/995, expiry-day poll | same, expiry-day poll | **Mumbai** 995 × 999/995, expiry-day poll |
| Last trading day | 5th | 5th | Last calendar day | Last calendar day | Last calendar day |
| Tender window | Last 3 trading days | Last 3 trading days | Last 3 trading days | Last 3 trading days | Last 3 trading days |
| Making charge (buyer, on delivery) | — | — | ₹300 per 10 g | ₹200 per guinea | ₹100 per 1 g coin |

Making charges are not in `specs.py` because AuLens never takes delivery; they are one more
reason holding into the tender window is not free.

## Verification log

PDFs: *Gold February 2027 Contract Onwards* (MCX/TRD/040/2026), *Gold Mini August 2026 Contract
Onwards* (MCX/TRD/041/2026), *Gold Guinea / Gold Petal July 2026 Contract Onwards*
(MCX/TRD/042, 043/2026 and MCX/PMT/375/2026), *Gold Ten July 2026 Contract Onwards*
(MCX/TRD/044/2026 and MCX/PMT/375/2026).

| Field | Contract | PDF page | Matches `specs.py`? |
|---|---|---|---|
| Lot, quote unit, tick, price basis, last trading day | all five | p. 1 | Yes |
| Purity (quality specification) | all five | p. 2 | Yes |
| Tender window: "last 3 trading days (including expiry day)" | GOLDTEN, GOLDGUINEA, GOLDPETAL | p. 2 | Yes (3) |
| Tender window: "last 3 trading days (including expiry day)" | GOLD, GOLDM | p. 2 | **No — was 5, corrected to 3** |
| DDR: simple average of last 3 polled spot prices | GOLD (p. 3), GOLDM (p. 2) | | Yes (`ddr_days_avg = 3`) |
| DDR: expiry-day poll, 995 × 999/995; Ahmedabad for TEN/GUINEA, Mumbai for PETAL | GOLDTEN (p. 3), GOLDGUINEA (p. 2), GOLDPETAL (p. 3) | | Yes |
| Making charges | GOLDTEN (p. 8), GOLDGUINEA (p. 11), GOLDPETAL (p. 8) | | Not modelled (no delivery) |

Effect of the correction: only the GOLDM vs GOLDTEN pair changes (positions may be held two
trading days longer). Its verdict stays NO EDGE.

## Calendar facts used as regime breaks

| Date | Event |
|---|---|
| 23 Jul 2024 | Gold import duty cut 15% → 6% |
| 1 Apr 2025 | GOLDTEN launches |
| 22 Sep 2025 | Six listed expiries per small contract (MCX/TRD/456/2025) |
| 1 Apr 2026 | SEBI: gold ETFs valued on exchange polled spot |
| 13 May 2026 | Gold import duty raised 6% → 15% |
