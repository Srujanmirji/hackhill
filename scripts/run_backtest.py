"""Print the verdict for every pair:  python scripts/run_backtest.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aulens.backtest import Params, walk_forward  # noqa: E402
from aulens.data.loader import load_processed  # noqa: E402
from aulens.specs import PAIRS  # noqa: E402
from aulens.verdict import verdict  # noqa: E402

df = load_processed()
print(f"Data source: {df['source'].iloc[0]}\n")
for a, b in PAIRS:
    v = verdict(walk_forward(df, a, b, Params(lot_scale=4 if b == "GOLDPETAL" else 1)))
    print(f"== {v['pair']}  [{v['verdict']}]  {v['lots']}")
    print(f"   {v['reason']}")
    if "net_pnl" in v:
        print(f"   trades {v['trades']}  gross ₹{v['gross_pnl']:,.0f}  costs ₹{v['costs']:,.0f}  "
              f"slippage ₹{v['slippage']:,.0f}  net ₹{v['net_pnl']:,.0f}  hit {v['hit_rate']:.0%}")
        print(f"   break-even slippage ₹{v['breakeven_slippage_per_leg']:.1f}/10 g/leg   gold beta {v['gold_beta']:.3f}")
        print(v["by_regime"].to_string(), "\n")
