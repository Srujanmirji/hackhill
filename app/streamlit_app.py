"""AuLens dashboard:  streamlit run app/streamlit_app.py"""
import hashlib
import sys
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Streamlit Cloud reruns this file after a git push but can keep the old aulens package in memory
# (seen as an ImportError on a newly added function). Drop it so every run imports the current code.
for _m in [m for m in sys.modules if m == "aulens" or m.startswith("aulens.") or m == "theme"]:
    del sys.modules[_m]
from aulens.backtest import Params, check_gap, latest_signals, walk_forward  # noqa: E402
from aulens.costs import CostModel  # noqa: E402
from aulens.data.loader import PROCESSED, load_processed  # noqa: E402
from aulens.normalize import curve_carry  # noqa: E402
from aulens.specs import (DEFAULT_SLIPPAGE, MCX_FULL_HOLIDAYS, PAIRS, RBI_REPO_RATE, RBI_REPO_SINCE,  # noqa: E402
                          REGIME_BREAKS, SPECS, UNITS, metal)
from aulens.verdict import verdict  # noqa: E402
from theme import (CSS, FAULT, GOLD, GOLD_TEXT, INK, PLOTLY_CONFIG, STEEL, VERDICT_COLOUR, VERDIGRIS,  # noqa: E402
                   hallmark, rupees)

st.set_page_config(page_title="AuLens", page_icon="🔎", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def data(version: tuple):   # keyed on the parquet's mtime so a git pull refreshes the cache
    return load_processed()


SLIP_GRID = {"gold": [0, 10, 20, 30, 40, 60], "silver": [0, 20, 40, 60, 80, 100]}   # ₹ per display unit per leg


def grams(g):
    return f"{g / 1000:g} kg" if g >= 1000 else f"{g:g} g"


# Passed to every cached function that reads df: changes when the data or the engine code changes,
# so Streamlit Cloud never serves results computed by an older backtest after a git pull.
ENGINE = Path(__file__).resolve().parents[1] / "aulens"
VER = (PROCESSED.stat().st_mtime if PROCESSED.exists() else 0.0,
       hashlib.md5(b"".join(f.read_bytes() for f in sorted(ENGINE.rglob("*.py")))).hexdigest())
df = data(VER)
source = "SYNTHETIC" if (df["source"] == "SYNTHETIC").any() else df["source"].iloc[0]

KIND = ["gold · control", "gold · control", "gold · Mumbai vs Ahmedabad", "gold · carry across expiries",
        "silver · control", "silver · carry across expiries"]

st.markdown("<p class='eyebrow'>AuLens · edge validator for MCX gold and silver futures</p>", unsafe_allow_html=True)
st.title("Is this spread real, and tradable after costs?")
if source == "SYNTHETIC":
    st.warning("Synthetic data, for UI development only. Numbers below are not findings.")
st.markdown(f"<p class='lede'>{'Real MCX settlement' if source == 'MCX' else 'Synthetic'} data from "
            f"{df['date'].min():%-d %b %Y} to {df['date'].max():%-d %b %Y}, {len(df):,} contract-days. Every price is "
            "converted to one unit at 999 purity (gold per 10 g, silver per kg), so the rulebook gaps are gone before we compare.</p>",
            unsafe_allow_html=True)
board_box = st.container()   # filled once the assumptions below are known

pick = st.pills("Inspect a pair", range(len(PAIRS)), format_func=lambda i: f"{PAIRS[i][0]} vs {PAIRS[i][1]}",
                default=0, key="pair")
if pick is not None:
    st.session_state["last_pair"] = pick
i_sel = st.session_state.get("last_pair", 0)   # clicking the selected pill again clears it; keep the last pair
a, b = PAIRS[i_sel]
MET = metal(a)
U, UNAME = UNITS[MET]   # display unit: gold ₹ per 10 g, silver ₹ per kg

with st.expander("Assumptions and contract rules"):
    c_set, c_rules = st.columns([1.3, 1], gap="large")
    with c_set:
        slip = st.slider(f"Slippage, ₹ per {UNAME} per leg", 0, SLIP_GRID[MET][-1], DEFAULT_SLIPPAGE[MET], SLIP_GRID[MET][1] // 2,
                         key=f"slip_{MET}",
                         help="Bhavcopy has no order-book depth, so this is an assumption. See the slippage chart.")
        min_vol = st.slider("Minimum daily volume, lots on both legs", 0, 500, 50, 10)
        scale = st.select_slider(f"Size multiplier for {a} vs {b}", [1, 2, 4, 8], 4 if b == "GOLDPETAL" else 1)
        cap_pct = st.slider("Capacity cap, % of each leg's daily volume", 1, 5, 2, 1,
                            help="A trade is skipped if our lots on either leg exceed this share of what traded that day.")
    with c_rules:
        for sp in (SPECS[a], SPECS[b]):
            st.markdown(f"**{sp.symbol}**  \n{grams(sp.lot_grams)} lot, quoted per {grams(sp.quote_grams)}, {sp.purity} purity. "
                        f"Settles on {sp.settle_city} spot, expires "
                        f"{'on the 5th' if sp.expiry_rule == '5th' else 'at month-end'}.")

@st.cache_data
def run(ver, a, b, slip, min_vol, scale, cap_pct):
    """slip is ₹ per display unit per leg (₹/10 g gold, ₹/kg silver); the engine works in ₹ per 10 g."""
    prm = Params(slippage_per_leg=slip / UNITS[metal(a)][0], min_volume=min_vol, lot_scale=scale, capacity_pct=cap_pct / 100)
    res = walk_forward(df, a, b, prm)
    return res, verdict(res)


@st.cache_data
def sensitivity(ver, a, b, min_vol, scale, cap_pct):
    return pd.DataFrame([{"slippage": s, "net": run(ver, a, b, s, min_vol, scale, cap_pct)[1].get("net_pnl", 0)}
                         for s in SLIP_GRID[metal(a)]])


@st.cache_data
def robustness(ver, a, b, min_vol, scale):
    """Net P&L over a slippage x capacity-cap grid: does NO EDGE survive other reasonable settings?"""
    slips, caps = SLIP_GRID[metal(a)], [1, 2, 3, 5]
    z = [[run(ver, a, b, sl, min_vol, scale, cp)[1].get("net_pnl", 0) for sl in slips] for cp in caps]
    return slips, caps, z


def report(v, res, a, b, slip, min_vol, scale, cap_pct):
    """Plain-text summary of the verdict and the assumptions it was made under."""
    lo, hi = v.get("mean_trade_ci90", (float("nan"), float("nan")))
    reg = v["by_regime"].to_string() if "by_regime" in v else "no trades"
    return f"""AuLens verdict report
Pair: {v['pair']} ({v['lots']})
Data: MCX settlement data {df['date'].min():%d %b %Y} to {df['date'].max():%d %b %Y}
Verdict: {v['verdict']}. {v['reason']}

Assumptions
  Slippage per {UNITS[metal(a)][1]} per leg: Rs {slip}
  Minimum daily volume, both legs: {min_vol} lots
  Capacity cap: {cap_pct}% of each leg's daily volume
  Size multiplier: {scale}

Results
  Trades (walk-forward): {v['trades']}
  Gross P&L: Rs {v.get('gross_pnl', 0):,.0f}   Costs: Rs {v.get('costs', 0):,.0f}   Slippage: Rs {v.get('slippage', 0):,.0f}
  Net P&L: Rs {v.get('net_pnl', 0):,.0f}   Win rate: {v.get('hit_rate', 0):.0%}
  Net Sharpe: {v.get('net_sharpe', float('nan')):.2f}   {metal(a).title()} beta: {v.get('gold_beta', float('nan')):.3f}
  Break-even slippage: Rs {v.get('breakeven_slippage_per_leg', float('nan')) * UNITS[metal(a)][0]:.1f} per {UNITS[metal(a)][1]} per leg
  90% CI of the mean trade: Rs {lo:,.0f} to Rs {hi:,.0f}

By regime
{reg}

Method: walk-forward z_entry, signals on day t, fills at t+1 settlement, exits before the tender window.
Not financial advice. https://github.com/Srujanmirji/hackhill
"""


def scoreboard(board, sel):
    """Every pair's verdict in one table, the selected pair marked."""
    edges = sum(bv["verdict"] == "EDGE" for _, bv in board)
    rows = []
    for i, ((pa, pb), (br, bv)) in enumerate(zip(PAIRS, board)):
        u_, un_ = UNITS[metal(pa)]
        be = bv.get("breakeven_slippage_per_leg", float("nan"))
        rows.append(
            f"<tr{' class=\'sel\' aria-current=\'true\'' if i == sel else ''}>"
            f"<th scope='row'>{escape(pa)} vs {escape(pb)}<span class='sub'>{escape(KIND[i])}</span></th>"
            f"<td><span class='pill' style='--mark:{VERDICT_COLOUR[bv['verdict']]}'>{escape(bv['verdict'])}</span></td>"
            f"<td class='num opt'>{bv['trades']}</td><td class='num'>{rupees(bv.get('net_pnl', 0))}</td>"
            f"<td class='num opt'>{'–' if pd.isna(be) else rupees(be * u_, 1) + f' /{un_}'}</td></tr>")
    return (f"<h2 class='board-h'>{edges} of {len(board)} pairs show an edge after costs</h2>"
            "<div class='board-wrap'><table class='board'>"
            "<thead><tr><th scope='col'>Pair</th><th scope='col'>Verdict</th><th scope='col' class='num opt'>Trades</th>"
            "<th scope='col' class='num'>Net P&amp;L</th><th scope='col' class='num opt'>Break-even slippage per leg</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></div>")


def calendar(panel, tender, buffer):
    """Per expiry: first pair day, last tradable day, tender start, expiry. Days after the last
    data date are weekdays minus MCX's published full-day holidays, so live contracts are estimates."""
    last_data = panel["date"].max()
    rows = []
    for exp, g in panel.groupby("expiry"):
        future = pd.bdate_range(last_data + pd.Timedelta(days=1), exp, freq="C", holidays=MCX_FULL_HOLIDAYS)
        days = list(g["date"]) + list(future)
        n = len(days)  # same rule as backtest.add_signals: hold only while days_left > tender + buffer
        rows.append({"expiry": exp, "first": days[0], "last_tradable": days[max(n - 2 - tender - buffer, 0)],
                     "tender_start": days[max(n - tender, 0)], "live": exp > last_data})
    return pd.DataFrame(rows)


# One backtest per pair at the current assumptions; feeds the scoreboard, the selected pair and the alerts.
board = []
for i, (pa, pb) in enumerate(PAIRS):
    m_ = metal(pa)
    board.append(run(VER, pa, pb, slip if m_ == MET else DEFAULT_SLIPPAGE[m_], min_vol,
                     scale if i == i_sel else (4 if pb == "GOLDPETAL" else 1), cap_pct))
with board_box:
    st.markdown(scoreboard(board, i_sel), unsafe_allow_html=True)
res, v = board[i_sel]
panel, trades = res["panel"], res["trades"]
hurdle = CostModel().breakeven_per_10g(panel["px10_a"].iloc[-1], res["grams"])

# ---- Verdict for the selected pair

lots_a, lots_b = res["lots"]
hero, numbers = st.columns([1, 1.9], gap="large")
with hero:
    st.markdown(hallmark(v["verdict"], v["pair"], f"{lots_a} {a} against {lots_b} {b}, {grams(res['grams'])} a side"),
                unsafe_allow_html=True)
    st.markdown(f"<div class='reason'>{v['reason']}</div>", unsafe_allow_html=True)
    if "mean_trade_ci90" in v:
        lo, hi = v["mean_trade_ci90"]
        st.caption(f"90% confidence that the average trade nets between {rupees(lo)} and {rupees(hi)}; "
                   f"{v['hit_rate']:.0%} of trades made money.")
with numbers:
    r1, r2 = st.columns(3), st.columns(3)
    beta = v.get("gold_beta", float("nan"))
    r1[0].metric("Trades", v["trades"], help="Walk-forward: each month is traded with settings chosen on earlier months only.")
    r1[1].metric("Net P&L", rupees(v.get("net_pnl", 0)), help="After statutory costs, brokerage and the slippage set under Assumptions.")
    sharpe = v.get("net_sharpe", float("nan"))
    r1[2].metric("Net Sharpe", "–" if pd.isna(sharpe) else f"{sharpe:.2f}",
                 help="Average net trade divided by its spread, scaled by how many trades a year the pair made.")
    r2[0].metric("Cost hurdle", rupees(hurdle * U), help=f"Statutory charges and brokerage for a round trip, per {UNAME}, before slippage.")
    r2[1].metric("Break-even", rupees(v.get("breakeven_slippage_per_leg", float("nan")) * U, 1),
                 help=f"Slippage per {UNAME} per leg at which net P&L reaches zero. Negative means it loses even with perfect fills.")
    r2[2].metric(f"{MET.title()} beta", "–" if pd.isna(beta) else f"{beta:.2f}",
                 help=f"Slope of trade P&L on the {MET} price move. Near 0 means the result is not just {MET} going up.")

# ---- Spread chart for one expiry
st.subheader("The spread, one contract at a time")
exps = sorted(panel["expiry"].unique())
expired = [x for x in exps if x <= panel["date"].max()]   # show a full life, through settlement
default_exp = expired[-1] if expired else exps[0]
exp = st.select_slider("Contract expiring in", exps, value=default_exp,
                       format_func=lambda d: pd.Timestamp(d).strftime("%b %Y"))
e = panel[panel["expiry"] == exp]
fig = go.Figure()
band = hurdle * U + 4 * slip
e = e.assign(expected=e["expected"] * U, spread=e["spread"] * U)
fig.add_trace(go.Scatter(x=e["date"], y=e["expected"] + band, line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=e["date"], y=e["expected"] - band, fill="tonexty", fillcolor="rgba(46,125,107,0.10)",
                         line=dict(width=0), name="Cost band", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=e["date"], y=e["expected"], name="Rules' end point",
                         line=dict(color=VERDIGRIS, dash="dash", width=1.5)))
fig.add_trace(go.Scatter(x=e["date"], y=e["spread"], name="Spread", line=dict(color=INK, width=1.8)))
et = trades[trades["expiry"] == exp] if len(trades) else trades
if len(et):
    m = e.set_index("date")["spread"]
    fig.add_trace(go.Scatter(x=et["entry_date"], y=m.reindex(et["entry_date"]).values, mode="markers",
                             marker=dict(color=GOLD, size=10, line=dict(color="white", width=1.5)), name="Entry (next-day fill)"))
    fig.add_trace(go.Scatter(x=et["exit_date"], y=m.reindex(et["exit_date"]).values, mode="markers",
                             marker=dict(color=VERDIGRIS, size=10, symbol="x-thin", line=dict(color=VERDIGRIS, width=2.5)),
                             name="Exit"))
shown = [(d, label) for d, label in REGIME_BREAKS.items() if e["date"].min() <= pd.Timestamp(d) <= e["date"].max()]
for k, (d, label) in enumerate(shown):   # stagger labels so neighbouring breaks don't collide
    fig.add_vline(x=pd.Timestamp(d), line=dict(color=FAULT, dash="dot", width=1))
    fig.add_annotation(x=pd.Timestamp(d), y=1 - 0.07 * (k % 2), yref="paper", text=label, showarrow=False,
                       xanchor="left", yanchor="top", xshift=6, font=dict(size=11, color=FAULT),
                       bgcolor="rgba(246,247,245,0.85)")
fig.update_layout(height=420, yaxis_title=f"₹ per {UNAME} at 999")
st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
st.caption("The dark line is the price gap between the two contracts. The dashed line is where the exchange "
           "rules say it must end up; a trade is only worth taking once the gap leaves the shaded cost band.")

# ---- Check a gap you see
st.subheader("Check a gap you see")
last_day = panel["date"].max()
live = panel[panel["date"] == last_day].sort_values("expiry")
qa, qb = grams(SPECS[a].quote_grams), grams(SPECS[b].quote_grams)
st.caption(f"Type the two prices from your trading screen exactly as quoted: {a} per {qa}, {b} per {qb}. "
           f"They start at the {last_day:%-d %b %Y} settlement prices.")


def contract_label(x):
    rw = live[live["expiry"] == x].iloc[0]
    if "expiry_a" in rw:   # carry pair: a's month M+1 against b's month M
        return f"{a} {rw['expiry_a']:%b %Y} / {b} {x:%b %Y}"
    return f"{x:%b %Y}"


g1, g2, g3 = st.columns([1.2, 1, 1])
holdable = live["can_hold"].tolist()
exp_g = g1.selectbox("Contract", live["expiry"].tolist(), format_func=contract_label, key=f"gap_exp_{a}_{b}",
                     index=holdable.index(True) if True in holdable else 0)   # nearest contract still outside the exit window
row = live[live["expiry"] == exp_g].iloc[0]
tag = f"{a}_{b}_{pd.Timestamp(exp_g):%Y%m%d}"
price_a = g2.number_input(f"{a}, ₹ per {qa}", min_value=1.0, value=float(row["close_a"]), step=1.0, format="%.0f", key=f"gap_a_{tag}")
price_b = g3.number_input(f"{b}, ₹ per {qb}", min_value=1.0, value=float(row["close_b"]), step=1.0, format="%.0f", key=f"gap_b_{tag}")
g = check_gap(res, exp_g, price_a, price_b)

edge = v["verdict"] == "EDGE"
OUTCOME = {
    "implausible": (FAULT, "These prices are more than 5% apart once converted to the same unit. "
                           "Check the prices and the contract month."),
    "no_estimate": (GOLD_TEXT, "AuLens has no expected spread for this contract yet: it needs about 20 days of its own history."),
    "late": (STEEL, "Too close to delivery. Under AuLens' exit rule a position in this contract must already be closed."),
    "inside": (STEEL, "Inside the cost band. The rulebook and trading costs explain this gap, so there is nothing to trade."),
    "clears": (VERDIGRIS, "Clears the rulebook and costs, on a pair with a tested edge. Check volume and the z-score before acting.")
              if edge else
              (GOLD_TEXT, f"Clears the rulebook and costs today, but this pair's verdict is {v['verdict']}: "
                          "in the backtest, gaps like this did not pay after costs."),
}
colour, message = OUTCOME[g["status"]]
fmt = lambda x: "–" if pd.isna(x) else rupees(x * U)   # noqa: E731
lines = [("Raw difference of the two quotes", rupees(g["quoted_gap"]), "different units, so not comparable"),
         (f"Same gap in ₹ per {UNAME} at 999", fmt(g["spread"]), "after purity and quote-unit conversion"),
         ("Where the rules say it should be", fmt(g["expected"]), "same city and expiry: ₹0; otherwise basis or carry"),
         ("Left over", fmt(g["residual"]), "what could be mispricing"),
         ("Cost and slippage hurdle", f"± {fmt(g['hurdle'])}", f"round-trip costs plus ₹{slip} slippage per leg")]
st.markdown("<div class='gap'><dl class='gap-ledger'>" + "".join(
    f"<div{' class=\'key\'' if k == 3 else ''}><dt>{escape(t)}<span>{escape(why)}</span></dt><dd>{val}</dd></div>"
    for k, (t, val, why) in enumerate(lines)) + "</dl>"
    f"<p class='gap-out' role='status' style='--mark:{colour}'>{escape(message)}</p></div>", unsafe_allow_html=True)
st.caption(f"Expected spread and the delivery-window check use data to {last_day:%-d %b %Y}. "
           "A single quote has no z-score or volume, so those entry rules are not checked here.")

# ---- Sensitivity + regimes
l, r = st.columns(2, gap="large")
with l:
    st.subheader("What slippage does to it")
    sens = sensitivity(VER, a, b, min_vol, scale, cap_pct)
    f2 = go.Figure(go.Bar(x=sens["slippage"], y=sens["net"], width=6,
                          marker_color=[VERDIGRIS if n > 0 else STEEL for n in sens["net"]],
                          marker_line=dict(color=[GOLD if s == slip else "rgba(0,0,0,0)" for s in sens["slippage"]], width=2.5),
                          hovertemplate="₹%{x} slippage: net ₹%{y:,.0f}<extra></extra>"))
    f2.add_hline(y=0, line=dict(color=INK, width=1))
    f2.update_layout(height=300, xaxis_title=f"Slippage, ₹ per {UNAME} per leg", yaxis_title="Net P&L, ₹",
                     xaxis=dict(tickvals=sens["slippage"]))
    st.plotly_chart(f2, width="stretch", config=PLOTLY_CONFIG)
    st.caption("Net profit if every fill costs this much extra. Green makes money, grey loses; "
               "the outlined bar is the slippage set under Assumptions.")
with r:
    st.subheader("Results by regime")
    if "by_regime" in v:
        reg = v["by_regime"].rename(columns={"count": "Trades", "sum": "Net P&L"}).rename_axis("Regime")
        st.table(reg.assign(**{"Net P&L": reg["Net P&L"].map(rupees)})
                 .style.set_properties(subset=["Net P&L"], **{"text-align": "right"}))
        st.caption("The same trades, split by the market regime they were opened in. "
                   "A real edge makes money in every row.")
    else:
        st.info("No trades cleared the cost hurdle, so there is nothing to split. Lower the slippage or volume filter to see why.")

# ---- Carry vs repo
st.subheader("What the curve pays to hold gold")
carry = curve_carry(df, "GOLDTEN")
f4 = go.Figure()
f4.add_trace(go.Scatter(x=carry.index, y=carry * 100, name="Daily implied carry", mode="lines",
                        line=dict(color=STEEL, width=1), opacity=0.45))
f4.add_trace(go.Scatter(x=carry.index, y=carry.rolling(20, min_periods=5).median() * 100, name="20-day median",
                        line=dict(color=GOLD, width=2.2)))
f4.add_hline(y=RBI_REPO_RATE * 100, line=dict(color=VERDIGRIS, dash="dash", width=1.5),
             annotation_text=f"RBI repo today {RBI_REPO_RATE:.2%}", annotation_position="top left",
             annotation_font=dict(color=VERDIGRIS, size=11))
f4.update_layout(height=300, yaxis_title="% a year", yaxis=dict(ticksuffix="%"))
st.plotly_chart(f4, width="stretch", config=PLOTLY_CONFIG)
before, after = carry[:"2025-11-30"].median(), carry["2025-12-01":].median()
st.caption(f"Annual rate implied by the two nearest GOLDTEN contracts: median {before:.1%} through Nov 2025, "
           f"{after:.1%} from the Dec 2025 rally onward. The dashed line is today's RBI repo rate "
           f"({RBI_REPO_RATE:.2%} since {pd.Timestamp(RBI_REPO_SINCE):%-d %b %Y}); earlier repo changes are not drawn. "
           "COMEX carry is not shown; AuLens has no COMEX data yet.")

# ---- Quiet alerts
st.subheader("Quiet alerts")
rows = []
for i, (pa, pb) in enumerate(PAIRS):
    m_, (u_, un_) = metal(pa), UNITS[metal(pa)]
    r_res, r_v = board[i]
    sig = latest_signals(r_res)
    ratio = (sig["residual"].abs() / sig["hurdle"]).dropna()   # newest contracts may lack a basis estimate yet
    if ratio.empty:
        continue
    top = sig.loc[ratio.idxmax()]
    status = ("Alert" if top["clears"] and r_v["verdict"] == "EDGE"
              else "Clears the hurdle, but the verdict is not EDGE" if top["clears"] else "Below the entry rules")
    rows.append({"Pair": f"{pa} vs {pb}", "Closest contract": top["expiry"].strftime("%b %Y"),
                 "Gap": rupees(top["residual"] * u_) + f" /{un_}", "Hurdle": rupees(top["hurdle"] * u_) + f" /{un_}",
                 "Status": status})
alerts = pd.DataFrame(rows).set_index("Pair")
if (alerts["Status"] == "Alert").any():
    st.success("A pair with an EDGE verdict clears its cost hurdle today.")
else:
    st.markdown(f"No alerts on {df['date'].max():%-d %b %Y}. AuLens only alerts when a pair's verdict is EDGE "
                "**and** the gap clears costs, slippage and the entry rules, so silence is the normal state.")
st.table(alerts)
st.caption("Gap and hurdle are for the contract closest to its hurdle (gold per 10 g, silver per kg). Entry rules also need a large "
           "enough z-score, enough volume and enough days before the delivery window.")

# ---- Robustness
st.subheader("Does NO EDGE survive other settings?")
st.caption("Net P&L for this pair across slippage and capacity-cap settings, everything else as set under Assumptions. "
           "About 24 backtests, so it runs on request and is then cached.")
if st.button("Run the robustness grid", key="robust") or st.session_state.get("robust_done"):
    st.session_state["robust_done"] = True
    with st.spinner("Running 24 walk-forward backtests…"):
        slips, caps, z = robustness(VER, a, b, min_vol, scale)
    zabs = max(abs(x) for row in z for x in row) or 1
    f5 = go.Figure(go.Heatmap(
        z=z, x=[f"₹{x}" for x in slips], y=[f"{c}%" for c in caps], zmid=0, zmin=-zabs, zmax=zabs,
        colorscale=[[0, STEEL], [0.5, "#F6F7F5"], [1, VERDIGRIS]], showscale=False,
        text=[[rupees(x) for x in row] for row in z], texttemplate="%{text}", textfont=dict(size=13),
        hovertemplate="Slippage %{x}, cap %{y}: %{text}<extra></extra>"))
    f5.update_layout(height=320, xaxis_title=f"Slippage, ₹ per {UNAME} per leg", yaxis_title="Capacity cap",
                     xaxis=dict(type="category"), yaxis=dict(type="category"))
    st.plotly_chart(f5, width="stretch", config=PLOTLY_CONFIG)
    wins = sum(x > 0 for row in z for x in row)
    total = len(slips) * len(caps)
    why = ""
    if wins == total and v["verdict"] != "EDGE":
        why = (" Costs and slippage are not what stops this pair: it is still NO EDGE because it loses in at "
               "least one regime and its 90% confidence interval includes zero.")
    st.caption(f"{wins} of {total} settings make money. Green makes money, grey loses; "
               f"a real edge would stay green across most of the grid.{why}")

# ---- Take the numbers with you
st.subheader("Take the numbers with you")
d1, d2 = st.columns(2)
d1.download_button("Download verdict report (.txt)", report(v, res, a, b, slip, min_vol, scale, cap_pct),
                   file_name=f"aulens_{a}_{b}_verdict.txt", mime="text/plain", width="stretch")
d2.download_button("Download trade log (.csv)", trades.assign(pair=f"{a} vs {b}").to_csv(index=False),
                   file_name=f"aulens_{a}_{b}_trades.csv", mime="text/csv", width="stretch", disabled=trades.empty)

# ---- Contract calendar
st.subheader("When a position can be held")
tender = max(SPECS[a].tender_days, SPECS[b].tender_days)
cal = calendar(panel, tender, res["params"].exit_buffer_days)
phases = {"Can hold the pair": GOLD, "Must already be out": STEEL, "Delivery window to expiry": FAULT}
segments = pd.concat([
    cal.assign(start=cal["first"], end=cal["last_tradable"], phase="Can hold the pair"),
    cal.assign(start=cal["last_tradable"], end=cal["tender_start"], phase="Must already be out"),
    cal.assign(start=cal["tender_start"], end=cal["expiry"], phase="Delivery window to expiry"),
])
segments["contract"] = segments["expiry"].dt.strftime("%b %Y") + segments["live"].map({True: " (live, est.)", False: ""})
f3 = px.timeline(segments, x_start="start", x_end="end", y="contract", color="phase", color_discrete_map=phases,
                 hover_data={"first": "|%d %b %Y", "last_tradable": "|%d %b %Y", "expiry": "|%d %b %Y",
                             "start": False, "end": False, "contract": False, "phase": False})
f3.update_yaxes(autorange="reversed", title=None, showgrid=False)
f3.update_xaxes(showgrid=True, gridcolor="#E3E6E1")
f3.update_layout(height=max(300, 22 * len(cal)), bargap=0.35, legend_title_text="")
st.plotly_chart(f3, width="stretch", config=PLOTLY_CONFIG)
st.caption("One bar per contract. Gold is when AuLens may hold the pair; grey is the broker's early-exit "
           "buffer; red is the delivery window up to expiry. Dates after the last data day skip weekends and "
           "MCX's published 2026 holidays (2027 is not out yet), so live contracts are estimates.")

with st.expander("Every trade"):
    st.dataframe(trades, hide_index=True)
with st.expander("How AuLens decides"):
    st.markdown(Path(__file__).resolve().parents[1].joinpath("docs", "METHODOLOGY.md").read_text())
