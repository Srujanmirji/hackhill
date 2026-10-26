"""Capture real AuLens UI regions at 2x for the demo video."""
import json, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
JS_BOXES = """() => {
  const r = e => { const b = e.getBoundingClientRect(); return [b.x, b.y + window.scrollY, b.width, b.height]; };
  const h = [...document.querySelectorAll('h1, h3')];
  const head = t => h.find(x => x.innerText.trim().startsWith(t));
  const plots = [...document.querySelectorAll('.js-plotly-plot')];
  const tables = [...document.querySelectorAll('[data-testid="stTable"]')];
  return {
    sidebar: r(document.querySelector('section[data-testid="stSidebar"]')),
    title: r(head('Is this gold')), lede: r(document.querySelector('.lede')),
    stamp: r(document.querySelector('.hallmark')), reason: r(document.querySelector('.reason')),
    metrics: (() => { const m = [...document.querySelectorAll('[data-testid="stMetric"]')].map(r);
      const x0 = Math.min(...m.map(b => b[0])), y0 = Math.min(...m.map(b => b[1]));
      return [x0, y0, Math.max(...m.map(b => b[0] + b[2])) - x0, Math.max(...m.map(b => b[1] + b[3])) - y0]; })(),
    h_spread: r(head('The spread')), spread: r(plots[0]), slippage: r(plots[1]), carry: r(plots[2]), calendar: r(plots[3]),
    h_regime: r(head('Results by regime')), regime: r(tables[0]), h_alerts: r(head('Quiet alerts')), alerts: r(tables[1]),
  };
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for i, tag in enumerate(["control", "petal", "goldm"]):
        pg = b.new_page(viewport={"width": 1920, "height": 4600}, device_scale_factor=2)
        pg.goto("http://localhost:8502")
        pg.wait_for_function("document.querySelectorAll('.js-plotly-plot').length >= 4", timeout=90000)
        if i:
            pg.get_by_text(["GOLDTEN vs GOLDGUINEA", "GOLDTEN vs GOLDPETAL", "GOLDM vs GOLDTEN"][i], exact=False).first.click()
            pg.wait_for_timeout(4000)
            pg.wait_for_function("document.querySelectorAll('.js-plotly-plot').length >= 4", timeout=90000)
        pg.wait_for_timeout(2500)
        boxes = pg.evaluate(JS_BOXES)
        full = OUT / f"full_{tag}.png"; pg.screenshot(path=str(full), full_page=False)
        im = Image.open(full)
        pad = 24
        crops = {"hero": ("stamp", "metrics"), "title": ("title", "lede")} if tag != "control" else {
            "hero": ("stamp", "metrics"), "title": ("title", "lede"), "sidebar": ("sidebar",), "spread": ("h_spread", "spread"),
            "slippage": ("slippage",), "regime": ("h_regime", "regime"), "carry": ("carry",), "alerts": ("h_alerts", "alerts"),
            "calendar": ("calendar",)}
        meta = {}
        for name, keys in crops.items():
            bx = [boxes[k] for k in keys] + ([boxes["reason"]] if name == "hero" else [])
            x0 = min(b_[0] for b_ in bx) - pad; y0 = min(b_[1] for b_ in bx) - pad
            x1 = max(b_[0] + b_[2] for b_ in bx) + pad; y1 = max(b_[1] + b_[3] for b_ in bx) + pad
            box = tuple(int(v * 2) for v in (max(x0, 0), max(y0, 0), x1, y1))
            im.crop(box).save(OUT / f"{name}_{tag}.png"); meta[name] = [v // 2 for v in box]
        print(tag, json.dumps(meta))
        pg.close()
    b.close()
