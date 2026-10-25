# Contract specifications

Source: MCX/TRD/456/2025 (11 Sep 2025) and earlier MCX delivery procedures.
**Status: NOT yet verified against the July 2026 MCX spec PDFs** — do that before any pitch,
then record the PDF name and page next to each row.

| | GOLD | GOLDM | GOLDTEN | GOLDGUINEA | GOLDPETAL |
|---|---|---|---|---|---|
| Lot | 1 kg | 100 g | 10 g | 8 g | 1 g |
| Quote | ₹/10 g | ₹/10 g | ₹/10 g | ₹/8 g | ₹/1 g |
| Purity | 995 | 995 | 999 | 999 | 999 |
| Price basis | Ex-Ahmedabad | Ex-Ahmedabad | Ex-Ahmedabad | Ex-Ahmedabad | **Ex-Mumbai** |
| DDR | Ahmedabad spot, 3-day avg | Ahmedabad spot, 3-day avg | Ahmedabad 995 × 999/995 | same × 8/10 | **Mumbai** 995 × 999/995 × 1/10 |
| Last trading day | 5th | 5th | Month-end | Month-end | Month-end |
| Tender window | 5 days* | 5 days | 3 days* | 3 days | 3 days |
| Making charge (delivery) | — | — | — | ₹200/guinea | ₹100/coin* |

\* Conflicts found in research: GOLDTEN was 5 tender days at launch (Mar 2025), 3 in later
specs; a 2026 GOLD circular may show 3 days; an old brochure says ₹200 per Petal coin.

## Verification log

| Field | Contract | PDF / circular | Page | Matches `specs.py`? |
|---|---|---|---|---|
| | | | | |

## Calendar facts used as regime breaks

| Date | Event |
|---|---|
| 23 Jul 2024 | Gold import duty cut 15% → 6% |
| 1 Apr 2025 | GOLDTEN launches |
| 22 Sep 2025 | Six listed expiries per small contract (MCX/TRD/456/2025) |
| 1 Apr 2026 | SEBI: gold ETFs valued on exchange polled spot |
| 13 May 2026 | Gold import duty raised 6% → 15% |
