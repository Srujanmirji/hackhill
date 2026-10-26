"""Full-page 2x capture of the local AuLens app, sliced into tiles, plus section offsets (CSS px)."""
import json, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

Image.MAX_IMAGE_PIXELS = None
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8501"
TILE = 2000  # device px per tile

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
    pg.goto(URL)
    pg.wait_for_function("document.querySelectorAll('.js-plotly-plot').length >= 5", timeout=120000)
    pg.wait_for_timeout(4000)
    # Streamlit scrolls inside its own container; let the document grow so a full-page shot works.
    pg.add_style_tag(content="html,body,#root,[data-testid=stApp],[data-testid=stAppViewContainer],[data-testid=stMain]"
                             "{height:auto!important;overflow:visible!important;position:static!important}"
                             "header[data-testid=stHeader],[data-testid=stToolbar],[data-testid=stDecoration],"
                             "[data-testid=stStatusWidget]{display:none!important}")
    pg.wait_for_timeout(2500)
    marks = pg.evaluate("""() => { const o = {}; const y = e => Math.round(e.getBoundingClientRect().top + window.scrollY);
      document.querySelectorAll('h1,h2,h3').forEach(h => o[h.innerText.trim().slice(0, 40)] = y(h));
      const q = (k, s) => { const e = document.querySelector(s); if (e) o[k] = y(e); };
      q('@pills', '[data-testid=stButtonGroup]'); q('@stamp', '.hallmark'); q('@gap', '.gap');
      document.querySelectorAll('.js-plotly-plot').forEach((e, i) => o['@plot' + i] = y(e));
      o['@height'] = document.documentElement.scrollHeight;
      const R = e => { if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y + window.scrollY), Math.round(b.width), Math.round(b.height)]; };
      const H = t => [...document.querySelectorAll('h1,h2,h3')].find(h => h.innerText.trim().startsWith(t));
      const plots = [...document.querySelectorAll('.js-plotly-plot')];
      const tables = [...document.querySelectorAll('[data-testid=stTable], [data-testid=stDataFrame]')];
      const m = [...document.querySelectorAll('[data-testid=stMetric]')].map(R);
      o['@rects'] = { main: R(document.querySelector('[data-testid=stMainBlockContainer], .block-container')),
        title: R(document.querySelector('h1')), board_h: R(H('0 of 6')), board: R(H('0 of 6') && H('0 of 6').closest('[data-testid=stVerticalBlock]')),
        pills: R(document.querySelector('[data-testid=stButtonGroup]')), stamp: R(document.querySelector('.hallmark')),
        metrics: m.length ? [Math.min(...m.map(b=>b[0])), Math.min(...m.map(b=>b[1])), Math.max(...m.map(b=>b[0]+b[2]))-Math.min(...m.map(b=>b[0])), Math.max(...m.map(b=>b[1]+b[3]))-Math.min(...m.map(b=>b[1]))] : null,
        spread: R(plots[0]), ledger: R(document.querySelector('.gap-ledger')), leftover: R(document.querySelector('.gap-ledger .key')),
        gapout: R(document.querySelector('.gap-out')), slip: R(plots[1]), carry: R(plots[2]), roll: R(plots[3]), calendar: R(plots[4]), liquid: R(plots[5]),
        tables: tables.map(R) };
      return o; }""")
    full = OUT / "_full.png"
    pg.screenshot(path=str(full), full_page=True)
    b.close()

im = Image.open(full)
n = 0
for top in range(0, im.height, TILE):
    im.crop((0, top, im.width, min(top + TILE, im.height))).save(OUT / f"tile{n:02d}.png", optimize=True); n += 1
marks.update({"@tiles": n, "@tile_px": TILE, "@width_px": im.width, "@height_px": im.height})
(OUT / "marks.json").write_text(json.dumps(marks, indent=1))
print(json.dumps(marks, indent=1))
