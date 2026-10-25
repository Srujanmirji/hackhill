"""AuLens dashboard:  streamlit run app/streamlit_app.py"""
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aulens.backtest import Params, walk_forward  # noqa: E402
from aulens.costs import CostModel  # noqa: E402
from aulens.data.loader import load_processed  # noqa: E402
from aulens.specs import PAIRS, REGIME_BREAKS, SPECS  # noqa: E402
from aulens.verdict import verdict  # noqa: E402

GOLD, DARK, GREEN, GREY, RED = "#B07A1E", "#1D1D1F", "#2E7D55", "#5F6368", "#C0392B"
st.set_page_config(page_title="AuLens", page_icon="🔎", layout="wide")


@st.cache_data
def data():
    return load_processed()


df = data()
source = df["source"].iloc[0]

st.title("AuLens — is this gold spread real, and tradable after costs?")
if source == "SYNTHETIC":
    st.warning("SYNTHETIC DATA — for UI development only. Numbers below are not findings.")
st.caption(f"Source: {source} · {df['date'].min():%d %b %Y} → {df['date'].max():%d %b %Y} · "
           f"{len(df):,} contract-days")

with st.sidebar:
    st.header("Pair")
    labels = [f"{a} vs {b}" + ("  (control pair)" if i == 0 else "") for i, (a, b) in enumerate(PAIRS)]
    a, b = PAIRS[st.radio("Pair", range(len(PAIRS)), format_func=lambda i: labels[i])]
    st.header("Assumptions")
    slip = st.slider("Slippage, ₹ per 10 g per leg", 0, 60, 20, 5,
                     help="Bhavcopy has no order-book depth, so this is an assumption. See the sensitivity chart.")
    min_vol = st.slider("Minimum daily volume (lots, both legs)", 0, 500, 50, 10)
    scale = st.select_slider("Size multiplier", [1, 2, 4, 8], 4 if b == "GOLDPETAL" else 1)
    st.header("Contract rules")
    st.dataframe(pd.DataFrame([{"Contract": s.symbol, "Unit g": s.lot_grams, "Quote g": s.quote_grams,
                                "Purity": s.purity, "DDR city": s.settle_city}
                               for s in SPECS.values() if s.symbol in (a, b)]), hide_index=True)


@st.cache_data
def run(a, b, slip, min_vol, scale):
    prm = Params(slippage_per_leg=slip, min_volume=min_vol, lot_scale=scale)
    res = walk_forward(df, a, b, prm)
    return res, verdict(res)


res, v = run(a, b, slip, min_vol, scale)
panel, trades = res["panel"], res["trades"]

# ---- Verdict card
colour = {"EDGE": GREEN, "NO EDGE": GREY, "UNTESTABLE": GOLD}[v["verdict"]]
st.markdown(
    f"<div style='padding:18px 22px;border-radius:14px;background:{colour}18;border:1px solid {colour}55'>"
    f"<span style='background:{colour};color:white;padding:4px 14px;border-radius:999px;font-weight:700'>"
    f"{v['verdict']}</span>&nbsp;&nbsp;<b>{v['pair']}</b> · {v['lots']}<br>"
    f"<span style='color:{DARK}'>{v['reason']}</span></div>", unsafe_allow_html=True)

hurdle = CostModel().breakeven_per_10g(panel["px10_a"].iloc[-1], res["grams"])
c = st.columns(5)
c[0].metric("Trades (walk-forward)", v["trades"])
c[1].metric("Net P&L", f"₹{v.get('net_pnl', 0):,.0f}")
c[2].metric("Hit rate", f"{v.get('hit_rate', 0):.0%}")
c[3].metric("Cost hurdle", f"₹{hurdle:,.0f} / 10 g", help="Statutory + brokerage round trip, before slippage")
c[4].metric("Break-even slippage", f"₹{v.get('breakeven_slippage_per_leg', float('nan')):,.1f}",
            help="Slippage per 10 g per leg at which net P&L reaches zero")

# ---- Spread chart for one expiry
st.subheader("Normalized spread vs expected convergence")
exps = sorted(panel["expiry"].unique())
default_exp = (trades["expiry"].value_counts().idxmax() if len(trades) else exps[len(exps) // 2])
exp = st.select_slider("Contract expiry", exps, value=default_exp,
                       format_func=lambda d: pd.Timestamp(d).strftime("%b %Y"))
e = panel[panel["expiry"] == exp]
fig = go.Figure()
band = hurdle + 4 * slip
fig.add_trace(go.Scatter(x=e["date"], y=e["expected"] + band, line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=e["date"], y=e["expected"] - band, fill="tonexty", fillcolor="rgba(46,125,85,0.12)",
                         line=dict(width=0), name="cost + slippage hurdle"))
fig.add_trace(go.Scatter(x=e["date"], y=e["expected"], name="expected (E)", line=dict(color=GREEN, dash="dash")))
fig.add_trace(go.Scatter(x=e["date"], y=e["spread"], name="spread (S)", line=dict(color=DARK)))
et = trades[trades["expiry"] == exp] if len(trades) else trades
if len(et):
    m = e.set_index("date")["spread"]
    fig.add_trace(go.Scatter(x=et["entry_date"], y=m.reindex(et["entry_date"]).values, mode="markers",
                             marker=dict(color=GOLD, size=11), name="entry (T+1)"))
    fig.add_trace(go.Scatter(x=et["exit_date"], y=m.reindex(et["exit_date"]).values, mode="markers",
                             marker=dict(color=GREEN, size=11, symbol="x"), name="exit"))
for d, label in REGIME_BREAKS.items():
    if e["date"].min() <= pd.Timestamp(d) <= e["date"].max():
        fig.add_vline(x=pd.Timestamp(d), line=dict(color=RED, dash="dot"))
fig.update_layout(height=420, yaxis_title="₹ per 10 g @ 999", margin=dict(l=10, r=10, t=10, b=10),
                  legend=dict(orientation="h", y=-0.15))
st.plotly_chart(fig, use_container_width=True)

# ---- Sensitivity + regimes
l, r = st.columns(2)
with l:
    st.subheader("Slippage sensitivity")
    rows = []
    for s in [0, 10, 20, 30, 40, 60]:
        _, vv = run(a, b, s, min_vol, scale)
        rows.append({"slippage": s, "net": vv.get("net_pnl", 0)})
    sens = pd.DataFrame(rows)
    f2 = go.Figure(go.Bar(x=sens["slippage"], y=sens["net"],
                          marker_color=[GREEN if n > 0 else GREY for n in sens["net"]]))
    f2.update_layout(height=300, xaxis_title="₹ per 10 g per leg", yaxis_title="Net P&L ₹", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(f2, use_container_width=True)
with r:
    st.subheader("Results by regime")
    if "by_regime" in v:
        st.dataframe(v["by_regime"].rename(columns={"count": "Trades", "sum": "Net ₹"}).style.format({"Net ₹": "₹{:,.0f}"}))
        st.caption(f"Gold beta of trade P&L: {v['gold_beta']:.3f} (near 0 = gold-neutral)")
    else:
        st.info("No trades yet.")

with st.expander("Trade log"):
    st.dataframe(trades, hide_index=True)
with st.expander("How AuLens decides"):
    st.markdown(Path(__file__).resolve().parents[1].joinpath("docs", "METHODOLOGY.md").read_text())
