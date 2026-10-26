"""Build data/processed/gold_futures.parquet.

  python scripts/build_dataset.py --sample                 # synthetic data (dev only)
  python scripts/build_dataset.py --raw data/raw           # real CSV/XLSX/JSON downloads
  python scripts/build_dataset.py --endpoint "<url with {date}>" --start 2025-04-01 --end 2026-10-23
      (MCX answers 403 to scripts; use scripts/mcx_fetch_in_browser.js, see docs/MCX_DATA_API.md)
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aulens.data.loader import apply_ddr, tidy  # noqa: E402
from aulens.data.mcx_client import _rows_from_json, fetch_range  # noqa: E402
from aulens.data.sample import make_sample  # noqa: E402


def read_raw_dir(d: Path) -> pd.DataFrame:
    frames = []
    for f in sorted(d.rglob("*")):
        if "ddr" in f.parts:  # final settlement prices, applied separately
            continue
        if f.suffix.lower() == ".csv":
            frames.append(pd.read_csv(f))
        elif f.suffix.lower() in (".xls", ".xlsx"):
            frames.append(pd.read_excel(f))
        elif f.suffix.lower() == ".json":
            frames.append(pd.DataFrame(_rows_from_json(json.loads(f.read_text()))))
    if not frames:
        sys.exit(f"No CSV/XLSX/JSON files found in {d}")
    return pd.concat(frames, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sample", action="store_true")
    g.add_argument("--raw")
    g.add_argument("--endpoint")
    ap.add_argument("--start", default="2025-04-01")
    ap.add_argument("--end", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--out", default="data/processed/gold_futures.parquet")
    a = ap.parse_args()

    if a.sample:
        raw, source = make_sample(), "SYNTHETIC"
    elif a.raw:
        raw, source = read_raw_dir(Path(a.raw)), "MCX"
    else:
        raw, source = fetch_range(a.endpoint, a.start, a.end), "MCX"

    df = tidy(raw).assign(source=source)
    ddr_files = sorted(Path(a.raw).glob("ddr/*.csv")) if a.raw else []
    if ddr_files:
        df = apply_ddr(df, pd.concat(map(pd.read_csv, ddr_files), ignore_index=True))
        print(f"DDR applied to {(df['close'] != df['bhav_close']).sum()} expiry-day rows "
              f"({df['bhav_close'].ne(df['close']).groupby(df['symbol']).sum().to_dict()})")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(a.out, index=False)
    print(f"{source}: {len(df):,} rows, {df['date'].min():%d %b %Y} -> {df['date'].max():%d %b %Y}")
    print(df.groupby("symbol")["expiry"].nunique().rename("expiries").to_string())


if __name__ == "__main__":
    main()
