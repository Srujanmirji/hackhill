# Transaction costs

Defaults in `aulens/costs.py` (discount broker, 2026). Verify against your broker's charges
page; all rates are constructor arguments.

| Charge | Rate | Side |
|---|---|---|
| Brokerage | 0.03% or ₹20 per order, whichever is lower | both |
| CTT (non-agri) | 0.01% | sell |
| MCX transaction charge | 0.0021% | both |
| SEBI fee | ₹10 per crore | both |
| Stamp duty | 0.002% | buy |
| GST | 18% on brokerage + MCX + SEBI | both |

A pair round trip is **4 orders** (each leg bought once and sold once).

## Break-even per 10 g at ₹1.46 lakh (before slippage)

| Pair | Grams | Round trip | Break-even per 10 g |
|---|---|---|---|
| 4 GOLDTEN vs 5 GOLDGUINEA | 40 | ≈ ₹295 | ≈ ₹74 |
| 1 GOLDTEN vs 10 GOLDPETAL | 10 | ≈ ₹145 | ≈ ₹145 |
| 1 GOLDM vs 10 GOLDTEN | 100 | ≈ ₹596 | ≈ ₹60 |

`tests/test_costs.py` checks the first two rows.

## Slippage

Bhavcopy has no bid/ask, so slippage is an **assumption** (default ₹20 per 10 g per leg per
crossing; 4 crossings per round trip). The dashboard shows how net P&L changes from ₹0 to ₹60
and reports the break-even slippage. Tick floors: GOLDTEN ₹1, GOLDGUINEA ₹1.25, GOLDPETAL ₹10
per 10 g.

## Costs outside this model

"Net P&L" means net of the configured charges above plus assumed slippage. It excludes
margin capital, funding/opportunity cost, variation-margin financing and measured market
impact or bid/ask costs beyond the slippage assumption. Delivery/storage costs are not
charged because the model intends to exit before tender. No return on margin/capital is
reported. These exclusions can overstate real-world profitability; see [VALIDATION.md](VALIDATION.md).
