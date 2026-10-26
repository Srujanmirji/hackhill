"""Visual system for the dashboard: "Assay certificate". Tokens mirror .streamlit/config.toml."""
from html import escape

import plotly.graph_objects as go
import plotly.io as pio

INK = "#23262B"        # touchstone: text, spread line
GOLD = "#B07A1E"       # fine gold: entries, holdable window
GOLD_TEXT = "#8A5D12"  # gold that passes 4.5:1 on paper, for small text
STEEL = "#5B6470"      # hallmark steel: secondary text, NO EDGE
VERDIGRIS = "#2E7D6B"  # expected spread, EDGE, exits
FAULT = "#B23A2E"      # regime breaks, tender window
PAPER = "#F6F7F5"
RULE = "#D5D9D3"

VERDICT_COLOUR = {"EDGE": VERDIGRIS, "NO EDGE": STEEL, "UNTESTABLE": GOLD_TEXT}

PLOTLY_CONFIG = {"displayModeBar": False}  # hover-only toolbar; drag zooms, double-click resets

pio.templates["assay"] = go.layout.Template(layout=go.Layout(
    font=dict(family="Public Sans, sans-serif", size=13, color=INK),
    paper_bgcolor=PAPER, plot_bgcolor=PAPER,
    colorway=[INK, GOLD, VERDIGRIS, STEEL, FAULT],
    xaxis=dict(showgrid=False, linecolor=RULE, ticks="outside", tickcolor=RULE, zeroline=False),
    yaxis=dict(gridcolor=RULE, gridwidth=1, zeroline=False, linecolor=RULE, tickformat=",~r"),
    hoverlabel=dict(bgcolor="white", bordercolor=RULE, font=dict(family="Public Sans", color=INK)),
    legend=dict(orientation="h", y=-0.18, x=0, title=None, font=dict(size=12, color=STEEL)),
    margin=dict(l=8, r=8, t=8, b=8),
))
pio.templates.default = "assay"

CSS = f"""
<style>
  /* tabular figures everywhere numbers line up */
  [data-testid="stMetricValue"], [data-testid="stTable"] td, .ledger {{ font-variant-numeric: tabular-nums; }}
  [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{ font-family: "Barlow Condensed", sans-serif !important;
    font-weight: 600; font-size: 2.1rem; line-height: 1.1; }}
  [data-testid="stMetricLabel"] p {{ color: {STEEL}; font-size: .85rem; }}
  [data-testid="stCaptionContainer"] p {{ color: {STEEL}; max-width: 72ch; }}
  .block-container {{ padding-top: 2.5rem; max-width: 1180px; }}
  h1 {{ font-size: 2.6rem !important; line-height: 1.05 !important; letter-spacing: -.01em; max-width: 30ch; }}
  .lede {{ color: {STEEL}; margin: .25rem 0 1.75rem; max-width: 62ch; }}

  /* the signature: verdict as a punched hallmark */
  .hallmark {{ display: inline-flex; flex-direction: column; align-items: center; justify-content: center;
    min-width: 13rem; padding: 1.1rem 1.6rem 1rem; border: 3px solid var(--mark);
    outline: 1.5px solid var(--mark); outline-offset: 4px; border-radius: 6px; color: var(--mark);
    background: color-mix(in srgb, var(--mark) 5%, white); }}
  .hallmark .v {{ font-family: "Barlow Condensed", sans-serif; font-weight: 700; font-size: 2.6rem;
    line-height: 1; letter-spacing: .04em; }}
  .hallmark .p {{ font-size: .8rem; margin-top: .45rem; color: {INK}; text-align: center; }}
  .reason {{ margin-top: 1.4rem; max-width: 46ch; }}
  section[data-testid="stSidebar"] h2 {{ font-size: 1.35rem; }}
  h3 {{ margin-top: 1.5rem !important; }}
  /* slider value labels default to primary gold (3.4:1); use the text-safe gold */
  [data-testid="stSliderThumbValue"], [data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] {{ color: {GOLD_TEXT} !important; }}

  /* phones: keep the six key numbers three across instead of one per row */
  @media (max-width: 640px) {{
    [data-testid="stColumn"] [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .75rem; }}
    [data-testid="stColumn"] [data-testid="stColumn"] {{ min-width: 0 !important; flex: 1 1 0 !important; }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {{ font-size: 1.55rem !important; }}
    [data-testid="stMetricLabel"] p {{ font-size: .75rem; }}
    h1 {{ font-size: 2.1rem !important; }}
  }}
</style>
"""


def hallmark(verdict: str, pair: str, lots: str) -> str:
    return (f"<div class='hallmark' role='img' aria-label='Verdict: {escape(verdict)} for {escape(pair)}' "
            f"style='--mark:{VERDICT_COLOUR[verdict]}'><span class='v'>{escape(verdict)}</span>"
            f"<span class='p'>{escape(lots)}</span></div>")


def rupees(x: float, decimals: int = 0) -> str:
    """₹ with a true minus sign: −₹25,726 rather than ₹-25,726."""
    s = f"₹{abs(x):,.{decimals}f}"
    return f"−{s}" if x < 0 else s
