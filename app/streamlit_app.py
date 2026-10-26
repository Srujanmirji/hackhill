"""AuLens dashboard:  streamlit run app/streamlit_app.py"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aulens.backtest import Params, latest_signals, walk_forward  # noqa: E402
from aulens.costs import CostModel  # noqa: E402
from aulens.data.loader import load_processed  # noqa: E402
from aulens.normalize import curve_carry  # noqa: E402
from aulens.specs import MCX_FULL_HOLIDAYS, PAIRS, RBI_REPO_RATE, RBI_REPO_SINCE, REGIME_BREAKS, SPECS  # noqa: E402
from aulens.verdict import verdict  # noqa: E402
from theme import (CSS, FAULT, GOLD, INK, PLOTLY_CONFIG, STEEL, VERDIGRIS,  # noqa: E402
                   hallmark, rupees)

st.set_page_config(page_title="AuLens", page_icon="🔎", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def data():
    return load_processed()


df = data()
source = "SYNTHETIC" if (df["source"] == "SYNTHETIC").any() else df["source"].iloc[0]

with st.sidebar:
    st.header("AuLens")
    st.caption("An edge validator for MCX gold futures.")
    tags = {0: " (control)", 2: " (stretch)"}
    labels = [f"{a} vs {b}" + tags.get(i, "") for i, (a, b) in enumerate(PAIRS)]
    a, b = PAIRS[st.radio("Pair to test", range(len(PAIRS)), format_func=lambda i: labels[i])]
    st.subheader("Assumptions")
    slip = st.slider("Slippage, ₹ per 10 g per leg", 0, 60, 20, 5,
                     help="Bhavcopy has no order-book depth, so this is an assumption. See the slippage chart.")
    min_vol = st.slider("Minimum daily volume, lots on both legs", 0, 500, 50, 10)
    scale = st.select_slider("Size multiplier", [1, 2, 4, 8], 4 if b == "GOLDPETAL" else 1)
    cap_pct = st.slider("Capacity cap, % of each leg's daily volume", 1, 5, 2, 1,
                        help="A trade is skipped if our lots on either leg exceed this share of what traded that day.")
    st.subheader("Contract rules")
    for s in (SPECS[a], SPECS[b]):
        st.markdown(f"**{s.symbol}**  \n{s.lot_grams:g} g lot, quoted per {s.quote_grams:g} g, {s.purity} purity. "
                    f"Settles on {s.settle_city} spot, expires "
                    f"{'on the 5th' if s.expiry_rule == '5th' else 'at month-end'}.")


@st.cache_data
def run(a, b, slip, min_vol, scale, cap_pct):
    prm = Params(slippage_per_leg=slip, min_volume=min_vol, lot_scale=scale, capacity_pct=cap_pct / 100)
    res = walk_forward(df, a, b, prm)
    return res, verdict(res)


@st.cache_data
def sensitivity(a, b, min_vol, scale, cap_pct):
    return pd.DataFrame([{"slippage": s, "net": run(a, b, s, min_vol, scale, cap_pct)[1].get("net_pnl", 0)}
                         for s in [0, 10, 20, 30, 40, 60]])


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


res, v = run(a, b, slip, min_vol, scale, cap_pct)
panel, trades = res["panel"], res["trades"]
hurdle = CostModel().breakeven_per_10g(panel["px10_a"].iloc[-1], res["grams"])

# ---- Header and verdict
st.title("Is this gold spread real, and tradable after costs?")
if source == "SYNTHETIC":
    st.warning("Synthetic data, for UI development only. Numbers below are not findings.")
st.markdown(f"<p class='lede'>{'Real MCX settlement' if source == 'MCX' else 'Synthetic'} data from "
            f"{df['date'].min():%-d %b %Y} to {df['date'].max():%-d %b %Y}, {len(df):,} contract-days. Every price is "
            "converted to rupees per 10 g at 999 purity, so the rulebook gaps are gone before we compare.</p>",
            unsafe_allow_html=True)

lots_a, lots_b = res["lots"]
hero, numbers = st.columns([1, 1.9], gap="large")
with hero:
    st.markdown(hallmark(v["verdict"], v["pair"], f"{lots_a} {a} against {lots_b} {b}, {res['grams']:.0f} g a side"),
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
    r1[1].metric("Net P&L", rupees(v.get("net_pnl", 0)), help="After statutory costs, brokerage and the slippage set in the sidebar.")
    sharpe = v.get("net_sharpe", float("nan"))
    r1[2].metric("Net Sharpe", "–" if pd.isna(sharpe) else f"{sharpe:.2f}",
                 help="Average net trade divided by its spread, scaled by how many trades a year the pair made.")
    r2[0].metric("Cost hurdle", rupees(hurdle), help="Statutory charges and brokerage for a round trip, per 10 g, before slippage.")
    r2[1].metric("Break-even", rupees(v.get("breakeven_slippage_per_leg", float("nan")), 1),
                 help="Slippage per 10 g per leg at which net P&L reaches zero. Negative means it loses even with perfect fills.")
    r2[2].metric("Gold beta", "–" if pd.isna(beta) else f"{beta:.2f}",
                 help="Slope of trade P&L on the gold move. Near 0 means the result is not just gold going up.")

# ---- Spread chart for one expiry
st.subheader("The spread, one contract at a time")
exps = sorted(panel["expiry"].unique())
expired = [x for x in exps if x <= panel["date"].max()]   # show a full life, through settlement
default_exp = expired[-1] if expired else exps[0]
exp = st.select_slider("Contract expiring in", exps, value=default_exp,
                       format_func=lambda d: pd.Timestamp(d).strftime("%b %Y"))
e = panel[panel["expiry"] == exp]
fig = go.Figure()
band = hurdle + 4 * slip
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
fig.update_layout(height=420, yaxis_title="₹ per 10 g at 999")
st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)
st.caption("The dark line is the price gap between the two contracts. The dashed line is where the exchange "
           "rules say it must end up; a trade is only worth taking once the gap leaves the shaded cost band.")

# ---- Sensitivity + regimes
l, r = st.columns(2, gap="large")
with l:
    st.subheader("What slippage does to it")
    sens = sensitivity(a, b, min_vol, scale, cap_pct)
    f2 = go.Figure(go.Bar(x=sens["slippage"], y=sens["net"], width=6,
                          marker_color=[VERDIGRIS if n > 0 else STEEL for n in sens["net"]],
                          marker_line=dict(color=[GOLD if s == slip else "rgba(0,0,0,0)" for s in sens["slippage"]], width=2.5),
                          hovertemplate="₹%{x} slippage: net ₹%{y:,.0f}<extra></extra>"))
    f2.add_hline(y=0, line=dict(color=INK, width=1))
    f2.update_layout(height=300, xaxis_title="Slippage, ₹ per 10 g per leg", yaxis_title="Net P&L, ₹",
                     xaxis=dict(tickvals=sens["slippage"]))
    st.plotly_chart(f2, width="stretch", config=PLOTLY_CONFIG)
    st.caption("Net profit if every fill costs this much extra. Green makes money, grey loses; "
               "the outlined bar is the slippage set in the sidebar.")
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
    r_res, r_v = run(pa, pb, slip, min_vol, 4 if pb == "GOLDPETAL" else 1, cap_pct)
    sig = latest_signals(r_res)
    top = sig.loc[(sig["residual"].abs() / sig["hurdle"]).idxmax()]
    status = ("Alert" if top["clears"] and r_v["verdict"] == "EDGE"
              else "Clears the hurdle, but the verdict is not EDGE" if top["clears"] else "Below the entry rules")
    rows.append({"Pair": f"{pa} vs {pb}", "Closest contract": top["expiry"].strftime("%b %Y"),
                 "Gap": rupees(top["residual"]), "Hurdle": rupees(top["hurdle"]), "Status": status})
alerts = pd.DataFrame(rows).set_index("Pair")
if (alerts["Status"] == "Alert").any():
    st.success("A pair with an EDGE verdict clears its cost hurdle today.")
else:
    st.markdown(f"No alerts on {df['date'].max():%-d %b %Y}. AuLens only alerts when a pair's verdict is EDGE "
                "**and** the gap clears costs, slippage and the entry rules, so silence is the normal state.")
st.table(alerts)
st.caption("Gap and hurdle are ₹ per 10 g for the contract closest to its hurdle. Entry rules also need a large "
           "enough z-score, enough volume and enough days before the delivery window.")

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
