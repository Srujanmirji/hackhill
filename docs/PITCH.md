# 2-minute pitch and live demo

Numbers are from the live app at default settings (data to 23 Oct 2026). Long answers are in
[QA.md](QA.md). Open the app before you start: https://hackhill-wikhjmugah4iqupyf4nlh4.streamlit.app/

## Talk track (≈ 280 words, 2:00)

| Time | Say | Do |
|---|---|---|
| 0:00–0:15 | "On MCX, GOLDGUINEA trades at ₹1,14,322 and GOLDTEN at ₹1,42,260. That's a ₹28,000 gap on the same gold. Traders see gaps like this every day and ask: is it free money?" | App open at the top, scoreboard visible. |
| 0:15–0:35 | "It isn't. Most of it is the rulebook: GUINEA is quoted per 8 grams, TEN per 10, some contracts are 995 purity, some settle in Mumbai, some expire on the 5th. AuLens converts every contract to one unit, then asks if what's left is real **and** tradable after costs." | Scroll to **Check a gap you see**. |
| 0:35–0:55 | "Here's that exact gap. ₹27,938 raw. Same unit: minus ₹642. The rules say it should be zero. The cost hurdle is ₹153. So it clears costs today, but look at the answer: this pair has no tested edge." | Point at the five ledger lines, then the answer box. |
| 0:55–1:20 | "Because we tested it. Walk-forward on 18 months of real settlement data: signals use only past data, fills are next day, every trade exits before delivery. Six pairs, gold and silver. Zero of six show an edge after costs." | Scroll up to **0 of 6 pairs show an edge after costs**. |
| 1:20–1:40 | "And we check ourselves. This control pair must settle at zero, and it does, within one rupee on all 18 expiries. But that only happens in the delivery window, and liquidity peaks 24 days before expiry, right before you're forced out." | Click **GOLDTEN vs GOLDGUINEA** if not selected; scroll to the spread chart, then **When contracts are liquid**. |
| 1:40–2:00 | "The brief says a rigorous 'no edge' is a valid result. AuLens is that result, made usable: it stays quiet until a gap is real, and it shows why. Open source, live today." | Scroll back to the top. Stop. |

**If the app is slow or down:** use slide 4 (How the prototype works) and slide 6 (Results). Say the same lines.

## Click path, in one line

Top scoreboard → scroll to **Check a gap you see** → back up to the scoreboard → **GOLDTEN vs GOLDGUINEA** pill → spread chart → **When contracts are liquid** → top.

Don't touch the sliders during the 2 minutes. The defaults are the numbers on the slides.

## Drill: likely judge questions

Answer each in under 20 seconds. **Bold** = the line you must say.

1. **"So it doesn't work?"** **"It works: it proves there's no edge after costs, which is what the brief asks for."** It stops traders paying to chase a gap that's just the rulebook.
2. **"Why settlement prices, not live ticks?"** The brief's data is the Bhavcopy. **Settlement isn't a fill, so we show break-even slippage**: the control pair dies at ₹3.0 per 10 g a leg, about two ticks.
3. **"How do you know there's no look-ahead?"** Rolling stats are shifted a day, fills are next day, z-thresholds are chosen on earlier months only. **A test adds ₹10 lakh to the last day's spread and checks that no earlier signal changes.**
4. **"Isn't the P&L just gold going up?"** **Gold beta is 0.07 on the control pair**: the result barely depends on the gold move.
5. **"Why is GUINEA ₹642 rich if it settles on the same price?"** Coin demand. The gap only closes at final settlement, **inside the delivery window, after any trader must exit.**
6. **"One pair made ₹35,653. Isn't that an edge?"** **57% came from one trade on 30 Jan 2026, it loses after the May 2026 duty hike, and its confidence interval includes zero.** That's why it's NO EDGE.
7. **"Is 18 months enough?"** GOLDTEN only listed in April 2025, so it's all there is. **The verdict needs every regime positive and a 90% interval above zero, so short data makes us stricter, not looser.**
8. **"Who pays for this?"** Retail and prop traders (free monitor, Pro tier), and **brokers embedding the gap check** so clients don't trade fake arbitrage.
9. **"What did you find that surprised you?"** **Volume peaks about 24 days before expiry, exactly before the window you must exit**. The convergence everyone wants happens when you can't hold.
10. **"What next?"** **Measured slippage from live bid/ask**, then base metals on the same engine.
