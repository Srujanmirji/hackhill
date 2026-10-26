"""AuLens walkthrough film: deck slides + live app, narrated. Writes index.html and compositions/*.html.

Run from walkthrough/: python3 scripts/build.py
Inputs: assets/vo/scenes.json (voice timing per line), assets/vo/transcript.json (word starts),
        assets/deck/slide-NN.png (deck at 2x), assets/app/tile*.png + marks.json (app capture at 2x).
Every cue is a word start from the voice; edit copy in assets/vo/script.json, re-run scripts/voice.py, then this.
"""
import difflib
import json
import re
from pathlib import Path

P = Path(".")
VO = json.loads((P / "assets/vo/scenes.json").read_text())
TR = json.loads((P / "assets/vo/transcript.json").read_text())
TR = TR["words"] if isinstance(TR, dict) else TR
APP = json.loads((P / "assets/app/marks.json").read_text())
RECT = APP["@rects"]
TOTAL = round(VO[-1]["start"] + VO[-1]["duration"], 3)
INK, GOLD, STEEL, PAPER = "#23262B", "#B07A1E", "#5B6470", "#F6F7F5"
URL = "hackhill-wikhjmugah4iqupyf4nlh4.streamlit.app"

# Plate: where a slide or the browser window sits; the band under it holds captions.
PX, PY, PW, PH = 160, 28, 1600, 900

# ---------- word timings: script words, voice timing ----------
script_words = [(s["id"], w) for s in VO for w in s["text"].split()]
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())  # noqa: E731
sm = difflib.SequenceMatcher(a=[norm(w["text"]) for w in TR], b=[norm(w) for _, w in script_words], autojunk=False)
times = [None] * len(script_words)
for op, a0, a1, b0, b1 in sm.get_opcodes():
    if op == "equal":
        for k in range(b1 - b0):
            times[b0 + k] = (TR[a0 + k]["start"], TR[a0 + k]["end"])
    elif b1 > b0:
        s, e = (TR[a0]["start"], TR[a1 - 1]["end"]) if a1 > a0 else (times[b0 - 1][1], times[b0 - 1][1] + 0.3)
        st = (e - s) / (b1 - b0)
        for k in range(b1 - b0):
            times[b0 + k] = (s + k * st, s + (k + 1) * st)
WORDS = [{"vo": sid, "text": w, "start": round(t[0], 3), "end": round(t[1], 3)} for (sid, w), t in zip(script_words, times)]
VOS = {s["id"]: s for s in VO}


def cue(vo, word, nth=1):
    hits = [w for w in WORDS if w["vo"] == vo and norm(w["text"]).startswith(norm(word))]
    return hits[nth - 1]["start"]


FONTS = """
@font-face { font-family: 'Barlow Condensed'; font-weight: 600; src: url('assets/fonts/BarlowCondensed-SemiBold.woff2'); }
@font-face { font-family: 'Public Sans'; font-weight: 400; src: url('assets/fonts/PublicSans-Regular.woff2'); }
@font-face { font-family: 'Public Sans'; font-weight: 600; src: url('assets/fonts/PublicSans-SemiBold.woff2'); }
"""
BASE_CSS = FONTS + f"""
#root {{ position: absolute; inset: 0; background: {PAPER}; font-family: 'Public Sans', sans-serif; color: {INK}; overflow: hidden; }}
.cam {{ position: absolute; inset: 0; transform-origin: 0 0; }}
.frame {{ position: absolute; left: {PX}px; top: {PY}px; width: {PW}px; height: {PH}px; border-radius: 8px; overflow: hidden;
          box-shadow: 0 18px 40px rgba(35,38,43,0.14), 0 1px 0 rgba(35,38,43,0.06); }}
.plate {{ position: absolute; left: 0; top: 0; width: {PW}px; height: {PH}px; overflow: hidden; background: #fff; }}
.plate > img {{ display: block; width: 100%; height: 100%; }}
.mark {{ position: absolute; border: 4px solid {GOLD}; border-radius: 6px; opacity: 0; }}
"""
SFX = []   # (global time, file, volume)


class Scene:
    def __init__(self, hid, vos, extra=""):
        self.h, self.vos = hid, vos
        self.t0 = VOS[vos[0]]["start"]
        self.dur = round(sum(VOS[v]["duration"] for v in vos), 3)
        self.body, self.js, self.css, self.n = [], [], extra, 0

    def L(self, t):
        return round(t - self.t0, 3)

    def nid(self, kind):
        self.n += 1
        return f"{self.h}-{kind}{self.n}"

    def tw(self, line):
        self.js.append("    " + line)

    def sfx(self, t_local, file, vol):
        SFX.append((round(self.t0 + t_local, 3), file, vol))

    def enter(self, sel):
        self.tw(f'tl.fromTo("{sel}", {{ clipPath: "inset(0 100% 0 0 round 8px)" }}, '
                f'{{ clipPath: "inset(0 0% 0 0 round 8px)", duration: 0.55, ease: "expo.out" }}, 0);')
        self.sfx(0, "whoosh-short", 0.3)

    def write(self, html):
        js = "\n".join(self.js)
        Path(P / f"compositions/{self.h}.html").write_text(f"""<template>
  <style>{BASE_CSS}{self.css}</style>
  <div id="root" data-composition-id="{self.h}" data-width="1920" data-height="1080">
{html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{self.h}"] = tl;
  </script>
</template>
""")


# ---------- slide scenes: camera fits a region of the slide into the plate ----------
def fit(r):
    """Camera (x, y, scale) that shows slide region r = (x0, y0, x1, y1) in fractions, centred in the plate."""
    x0, y0, x1, y1 = r
    z = round(min(1 / (x1 - x0), 1 / (y1 - y0), 2.6), 3)
    cx, cy = (x0 + x1) / 2 * PW, (y0 + y1) / 2 * PH
    return round(PW / 2 - cx * z, 1), round(PH / 2 - cy * z, 1), z


FULL = (0, 0, 1, 1)


def slide_scene(hid, vos, slide, moves, extra_html="", extra_css=""):
    """moves: [(vo, word, region)] -- at that word the camera glides to that region."""
    s = Scene(hid, vos, extra_css)
    cam = f"#{hid}-cam"
    s.tw(f'gsap.set("{cam}", {{ x: 0, y: 0, scale: 1 }});')
    s.enter(f"#{hid}-frame")
    for vo, word, region in moves:
        x, y, z = fit(region)
        at = s.L(cue(vo, word)) - 0.15
        s.tw(f'tl.to("{cam}", {{ x: {x}, y: {y}, scale: {z}, duration: 1.1, ease: "power3.inOut" }}, {max(at, 0.6):.3f});')
    s.write(f"""    <div id="{hid}-frame" class="frame"><div id="{hid}-cam" class="cam">
      <div id="{hid}-plate" class="plate" data-hold="true"><img src="assets/deck/{slide}.png" alt=""></div>
    </div></div>
{extra_html}""")
    return s


# ---------- the app demo: one long page scrolled inside a browser window ----------
BAR = 46                              # browser bar height
VW, VH = PW, PH - BAR                 # viewport in film px
CSS_W, CSS_H = 1600, APP["@height"]   # captured page in CSS px
TILE_CSS = APP["@tile_px"] // 2
S1 = round(PW / 1100, 4)              # film px per CSS px at zoom 1: content column (1030) + margins fills the window
CX = RECT["main"][0] + RECT["main"][2] / 2   # content column centre, CSS px


def view_top(top, z=1.0):
    s = S1 * z
    return round(VW / 2 - CX * s, 1), round(-top * s, 1), round(s, 4)


def view_at(cx, cy, z):
    s = S1 * z
    return round(VW / 2 - cx * s, 1), round(VH / 2 - cy * s, 1), round(s, 4)


def demo_scene():
    vos = ["v06", "v07", "v08", "v09", "v10", "v12"]
    s = Scene("demo", vos, f"""
.win {{ position: absolute; left: {PX}px; top: {PY}px; width: {PW}px; height: {PH}px; border-radius: 10px; overflow: hidden;
        background: #fff; box-shadow: 0 22px 48px rgba(35,38,43,0.18), 0 1px 0 rgba(35,38,43,0.08); }}
.bar {{ position: absolute; left: 0; top: 0; right: 0; height: {BAR}px; background: #ECEEEA; border-bottom: 1px solid #D9DCD6;
        display: flex; align-items: center; gap: 9px; padding-left: 18px; }}
.dot {{ width: 12px; height: 12px; border-radius: 50%; background: #C9CDC6; }}
.url {{ margin-left: 22px; height: 30px; padding: 0 16px; border-radius: 15px; background: #fff; display: flex; align-items: center;
        font-size: 17px; color: {STEEL}; letter-spacing: 0.01em; }}
.url b {{ color: {INK}; font-weight: 600; }}
.live {{ margin-left: auto; margin-right: 18px; font-size: 15px; font-weight: 600; color: #1F5F50; letter-spacing: 0.06em; }}
.vp {{ position: absolute; left: 0; top: {BAR}px; width: {VW}px; height: {VH}px; overflow: hidden; background: #fff; }}
.page {{ position: absolute; left: 0; top: 0; width: {CSS_W}px; height: {CSS_H}px; transform-origin: 0 0; }}
.page img {{ position: absolute; left: 0; width: {CSS_W}px; display: block; }}
.page .mark {{ border-width: 3px; }}
""")
    tiles = "\n".join(
        f'          <img src="assets/app/tile{i:02d}.png" style="top:{i * TILE_CSS}px; height:{min(TILE_CSS, CSS_H - i * TILE_CSS)}px;" alt="">'
        for i in range(APP["@tiles"]))
    marks = []

    def mark(key, r, at, until, pad=8):
        mid = f"demo-m-{key}"
        x, y, w, h = r
        marks.append(f'          <div id="{mid}" class="mark" style="left:{x - pad}px; top:{y - pad}px; width:{w + 2 * pad}px; height:{h + 2 * pad}px;"></div>')
        s.tw(f'tl.fromTo("#{mid}", {{ opacity: 0, scale: 1.04 }}, {{ opacity: 1, scale: 1, duration: 0.27, ease: "power3.out" }}, {s.L(at):.3f});')
        s.tw(f'tl.to("#{mid}", {{ opacity: 0, duration: 0.2, ease: "power2.in" }}, {s.L(until):.3f});')
        s.sfx(s.L(at), "click-soft", 0.3)

    def go(at, view, dur=1.3):
        x, y, sc = view
        s.tw(f'tl.to("#demo-page", {{ x: {x}, y: {y}, scale: {sc}, duration: {dur}, ease: "power2.inOut" }}, {max(s.L(at) - 0.2, 0.5):.3f});')

    x, y, sc = view_top(30)
    s.tw(f'gsap.set("#demo-page", {{ x: {x}, y: {y}, scale: {sc} }});')
    s.tw('tl.fromTo("#demo-win", { clipPath: "inset(0 100% 0 0 round 10px)" }, '
         '{ clipPath: "inset(0 0% 0 0 round 10px)", duration: 0.6, ease: "expo.out" }, 0);')
    s.sfx(0, "whoosh-short", 0.3)
    end = lambda v: VOS[v]["start"] + VOS[v]["duration"] - 0.3  # noqa: E731

    # v06 scoreboard
    go(cue("v06", "scoreboard"), view_top(RECT["board"][1] - 40))
    mark("board", RECT["board_h"], cue("v06", "Zero"), end("v06"))
    # v07 pick a pair -> verdict
    go(cue("v07", "Take"), view_top(RECT["pills"][1] - 30))
    mark("pills", RECT["pills"], cue("v07", "Take"), cue("v07", "sixty-two"))
    mark("metrics", RECT["metrics"], cue("v07", "sixty-two"), cue("v07", "No"))
    mark("stamp", RECT["stamp"], cue("v07", "No"), end("v07"))
    # v08 spread chart, then punch into the latest expiries at "within one rupee"
    sp = RECT["spread"]
    go(cue("v08", "The"), view_top(sp[1] - 150))
    go(cue("v08", "eighteen"), view_at(sp[0] + sp[2] * 0.72, sp[1] + sp[3] * 0.5, 1.3), 1.2)
    # v09 check a gap
    go(cue("v09", "Check"), view_top(RECT["ledger"][1] - 200), 1.3)
    mark("leftover", RECT["leftover"], cue("v09", "shows"), cue("v09", "costs"))
    mark("gapout", RECT["gapout"], cue("v09", "costs"), end("v09"))
    # v10 slippage + regimes
    reg = RECT["tables"][2]
    go(cue("v10", "Results"), view_top(RECT["slip"][1] - 70))
    mark("slip", RECT["slip"], cue("v10", "slippage"), cue("v10", "split"))
    mark("regime", reg, cue("v10", "split"), end("v10"))
    # v12 alerts
    al = RECT["tables"][3]
    go(cue("v12", "Alerts"), view_top(al[1] - 140))
    mark("alerts", al, cue("v12", "none"), end("v12"))

    s.write(f"""    <div id="demo-win" class="win">
      <div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span>
        <span class="url">https://<b>{URL}</b></span><span class="live">LIVE APP · REAL MCX DATA</span></div>
      <div class="vp">
        <div id="demo-page" class="page">
{tiles}
{chr(10).join(marks)}
        </div>
      </div>
    </div>""")
    return s


# ---------- limits card over the results slide (v16), wording from docs/VALIDATION.md ----------
LIMITS = [("Simulated fills", "from next settlement prices, plus assumed slippage"),
          ("Costs are modelled", "margin and funding costs are excluded"),
          ("No untouched holdout", "the history was already inspected while building"),
          ("NO EDGE", "means none was established under these assumptions")]


def results_scene():
    css = f"""
.lim {{ position: absolute; left: 1080px; top: 150px; width: 640px; background: #fff; border-radius: 8px; padding: 40px 44px 36px;
        border-left: 6px solid {GOLD}; box-shadow: 0 22px 48px rgba(35,38,43,0.18); opacity: 0; }}
.lim h2 {{ font-family: 'Barlow Condensed'; font-weight: 600; font-size: 54px; letter-spacing: -0.01em; margin-bottom: 26px; }}
.lim .row {{ margin-top: 22px; opacity: 0; }}
.lim .row b {{ display: block; font-size: 30px; font-weight: 600; }}
.lim .row span {{ display: block; font-size: 28px; color: {STEEL}; margin-top: 4px; line-height: 1.3; }}
"""
    rows = "\n".join(f'        <div id="results-r{i}" class="row"><b>{a}</b><span>{b}</span></div>' for i, (a, b) in enumerate(LIMITS))
    card = f"""    <div id="results-lim" class="lim">
      <h2>What this test does not claim</h2>
{rows}
    </div>"""
    s = slide_scene("results", ["v15", "v16"], "slide-06",
                    [("v15", "about", (0.03, 0.25, 0.51, 0.69)), ("v15", "fails", (0.0, 0.0, 1.0, 1.0))], card, css)
    # the slide steps left to make room; the card prints row by row as the voice names each limit
    t = s.L(cue("v16", "Limits"))
    s.tw(f'tl.to("#results-frame", {{ x: -100, y: 272, scale: 0.52, transformOrigin: "0 0", duration: 1.0, ease: "power3.inOut" }}, {t + 0.05:.3f});')
    s.tw(f'tl.fromTo("#results-lim", {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out" }}, {t + 0.3:.3f});')
    for i, w in enumerate(["fills", "funding", "untouched", "untouched"]):
        at = s.L(cue("v16", w)) - 0.1 + (0.45 if i == 3 else 0)
        s.tw(f'tl.fromTo("#results-r{i}", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }}, {max(at, t + 0.6):.3f});')
        s.sfx(max(at, t + 0.6), "click-soft", 0.25)
    # rewrite with the extra tweens (slide_scene already wrote once)
    s.write(f"""    <div id="results-frame" class="frame"><div id="results-cam" class="cam">
      <div id="results-plate" class="plate" data-hold="true"><img src="assets/deck/slide-06.png" alt=""></div>
    </div></div>
{card}""")
    return s


# ---------- captions: phrase groups on a paper band under the plate ----------
def captions():
    groups, cur = [], []
    for w in WORDS:
        cur.append(w)
        if len(cur) >= 8 or re.search(r"[.,:;?!]$", w["text"]) and len(cur) >= 4 or w is WORDS[-1] or \
                (WORDS.index(w) + 1 < len(WORDS) and WORDS[WORDS.index(w) + 1]["vo"] != w["vo"]):
            groups.append(cur); cur = []
    out, js = [], []
    for i, g in enumerate(groups):
        start = g[0]["start"] - 0.05
        nxt = groups[i + 1][0]["start"] - 0.05 if i + 1 < len(groups) else g[-1]["end"] + 0.6
        end = min(nxt, g[-1]["end"] + 0.9)
        text = " ".join(w["text"] for w in g)
        out.append(f'    <div id="cap{i}" class="clip cap" data-start="{start:.3f}" data-duration="{end - start:.3f}">'
                   f'<span>{text}</span></div>')
    Path(P / "compositions/captions.html").write_text(f"""<template>
  <style>{FONTS}
#root {{ position: absolute; inset: 0; pointer-events: none; }}
.cap {{ position: absolute; left: {PX}px; right: {1920 - PX - PW}px; top: {PY + PH + 30}px; height: 92px; display: flex; align-items: center; }}
.cap span {{ background: {PAPER}; padding: 8px 18px 10px; border-radius: 6px; font-family: 'Public Sans', sans-serif; font-weight: 600;
             font-size: 38px; line-height: 1.2; color: {INK}; white-space: nowrap; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
{chr(10).join(out)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    window.__timelines["captions"] = tl;
  </script>
</template>
""")


scenes = [
    slide_scene("team", ["v01"], "slide-01", [("v01", "CodeWick", (0.0, 0.40, 1.0, 0.86)), ("v01", "powered", FULL)]),
    slide_scene("problem", ["v02", "v03"], "slide-02",
                [("v02", "A", (0.03, 0.46, 0.51, 0.97)), ("v03", "Quote", (0.505, 0.26, 0.975, 0.6))]),
    slide_scene("solution", ["v04"], "slide-03", [("v04", "converts", (0.02, 0.66, 0.52, 0.96)), ("v04", "One", FULL)]),
    slide_scene("prototype", ["v05"], "slide-04", [("v05", "live", (0.02, 0.3, 0.5, 0.67)), ("v05", "eighteen", (0.02, 0.1, 0.98, 0.34))]),
    demo_scene(),
    slide_scene("architecture", ["v14"], "slide-05",
                [("v14", "MCX", (0.02, 0.29, 0.42, 0.8)), ("v14", "rule", (0.33, 0.29, 0.83, 0.8)), ("v14", "monthly", (0.55, 0.29, 0.99, 0.8)),
                 ("v14", "Python", (0.02, 0.8, 0.99, 0.99))]),
    results_scene(),
    slide_scene("innovation", ["v17"], "slide-07", [("v17", "AuLens", (0.02, 0.26, 0.98, 0.7))]),
    slide_scene("market", ["v18"], "slide-08",
                [("v18", "free", (0.02, 0.5, 0.98, 0.98))]),
    slide_scene("roadmap", ["v19"], "slide-09", [("v19", "live", (0.5, 0.64, 0.99, 0.99))]),
    slide_scene("end", ["v20"], "slide-10", [("v20", "open", (0.3, 0.56, 0.86, 0.99))]),
]
captions()

hosts = []
for k, s in enumerate(scenes):
    dur = s.dur if k + 1 < len(scenes) else round(TOTAL - s.t0, 3)
    hosts.append(f'      <div id="{s.h}" class="clip" data-composition-id="{s.h}" data-composition-src="compositions/{s.h}.html" '
                 f'data-start="{s.t0}" data-duration="{dur}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>')
DUR = {"whoosh-short": 0.57, "click-soft": 0.37}
sfx = [f'      <audio id="sfx{i}" src="assets/sfx/{f}.mp3" data-start="{t:.3f}" data-duration="{DUR[f]}" data-track-index="{4 + i % 2}" data-volume="{v}"></audio>'
       for i, (t, f, v) in enumerate(sorted(SFX))]
(P / "index.html").write_text(f"""<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: {PAPER}; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
      #captions {{ z-index: 10; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
      <div id="captions" class="clip" data-composition-id="captions" data-composition-src="compositions/captions.html"
        data-start="0" data-duration="{TOTAL}" data-track-index="2" data-track-kind="captions" data-width="1920" data-height="1080"></div>
      <audio id="vo" src="assets/vo/voiceover.wav" data-start="0" data-duration="{TOTAL - 0.45:.3f}" data-track-index="3" data-volume="1"></audio>
{chr(10).join(sfx)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
print(f"{len(scenes)} scenes, {len(SFX)} sfx, {TOTAL}s")
