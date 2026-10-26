# Final-round submission kit (deadline 28 Oct 2026)

The Google Form takes **one submission per team**. Fill it only when every link below opens in a
private/incognito window.

## 1-minute elevator pitch (≈150 words, 60 s)

The intro **must** contain the exact phrase *"Hack in Hills, powered by TinyFish."* Say it word for word.

| Time | Say | Show |
|---|---|---|
| 0:00–0:08 | "Hi, we're team CodeWick, and this is AuLens, built for **Hack in Hills, powered by TinyFish.**" | Faces or app top screen |
| 0:08–0:18 | "On MCX the same gold trades in five contract sizes, and their prices never match. GOLDTEN and GOLDGUINEA sit ₹28,000 apart. Free money? No." | Scoreboard |
| 0:18–0:33 | "Most of that gap is the rulebook: grams per quote, 995 versus 999 purity, settlement city, expiry date. AuLens converts every contract to rupees per 10 grams of 999 gold and removes everything the rules explain." | **Check a gap you see** ledger |
| 0:33–0:48 | "We test monthly on earlier-month thresholds, using simulated settlement fills, modelled fees and assumed slippage. Zero of six pairs establishes an edge. Funding is excluded; this is not a final untouched holdout." | Scoreboard → spread chart |
| 0:48–1:00 | "AuLens tells traders when a gap is real, and when it's just the rulebook. Open source, live today. Link below." | App top + URL on screen |

Record vertical (9:16) if it will also go on Instagram; LinkedIn and X accept it too.
Keep it ≤ 60 s. Burn in captions: most people watch muted.

## Accounts to tag (all posts)

**@TinyFish @Nexido @BuilderBase @Web3India**. Type each handle and pick it from the
dropdown so it becomes a real tag; the handle can differ per platform, so check each one resolves
to the right page before posting.

## LinkedIn post (mandatory)

> Same gold, five prices. Is the gap free money?
>
> At Hack in Hills, powered by TinyFish, our team CodeWick built AuLens: an edge validator for MCX gold and silver futures.
>
> MCX lists the same metal in several contract sizes, and their prices never line up. Most of the gap is written into the contract rules: purity, quotation unit, settlement city, expiry. AuLens removes everything the rulebook explains, then tests the residual after modelled costs using monthly walk-forward selection and regime checks within the available 2025–26 history.
>
> On 18 months of real MCX data: 0 of 6 pairs show an edge after costs. Our control pair converges within ₹1 on all 18 expiries, but only inside the delivery window, after a trader must exit.
>
> Fills are simulated from settlement observations with assumed slippage. Margin/funding and measured market impact are excluded. There is no final untouched holdout; metal beta is diagnostic, not proof of neutrality.
>
> A rigorous "no edge" is a result. AuLens makes it usable.
>
> Live demo: https://hackhill-wikhjmugah4iqupyf4nlh4.streamlit.app/
> Code: https://github.com/Srujanmirji/hackhill
>
> @TinyFish @Nexido @BuilderBase @Web3India
> #HackInHills #TinyFish #MCX #QuantFinance #OpenSource

## X / Twitter post (mandatory, ≤280 characters)

> Same gold on MCX, five prices. Free money? No.
>
> AuLens strips out what the contract rules explain and tests the rest after modelled costs: 0 of 6 pairs establishes an edge.
>
> Built at #HackInHills, powered by TinyFish.
> hackhill-wikhjmugah4iqupyf4nlh4.streamlit.app
>
> @TinyFish @Nexido @BuilderBase @Web3India

Paste it into the composer and check the counter before posting; links count as 23 characters.
If it runs over, drop the `#HackInHills` line first.

## Instagram reel (optional)

> Team CodeWick at Hack in Hills, powered by TinyFish. We built AuLens: is an MCX gold spread real, and is it tradable after costs? Live demo link in bio.
> @TinyFish @Nexido @BuilderBase @Web3India #HackInHills

Put the demo URL in your bio for the day; Instagram captions don't make links clickable.

## Google Form: answers to paste

- **Team name:** CodeWick
- **Project:** AuLens
- **One-liner:** An edge validator for MCX gold and silver futures: it removes the price gap the contract rules explain and tests whether the rest is tradable after real costs.
- **Description:** MCX lists the same metal in several contract sizes whose prices never match. AuLens normalizes every contract to ₹ per 10 g at 999 purity using MCX's own formulas, matches grams on individual expiries (with explicit cross-expiry carry pairs), and runs monthly walk-forward threshold selection with next-available settlement observations as simulated fills. P&L deducts configured CTT, exchange/SEBI fees, stamp duty, GST, brokerage and assumed slippage. Margin/funding and measured market impact are excluded. Monthly replay boundaries and thresholds are downloadable; existing positions close at each expiry slice's last observation; final-observation entries are omitted from completed trades. There is no final untouched holdout. Metal beta is a diagnostic, not proof of neutrality or alpha. The GOLDM averaging adjustment remains unmodelled. Each pair gets one verdict: EDGE, NO EDGE or UNTESTABLE. On real MCX data from 1 Apr 2025 to 23 Oct 2026, none of six gold and silver pairs shows an edge after costs; the control pairs converge close to ₹0 at expiry, supporting the normalization checks.
- **Track:** Track 03: Commodity Derivatives Intelligence
- **Live demo:** https://hackhill-wikhjmugah4iqupyf4nlh4.streamlit.app/
- **Repo:** https://github.com/Srujanmirji/hackhill
- **Demo video:** _(Drive/YouTube link to `AuLens_demo_HackInHills26_v2.mp4`, set to "Anyone with the link")_
- **Deck:** _(Drive link to `CodeWick_AuLens_HackInHills26_v5.pdf`, "Anyone with the link")_
- **LinkedIn post:** _(link)_
- **X post:** _(link)_
- **Instagram post:** _(link, optional)_

## Evidence to include with the submission

Link [VALIDATION.md](VALIDATION.md). Download the monthly validation CSV, verdict report and
trade log at default assumptions. Keep the MCX dataset range (1 Apr 2025–23 Oct 2026) distinct
from the test-window range shown for each pair. Do not relabel already-inspected dates as a
final untouched holdout. Do not claim executable settlement fills, all-in costs or proven alpha.
Re-record/revise the video and PDF deck if they contain stronger wording; updating this kit
alone does not change those assets.

## Before you press Submit

- [ ] Pitch video says "Hack in Hills, powered by TinyFish." word for word, in the intro
- [ ] LinkedIn and X posts are public and all four accounts are tagged (tags clickable)
- [ ] Every link opens in an incognito window: app, repo, video, deck, all posts
- [ ] Repo is public; Streamlit app is awake (open it once just before submitting)
- [ ] Member names, emails and phone numbers checked by each member
- [ ] Submit by 27 Oct night, not 28 Oct: the form is one-shot and there's no extension
