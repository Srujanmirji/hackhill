"""Fetch MCX daily Bhavcopy.

The working route is `scripts/mcx_fetch_in_browser.js`, run in a real browser on an MCX page;
it writes the CSVs `scripts/build_dataset.py --raw data/raw` reads. Endpoint map:
docs/MCX_DATA_API.md.

`fetch_range` below calls the same JSON endpoint from Python. As of Oct 2026 MCX's Akamai
protection answers 403 to scripts, so expect it to fail; it is kept for networks where the
endpoint is reachable. URL template:
https://www.mcxindia.com/market-data/bhavcopy/GetDateWiseBhavCopy?InstrumentName=FUTCOM&fromDate={date}
(the endpoint also needs the `X-Requested-With: XMLHttpRequest` header).

The old `backpage.aspx` routes were retired in MCX's 2026 redesign; libraries built on
them (mcxlib, mcxpy) were reported broken in Sep 2026. Do not rely on them.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

from aulens.data.loader import assert_requested_date

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.mcxindia.com/market-data/bhavcopy",
    "Origin": "https://www.mcxindia.com",
}


def _rows_from_json(payload) -> list[dict]:
    """MCX wraps rows differently across versions; find the first list of dicts."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for v in payload.values():
            if isinstance(v, str):
                try:
                    v = json.loads(v)
                except ValueError:
                    continue
            rows = _rows_from_json(v)
            if rows:
                return rows
    return []


def fetch_day(url_template: str, day: pd.Timestamp, session: requests.Session,
              cache_dir: Path = Path("data/raw/json")) -> pd.DataFrame | None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"{day:%Y%m%d}.json"
    if cache.exists():
        payload = json.loads(cache.read_text())
    else:
        r = session.get(url_template.format(date=day.strftime("%d/%m/%Y")), headers=HEADERS, timeout=30)
        r.raise_for_status()
        payload = r.json()
        cache.write_text(json.dumps(payload))
    rows = _rows_from_json(payload)
    if not rows:
        return None
    raw = pd.DataFrame(rows)
    if "Date" in raw.columns and not assert_requested_date(raw, day):
        return None  # holiday / invalid date: MCX returned another day
    return raw


def fetch_range(url_template: str, start: str, end: str, pause: float = 0.5) -> pd.DataFrame:
    session = requests.Session()
    frames = []
    for day in pd.bdate_range(start, end):
        try:
            raw = fetch_day(url_template, day, session)
        except requests.RequestException as e:
            print(f"{day:%Y-%m-%d}: {e}")
            raw = None
        if raw is not None:
            frames.append(raw)
        time.sleep(pause)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
