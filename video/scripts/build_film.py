"""AuLens demo film, motion pass. Generates index.html + compositions/*.html for HyperFrames.

Scenes: hook (s01+s02), spread (s03+s04), verdict, metrics, regimes, pairs, carry, alerts, end.
Every cue is a word start from the voice transcript (global seconds), converted to scene-local time.
"""
import difflib
import json
import re
import sys
from pathlib import Path

from PIL import Image

P = Path(sys.argv[1])
VO = json.loads((P / "assets/vo/scenes.json").read_text())
TR = json.loads((P / "assets/vo/transcript.json").read_text())
TR = TR["words"] if isinstance(TR, dict) else TR
TOTAL = round(VO[-1]["start"] + VO[-1]["duration"], 3)
INK, GOLD, GOLD_TXT, STEEL, PAPER = "#23262B", "#B07A1E", "#8A5D12", "#5B6470", "#F6F7F5"

# ---------- word timings (script words, voice timing) ----------
script_words = [(s["id"], w) for s in VO for w in s["text"].split()]
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
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


HOSTS = [("hook", ["s01", "s02"]), ("spread", ["s03", "s04"]), ("verdict", ["s05"]), ("metrics", ["s06"]),
         ("regimes", ["s07"]), ("pairs", ["s08"]), ("carry", ["s09"]), ("alerts", ["s10"]), ("end", ["s11"])]
HSTART = {h: VOS[v[0]]["start"] for h, v in HOSTS}
HDUR = {h: round(sum(VOS[x]["duration"] for x in v), 3) for h, v in HOSTS}
SFX = []   # (global time, file, volume)


def size(src):
    w, h = Image.open(P / src).size
    return w / 2, h / 2


BASE_CSS = f"""
@font-face {{ font-family: 'Barlow Condensed'; font-weight: 600; src: url('assets/fonts/BarlowCondensed-SemiBold.woff2'); }}
@font-face {{ font-family: 'Barlow Condensed'; font-weight: 700; src: url('assets/fonts/BarlowCondensed-Bold.woff2'); }}
@font-face {{ font-family: 'Public Sans'; font-weight: 400; src: url('assets/fonts/PublicSans-Regular.woff2'); }}
@font-face {{ font-family: 'Public Sans'; font-weight: 600; src: url('assets/fonts/PublicSans-SemiBold.woff2'); }}
#root {{ position: absolute; inset: 0; background: {PAPER}; font-family: 'Public Sans', sans-serif; color: {INK}; overflow: hidden; }}
.cam, .stage {{ position: absolute; inset: 0; }}
.plate {{ position: absolute; border-radius: 6px; overflow: hidden; background: #fff;
          box-shadow: 0 18px 40px rgba(35,38,43,0.14), 0 1px 0 rgba(35,38,43,0.06); }}
.plate img {{ display: block; width: 100%; height: 100%; }}
.mark {{ position: absolute; border: 4px solid {GOLD}; border-radius: 4px; opacity: 0; }}
.ring {{ position: absolute; border: 5px solid {STEEL}; border-radius: 14px; opacity: 0; }}
.lbl {{ position: absolute; font-family: 'Barlow Condensed'; font-weight: 600; color: {INK}; white-space: nowrap; }}
.lbl b {{ color: {GOLD_TXT}; font-weight: 700; }}
.lead {{ position: absolute; background: {GOLD}; }}
.wheel {{ display: inline-flex; font-variant-numeric: tabular-nums; }}
.wd {{ display: inline-block; height: 1em; overflow: hidden; line-height: 1em; }}
.ws {{ display: grid; }}
.ws span {{ height: 1em; line-height: 1em; }}
"""

# Rolling digits: one column per digit, each rolling 0 -> its digit (after the number-wheel registry block).
WHEEL_JS = """
    document.querySelectorAll('#root .wheel').forEach(el => {
      if (el.dataset.ready) return;
      const v = el.dataset.value; el.textContent = '';
      for (const ch of v) {
        if (!/\\d/.test(ch)) { el.append(document.createTextNode(ch)); continue; }
        const d = document.createElement('span'); d.className = 'wd';
        const s = document.createElement('span'); s.className = 'ws'; s.dataset.target = (-(10 + Number(ch))) + 'em';
        for (let i = 0; i <= 10 + Number(ch); i++) { const n = document.createElement('span'); n.textContent = String(i % 10); s.appendChild(n); }
        d.appendChild(s); el.appendChild(d);
      }
      el.dataset.ready = '1';
    });
"""


class Scene:
    def __init__(self, hid):
        self.h, self.t0, self.dur = hid, HSTART[hid], HDUR[hid]
        self.cam, self.stage, self.js, self.css, self.n = [], [], [], "", 0

    def L(self, t):  # global -> local seconds
        return round(t - self.t0, 3)

    def nid(self, kind):
        self.n += 1
        return f"{self.h}-{kind}{self.n}"

    def add(self, html, cam=True):
        (self.cam if cam else self.stage).append("      " + html)

    def tw(self, line):
        self.js.append("    " + line)

    def sfx(self, t_local, file, vol):
        SFX.append((round(self.t0 + t_local, 3), file, vol))

    # ----- building blocks -----
    def plate(self, src, x, y, w, reveal="wipe", at=0.1, dur=0.55, cam=True):
        iw, ih = size(src); h = round(w * ih / iw); pid = self.nid("p")
        self.add(f'<div id="{pid}" class="plate" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px;"><img src="{src}" alt=""></div>', cam)
        if reveal == "wipe":
            self.tw(f'tl.fromTo("#{pid}", {{ clipPath: "inset(0 100% 0 0 round 6px)" }}, {{ clipPath: "inset(0 0% 0 0 round 6px)", duration: {dur}, ease: "expo.out" }}, {at});')
        elif reveal == "down":
            self.tw(f'tl.fromTo("#{pid}", {{ clipPath: "inset(0 0 100% 0 round 6px)" }}, {{ clipPath: "inset(0 0 0% 0 round 6px)", duration: {dur}, ease: "power2.inOut" }}, {at});')
        elif reveal == "scan":
            sid = self.nid("scan")
            self.add(f'<div id="{sid}" class="lead" style="left:{x}px; top:{y - 10}px; width:3px; height:{h + 20}px; opacity:0;"></div>', cam)
            self.tw(f'tl.fromTo("#{pid}", {{ clipPath: "inset(0 100% 0 0 round 6px)" }}, {{ clipPath: "inset(0 0% 0 0 round 6px)", duration: {dur}, ease: "power1.inOut" }}, {at});')
            self.tw(f'tl.fromTo("#{sid}", {{ x: 0, opacity: 1 }}, {{ x: {w}, opacity: 1, duration: {dur}, ease: "power1.inOut" }}, {at});')
            self.tw(f'tl.to("#{sid}", {{ opacity: 0, duration: 0.15 }}, {round(at + dur, 3)});')
        return {"id": pid, "x": x, "y": y, "w": w, "h": h}

    def mark(self, pl, f, at, until=None, sound=True):
        fx0, fy0, fx1, fy1 = f; mid = self.nid("m")
        x, y = pl["x"] + fx0 * pl["w"] - 8, pl["y"] + fy0 * pl["h"] - 8
        self.add(f'<div id="{mid}" class="mark" style="left:{x:.0f}px; top:{y:.0f}px; width:{(fx1 - fx0) * pl["w"] + 16:.0f}px; height:{(fy1 - fy0) * pl["h"] + 16:.0f}px;"></div>')
        self.tw(f'tl.fromTo("#{mid}", {{ opacity: 0, scale: 1.08 }}, {{ opacity: 1, scale: 1, duration: 0.27, ease: "power3.out" }}, {at});')
        if until is not None:
            self.tw(f'tl.to("#{mid}", {{ opacity: 0, duration: 0.18, ease: "power2.in" }}, {until});')
        if sound:
            self.sfx(at, "click-soft", 0.35)
        return mid

    def label(self, html, x, y, size, at, lead=None, cam=False, until=None):
        """Annotation: optional leader line draws, then the text wipes in."""
        lid = self.nid("l")
        if lead:
            lx, ly, lw, lh = lead; did = self.nid("ld")
            self.add(f'<div id="{did}" class="lead" style="left:{lx}px; top:{ly}px; width:{lw}px; height:{lh}px;"></div>', cam)
            prop = "scaleY" if lh > lw else "scaleX"
            self.tw(f'tl.fromTo("#{did}", {{ {prop}: 0, transformOrigin: "50% 0%" }}, {{ {prop}: 1, duration: 0.25, ease: "power3.out" }}, {at});')
            at = round(at + 0.12, 3)
            self.last_lead = did
            if until is not None:
                self.tw(f'tl.to("#{did}", {{ opacity: 0, duration: 0.15 }}, {until});')
        self.add(f'<div id="{lid}" class="lbl" style="left:{x}px; top:{y}px; font-size:{size}px;">{html}</div>', cam)
        self.tw(f'tl.fromTo("#{lid}", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.4, ease: "expo.out" }}, {at});')
        if until is not None:
            self.tw(f'tl.to("#{lid}", {{ opacity: 0, filter: "blur(6px)", duration: 0.16 }}, {until});')
        return lid

    def press(self, sel, at, rot=-2.0, ring=None, vol=0.55):
        """Stamp press: slams in from 1.35x, settles tilted, ink ring bursts, camera shakes 3 frames."""
        self.tw(f'tl.fromTo("{sel}", {{ opacity: 0, scale: 1.35, rotation: {rot - 5} }}, {{ opacity: 1, scale: 1, rotation: {rot}, duration: 0.16, ease: "power4.in" }}, {round(at - 0.16, 3)});')
        if ring:
            rid = self.nid("ring"); x, y, w, h = ring
            self.add(f'<div id="{rid}" class="ring" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px;"></div>')
            self.tw(f'tl.fromTo("#{rid}", {{ opacity: 0.5, scale: 0.95, rotation: {rot} }}, {{ opacity: 0, scale: 1.3, rotation: {rot}, duration: 0.55, ease: "expo.out", immediateRender: false }}, {at});')
        for k, (dx, dy) in enumerate([(7, -4), (-5, 3), (3, -2), (0, 0)]):
            self.tw(f'tl.set("#{self.h}-cam", {{ x: {dx}, y: {dy} }}, {round(at + k / 30, 3)});')
        self.sfx(at - 0.02, "impact-bass-1", vol)

    # ----- transitions (exit at the end of this scene, entry at the start) -----
    def enter(self, kind):
        c = f"#{self.h}-cam"
        if kind == "zoom":
            self.tw(f'tl.fromTo("{c}", {{ scale: 1.14, filter: "blur(14px)" }}, {{ scale: 1, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }}, 0);')
        elif kind == "whip-left":
            self.tw(f'tl.fromTo("{c}", {{ x: 620, filter: "blur(18px)" }}, {{ x: 0, filter: "blur(0px)", duration: 0.32, ease: "expo.out" }}, 0);')
        elif kind == "whip-up":
            self.tw(f'tl.fromTo("{c}", {{ y: 520, filter: "blur(18px)" }}, {{ y: 0, filter: "blur(0px)", duration: 0.32, ease: "expo.out" }}, 0);')
        elif kind == "blur":
            self.tw(f'tl.fromTo("{c}", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power2.out" }}, 0);')

    def exit(self, kind, origin=None):
        c, e = f"#{self.h}-cam", self.dur
        if kind == "zoom":
            ox, oy = origin
            self.tw(f'tl.to("{c}", {{ scale: 2.4, transformOrigin: "{ox}px {oy}px", filter: "blur(14px)", duration: 0.4, ease: "power3.in" }}, {round(e - 0.4, 3)});')
            self.sfx(e - 0.42, "whoosh-short", 0.4)
        elif kind == "whip-left":
            self.tw(f'tl.to("{c}", {{ x: -620, filter: "blur(18px)", duration: 0.22, ease: "power3.in" }}, {round(e - 0.22, 3)});')
            self.sfx(e - 0.25, "whoosh-short", 0.4)
        elif kind == "whip-up":
            self.tw(f'tl.to("{c}", {{ y: -520, filter: "blur(18px)", duration: 0.22, ease: "power3.in" }}, {round(e - 0.22, 3)});')
            self.sfx(e - 0.25, "whoosh-short", 0.4)
        elif kind == "blur":
            self.tw(f'tl.to("{c}", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }}, {round(e - 0.18, 3)});')

    def write(self, under=""):
        cam = f'    <div id="{self.h}-cam" class="cam">\n' + "\n".join(self.cam) + "\n    </div>"
        stage = "\n".join(self.stage)
        (P / "compositions" / f"{self.h}.html").write_text(f"""<template>
  <style>{BASE_CSS}{self.css}</style>
  <div id="root" data-composition-id="{self.h}" data-width="1920" data-height="1080">
{under}
{cam}
{stage}
  </div>
  <script>
{WHEEL_JS}
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.js)}
    window.__timelines["{self.h}"] = tl;
  </script>
</template>
""")


(P / "compositions").mkdir(exist_ok=True)
for old in P.glob("compositions/s*.html"):
    old.unlink()

# ================= hook: five real closes -> the rulebook -> normalized =================
s = Scene("hook")
rows = [("GOLD", "1,42,024", "per 10 g", "1,42,595", "per 10 g"), ("GOLDM", "1,40,453", "per 10 g", "1,41,018", "per 10 g"),
        ("GOLDTEN", "1,40,832", "per 10 g", "1,40,832", "per 10 g"), ("GOLDGUINEA", "1,13,168", "per 8 g", "1,41,460", "per 10 g"),
        ("GOLDPETAL", "14,155", "per 1 g", "1,41,550", "per 10 g")]
notes = {0: ["995 → 999 purity", "expires 4 Dec"], 1: ["995 → 999 purity", "expires 5 Nov"], 3: ["quoted per 8 g"], 4: ["quoted per 1 g, settles Mumbai"]}
s.css = f"""
.src {{ position: absolute; left: 180px; top: 96px; font-size: 30px; color: {STEEL}; }}
.row {{ position: absolute; left: 180px; display: flex; align-items: baseline; gap: 36px; }}
.sym {{ width: 330px; font-family: 'Barlow Condensed'; font-weight: 600; font-size: 60px; color: {STEEL}; }}
.px {{ position: relative; width: 470px; height: 112px; font-family: 'Barlow Condensed'; font-weight: 700; font-size: 112px; line-height: 1; }}
.px > span {{ position: absolute; left: 0; top: 0; }}
.unit {{ position: relative; width: 150px; font-size: 32px; color: {STEEL}; }}
.unit > span {{ position: absolute; left: 0; bottom: -10px; white-space: nowrap; }}
.note {{ position: absolute; left: 1250px; font-size: 28px; color: {STEEL}; white-space: nowrap; }}
.note::before {{ content: ""; display: inline-block; width: 22px; height: 3px; background: {GOLD}; vertical-align: middle; margin-right: 12px; }}
.q {{ position: absolute; left: 1290px; top: 430px; font-family: 'Barlow Condensed'; font-weight: 700; font-size: 132px; color: {GOLD}; opacity: 0; }}
.bracket {{ position: absolute; left: 1250px; top: 186px; width: 4px; height: 620px; background: {GOLD}; }}
"""
s.add(f'<div id="hook-src" class="src">MCX closing prices, 23 Oct 2026</div>')
s.add(f'<div id="hook-src2" class="src" style="opacity:0; color:{INK};">Same prices, in ₹ per 10 g at 999 purity</div>')
for i, (sym, a, ua, b, ub) in enumerate(rows):
    s.add(f'<div id="hook-r{i}" class="row" style="top:{170 + i * 132}px;"><span class="sym">{sym}</span>'
          f'<span class="px"><span id="hook-a{i}">₹{a}</span><span id="hook-b{i}" class="wheel" data-value="₹{b}" style="opacity:0;"></span></span>'
          f'<span class="unit"><span id="hook-ua{i}">{ua}</span><span id="hook-ub{i}" style="opacity:0;">{ub}</span></span></div>')
s.add('<div id="hook-units" class="mark" style="left:1006px; top:178px; width:190px; height:660px;"></div>')
s.add('<div id="hook-q" class="q">Free money?</div>')
t_five, t_never, t_free = s.L(cue("s01", "five")), s.L(cue("s01", "never")), s.L(cue("s01", "free"))
t_rule, t_pur, t_quote, t_city, t_exp = (s.L(cue("s02", w)) for w in ("rulebook", "purity", "quote", "settlement", "expiry"))
t_conv, t_grams = s.L(cue("s02", "converts")), s.L(cue("s02", "grams"))
s.tw(f'tl.fromTo("#hook-units", {{ opacity: 0, scale: 1.06 }}, {{ opacity: 1, scale: 1, duration: 0.27, ease: "power3.out" }}, {t_five});')
s.sfx(t_five, "click-soft", 0.35)
for i, dx in enumerate([0, 46, -34, 78, -52]):   # prices never line up
    s.tw(f'tl.fromTo("#hook-r{i}", {{ x: 0 }}, {{ x: {dx}, duration: 0.55, ease: "elastic.out(1, 0.6)" }}, {round(t_never + 0.06 * i, 3)});')
s.tw(f'tl.to("#hook-units", {{ opacity: 0, duration: 0.15 }}, {t_never});')
s.press("#hook-q", t_free, rot=-3, vol=0.5)
s.tw(f'tl.to("#hook-q", {{ opacity: 0, filter: "blur(8px)", duration: 0.2, ease: "power2.in" }}, {round(t_rule - 0.2, 3)});')
cue_for = {0: [t_pur, t_exp], 1: [t_pur, t_exp], 3: [t_quote], 4: [t_city]}
for i, lines in notes.items():
    for k, txt in enumerate(lines):
        nid = f"hook-n{i}{k}"
        s.add(f'<div id="{nid}" class="note" style="top:{184 + i * 132 + k * 40}px;">{txt}</div>')
        at = cue_for[i][k] + 0.07 * (i % 2)
        s.tw(f'tl.fromTo("#{nid}", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.4, ease: "expo.out" }}, {round(at, 3)});')
        s.tw(f'tl.to("#{nid}", {{ opacity: 0, filter: "blur(6px)", duration: 0.16 }}, {round(t_conv - 0.05, 3)});')
for t in (t_pur, t_quote, t_city):
    s.sfx(t, "click-soft", 0.25)
# converts: rows snap back into line and every price rolls to its normalized value
for i in range(5):
    s.tw(f'tl.to("#hook-r{i}", {{ x: 0, duration: 0.5, ease: "power3.inOut" }}, {round(t_conv + 0.04 * i, 3)});')
    s.tw(f'tl.to("#hook-a{i}", {{ opacity: 0, filter: "blur(8px)", duration: 0.16, ease: "power2.in" }}, {round(t_conv + 0.05 * i, 3)});')
    s.tw(f'tl.set("#hook-b{i}", {{ opacity: 1 }}, {round(t_conv + 0.12 + 0.05 * i, 3)});')
    s.tw(f'tl.fromTo("#hook-b{i} .ws", {{ y: "0em" }}, {{ y: (k, el) => el.dataset.target, duration: 1.0, ease: "power3.out", stagger: 0.03 }}, {round(t_conv + 0.12 + 0.05 * i, 3)});')
    if rows[i][2] != rows[i][4]:
        s.tw(f'tl.to("#hook-ua{i}", {{ opacity: 0, duration: 0.15 }}, {t_conv});')
        s.tw(f'tl.fromTo("#hook-ub{i}", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2 }}, {round(t_conv + 0.6, 3)});')
s.tw(f'tl.to("#hook-src", {{ opacity: 0, filter: "blur(6px)", duration: 0.16 }}, {t_conv});')
s.tw(f'tl.fromTo("#hook-src2", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2 }}, {round(t_conv + 0.18, 3)});')
s.sfx(t_conv + 0.12, "key-press", 0.35)
s.add('<div id="hook-br" class="bracket"></div>')
s.tw(f'tl.fromTo("#hook-br", {{ scaleY: 0, transformOrigin: "50% 0%" }}, {{ scaleY: 1, duration: 0.45, ease: "power3.out" }}, {round(t_grams - 0.1, 3)});')
s.label('All five within <b>1.3%</b>', 1290, 452, 64, round(t_grams + 0.15, 3))
s.sfx(t_grams - 0.1, "click-soft", 0.35)
s.exit("zoom", origin=(780, 490))   # into the GOLDTEN price -> its spread chart
s.write()

# ================= spread: control pair converges, then the final weeks =================
s = Scene("spread")
s.enter("zoom")
sp = s.plate("assets/screens/spread_control.png", 220, 70, 1480, reveal=None)
zero_y = sp["y"] + 0.452 * sp["h"]
l_zero = s.label('Must settle at <b>₹0</b>', 1010, 300, 50, s.L(cue("s03", "zero")), lead=(1080, 356, 3, round(zero_y - 356)), cam=True)
ld_zero = s.last_lead
m_land = s.mark(sp, (0.955, 0.40, 0.995, 0.62), s.L(cue("s03", "lands")))
s.css = f".cnt {{ position: absolute; left: 1290px; top: 96px; padding: 14px 24px; background: {PAPER}; border-radius: 6px; box-shadow: 0 10px 30px rgba(35,38,43,0.12); font-family: 'Barlow Condensed'; font-weight: 600; font-size: 44px; opacity: 0; white-space: nowrap; }}\n.cnt .wheel {{ color: {GOLD_TXT}; font-weight: 700; }}"
t_eigh = s.L(cue("s03", "eighteen"))
s.add('<div id="spread-cnt" class="cnt"><span class="wheel" data-value="18"></span> of 18 expiries settled within ₹1</div>')
s.tw(f'tl.fromTo("#spread-cnt", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2 }}, {t_eigh});')
s.tw(f'tl.fromTo("#spread-cnt .ws", {{ y: "0em" }}, {{ y: (k, el) => el.dataset.target, duration: 1.1, ease: "power3.out", stagger: 0.05 }}, {t_eigh});')
s.sfx(t_eigh, "key-press", 0.3)
# s04: punch into the final weeks (labels leave first; the counter stays outside the camera)
t_wid = s.L(cue("s04", "widens"))
ox, oy, SC = round(sp["x"] + 0.93 * sp["w"]), round(sp["y"] + 0.62 * sp["h"]), 1.9
s.tw(f'tl.to(["#{l_zero}", "#{ld_zero}", "#{m_land}", "#spread-cnt"], {{ opacity: 0, duration: 0.15 }}, {round(t_wid - 0.5, 3)});')
s.tw(f'tl.set("#spread-cam", {{ transformOrigin: "{ox}px {oy}px" }}, {round(t_wid - 0.36, 3)});')
s.tw(f'tl.to("#spread-cam", {{ scale: {SC}, duration: 0.55, ease: "power3.inOut" }}, {round(t_wid - 0.35, 3)});')
s.sfx(t_wid - 0.38, "whoosh-short", 0.25)
fx0, fy0, fx1, fy1 = 0.885, 0.45, 0.99, 0.82
bx0, by0 = sp["x"] + fx0 * sp["w"], sp["y"] + fy0 * sp["h"]
s.mark(sp, (fx0, fy0, fx1, fy1), round(t_wid + 0.25, 3))
fbx = round(ox + (bx0 - ox) * SC); fby = round(oy + (by0 - oy) * SC)   # box corner in frame coords after the punch
s.label('Widens, then snaps shut <b>after</b> the exit', fbx - 760, fby - 92, 52, s.L(cue("s04", "exit")))
SPREAD_END = {"origin": (ox, oy), "scale": SC, "settle": (round(ox + (sp["x"] + 0.975 * sp["w"] - ox) * SC), round(oy + (sp["y"] + 0.452 * sp["h"] - oy) * SC))}
s.write()

# ================= verdict: iris from the settle point; checklist; stamp press =================
s = Scene("verdict")
iw, ih = size("assets/screens/spread_control.png"); ph = round(1480 * ih / iw)
under = (f'    <div id="verdict-under" class="cam" style="transform-origin:{SPREAD_END["origin"][0]}px {SPREAD_END["origin"][1]}px; transform: scale({SPREAD_END["scale"]});">'
         f'<div class="plate" style="left:220px; top:70px; width:1480px; height:{ph}px;"><img src="assets/screens/spread_control.png" alt=""></div></div>')
px_, py_ = SPREAD_END["settle"]
s.css = f"""
#verdict-cam {{ background: {PAPER}; }}
.chk {{ position: absolute; left: 230px; font-family: 'Barlow Condensed'; font-weight: 700; font-size: 92px; line-height: 1; }}
.chk .w {{ display: inline-block; margin-right: 0.22em; }}
.tick {{ position: absolute; left: 150px; width: 44px; height: 22px; border-left: 8px solid {GOLD}; border-bottom: 8px solid {GOLD}; transform-origin: 0 100%; }}
"""
s.tw(f'tl.fromTo("#verdict-cam", {{ clipPath: "circle(0% at {px_}px {py_}px)" }}, {{ clipPath: "circle(130% at {px_}px {py_}px)", duration: 0.5, ease: "power3.inOut" }}, 0);')
s.sfx(0.0, "whoosh-short", 0.35)
lines = [("Past data only", "past"), ("Next-day fills", "next"), ("Every cost included", "every")]
for k, (txt, w) in enumerate(lines):
    at = s.L(cue("s05", w)); y = 250 + k * 150
    s.add(f'<div id="verdict-t{k}" class="tick" style="top:{y + 26}px; rotate:-45deg;"></div>')
    s.add(f'<div id="verdict-c{k}" class="chk" style="top:{y}px;">' + "".join(f'<span class="w">{x}</span>' for x in txt.split()) + "</div>")
    s.tw(f'tl.fromTo("#verdict-c{k} .w", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.13, stagger: 0.07 }}, {at});')
    s.tw(f'tl.fromTo("#verdict-t{k}", {{ scale: 0 }}, {{ scale: 1, duration: 0.25, ease: "back.out(2)" }}, {round(at + 0.2, 3)});')
    s.sfx(at + 0.2, "click-soft", 0.3)
t_verd, t_no = s.L(cue("s05", "verdict")), s.L(cue("s05", "no"))
s.tw(f'tl.to([".chk", ".tick"], {{ opacity: 0, filter: "blur(8px)", duration: 0.18, stagger: 0.03, ease: "power2.in" }}, {round(t_verd - 0.1, 3)});')
st = s.plate("assets/screens/stamp_control.png", 560, 250, 800, reveal=None)
s.press(f'#{st["id"]}', t_no, rot=-2, ring=(560 - 20, 250 - 20, 840, round(st["h"] + 40)), vol=0.6)
s.exit("whip-left")
s.write(under=under)

# ================= metrics: numbers, then break-even on a tick ruler =================
s = Scene("metrics")
s.enter("whip-left")
m = s.plate("assets/screens/metrics_control.png", 180, 150, 1560)
t_sixty, t_breaks, t_ticks = s.L(cue("s06", "Sixty")), s.L(cue("s06", "breaks")), s.L(cue("s06", "ticks"))
s.mark(m, (0.02, 0.05, 0.66, 0.42), t_sixty, until=round(t_breaks - 0.1, 3))
s.mark(m, (0.34, 0.45, 0.62, 0.88), t_breaks)
X0, X1, VMAX, RY = 360, 1560, 3.75, 700   # ruler: ₹0 .. ₹3.75 per 10 g
px = lambda v: round(X0 + (X1 - X0) * v / VMAX)
s.css = f"""
.rul {{ position: absolute; left: {X0}px; top: {RY}px; width: {X1 - X0}px; height: 3px; background: {INK}; }}
.tk {{ position: absolute; top: {RY - 14}px; width: 3px; height: 31px; background: {INK}; }}
.tkl {{ position: absolute; top: {RY + 28}px; font-size: 28px; color: {STEEL}; transform: translateX(-50%); }}
.fill {{ position: absolute; left: {X0}px; top: {RY - 10}px; height: 23px; width: {px(2.5) - X0}px; background: rgba(176,122,30,0.28); }}
.pin {{ position: absolute; top: {RY - 70}px; width: 4px; height: 76px; background: {GOLD}; }}
.cap2 {{ position: absolute; left: {X0}px; top: {RY + 82}px; font-size: 26px; color: {STEEL}; }}
"""
for k, v in enumerate([0, 1.25, 2.5, 3.75]):
    s.add(f'<div id="metrics-tk{k}" class="tk" style="left:{px(v) - 1}px;"></div><div id="metrics-tl{k}" class="tkl" style="left:{px(v)}px;">₹{v:g}</div>')
s.add('<div id="metrics-rul" class="rul"></div><div id="metrics-fill" class="fill"></div>')
s.add(f'<div id="metrics-pin" class="pin" style="left:{X0}px;"></div>')
s.add('<div id="metrics-cap2" class="cap2">GOLDGUINEA moves in ticks of ₹1 per 8 g = ₹1.25 per 10 g</div>')
s.tw(f'tl.fromTo("#metrics-rul", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 0.5, ease: "power3.out" }}, {round(t_breaks - 0.2, 3)});')
s.tw(f'tl.fromTo([".tk", ".tkl", "#metrics-cap2"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2, stagger: 0.05 }}, {round(t_breaks, 3)});')
s.tw(f'tl.fromTo("#metrics-pin", {{ opacity: 0, x: 0 }}, {{ opacity: 1, x: {px(3.0) - X0}, duration: 0.9, ease: "power3.out" }}, {round(t_breaks + 0.3, 3)});')
s.label('Break-even <b>₹3.0</b>', px(3.0) - 40, RY - 140, 54, round(t_breaks + 1.0, 3))
s.tw(f'tl.fromTo("#metrics-fill", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 0.5, ease: "power2.out" }}, {round(t_ticks - 0.3, 3)});')
s.sfx(t_breaks + 0.3, "key-press", 0.3)
s.exit("blur")
s.write()

# ================= regimes =================
s = Scene("regimes")
s.enter("blur")
rg = s.plate("assets/screens/regime_control.png", 360, 110, 1200, reveal="down", dur=0.8)
s.mark(rg, (0.02, 0.72, 0.98, 0.96), s.L(cue("s07", "April")))
s.exit("whip-up")
s.write()

# ================= pairs: six stamps (gold row, then carry + silver row), six presses =================
s = Scene("pairs")
s.enter("whip-up")
t_all, t_no = s.L(cue("s08", "Six")), s.L(cue("s08", "no"))
STAMPS = [("control", -3), ("goldgoldm", 2), ("petal", -2), ("goldm", 2), ("silverm", -3), ("silver", -1)]
for i, (tag, rot) in enumerate(STAMPS):
    x, y = 105 + (i % 3) * 605, 190 + (i // 3) * 320
    st = s.plate(f"assets/screens/stamp_{tag}.png", x, y, 500, reveal=None)
    at = round(t_all + 0.25 + i * (t_no - t_all - 0.25) / (len(STAMPS) - 1), 3)
    s.press(f'#{st["id"]}', at, rot=rot, ring=(x - 20, y - 20, 540, round(st["h"] + 40)), vol=0.3 + 0.06 * i)
s.exit("zoom", origin=(1565, 645))
s.write()

# ================= carry: scan reveal, two real medians =================
s = Scene("carry")
s.enter("zoom")
c = s.plate("assets/screens/carry_control.png", 80, 190, 1760, reveal="scan", at=0.25, dur=1.6)
t_six, t_four = s.L(cue("s09", "six")), s.L(cue("s09", "fourteen"))
s.label('<b>≈6%</b> a year through 2025', 210, 112, 52, t_six, lead=(330, 172, 3, 120), cam=True)
s.label('<b>≈14%</b> since the rally', 1080, 112, 52, t_four, lead=(1200, 172, 3, 70), cam=True)
s.sfx(t_six, "click-soft", 0.3); s.sfx(t_four, "click-soft", 0.3)
s.exit("blur")
s.write()

# ================= alerts: the quiet state =================
s = Scene("alerts")
s.enter("blur")
a = s.plate("assets/screens/alerts_control.png", 260, 130, 1400)   # six pairs since the silver update
t_q = s.L(cue("s10", "quiet"))
s.mark(a, (0.005, 0.12, 0.99, 0.30), t_q)
s.css = f".zero {{ position: absolute; left: 80px; top: 640px; display: flex; align-items: baseline; gap: 26px; opacity: 0; }}\n.zero .n {{ font-family: 'Barlow Condensed'; font-weight: 700; font-size: 170px; line-height: 1; }}\n.zero .t {{ font-family: 'Barlow Condensed'; font-weight: 600; font-size: 60px; color: {STEEL}; }}"
s.add('<div id="alerts-zero" class="zero"><span class="n">0</span><span class="t">alerts today. Silence is the normal state.</span></div>')
s.tw(f'tl.fromTo("#alerts-zero", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2 }}, {round(t_q + 0.35, 3)});')
s.exit("whip-left")
s.write()

# ================= end card =================
s = Scene("end")
s.enter("whip-left")
s.css = f"""
.hm {{ position: absolute; left: 640px; top: 230px; width: 640px; height: 250px; display: flex; align-items: center; justify-content: center;
       border: 6px solid {INK}; outline: 2.5px solid {INK}; outline-offset: 9px; border-radius: 10px; background: {PAPER}; }}
.hm span {{ font-family: 'Barlow Condensed'; font-weight: 700; font-size: 168px; letter-spacing: 0.02em; }}
.tag {{ position: absolute; left: 0; right: 0; top: 548px; text-align: center; font-family: 'Barlow Condensed'; font-weight: 600; font-size: 64px; }}
.tag .w {{ display: inline-block; margin: 0 0.12em; }}
.links {{ position: absolute; left: 0; right: 0; top: 664px; text-align: center; font-size: 34px; line-height: 1.5; color: {GOLD_TXT}; }}
.team {{ position: absolute; left: 0; right: 0; top: 790px; text-align: center; font-size: 28px; color: {STEEL}; }}
"""
s.add('<div id="end-hm" class="hm"><span>AuLens</span></div>')
s.add('<div id="end-tag" class="tag">' + "".join(f'<span class="w">{w}</span>' for w in "Gold and silver, six pairs, one honest verdict.".split()) + "</div>")
s.add('<div id="end-links" class="links">hackhill-wikhjmugah4iqupyf4nlh4.streamlit.app<br>github.com/Srujanmirji/hackhill</div>')
s.add("<div id=\"end-team\" class=\"team\">Team CodeWick · Hack in Hills '26 · Track 03</div>")
s.press("#end-hm", s.L(cue("s11", "AuLens")) + 0.05, rot=0, ring=(620, 210, 680, 290), vol=0.6)
s.tw(f'tl.fromTo("#end-tag .w", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.13, stagger: 0.09 }}, {s.L(cue("s11", "Gold"))});')
s.tw(f'tl.fromTo("#end-links", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.5, ease: "expo.out" }}, {s.L(cue("s11", "Open"))});')
s.tw(f'tl.fromTo("#end-team", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4 }}, {round(s.L(cue("s11", "Open")) + 0.4, 3)});')
s.write()

# ================= captions: words print as they are spoken =================
groups, cur = [], []
for i, w in enumerate(WORDS):
    cur.append(w); nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
    end = w["text"][-1] in ".?:!,;" and len(cur) >= 2
    brk = nxt is None or nxt["vo"] != w["vo"] or nxt["start"] - w["end"] >= 0.15
    if len(cur) >= 5 or end or (brk and len(cur) >= 3) or nxt is None or nxt["vo"] != w["vo"]:
        groups.append(cur); cur = []
cb, cj = [], []
for i, g in enumerate(groups):
    s0 = max(round(g[0]["start"] - 0.05, 3), 0.15); e0 = round(g[-1]["end"] + 0.12, 3)
    if i + 1 < len(groups):
        e0 = min(e0, round(groups[i + 1][0]["start"] - 0.06, 3))
    gid = f"cap-g{i}"
    cb.append(f'    <div id="{gid}" class="cap"><span class="cap-t">' + " ".join(f'<span class="cw">{w["text"]}</span>' for w in g) + "</span></div>")
    cj.append(f'    tl.set("#{gid}", {{ opacity: 1, visibility: "visible" }}, {s0});')
    for k, w in enumerate(g):
        cj.append(f'    tl.fromTo("#{gid} .cw:nth-child({k + 1})", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.12, ease: "power2.out" }}, {max(w["start"], s0)});')
    cj.append(f'    tl.to("#{gid}", {{ opacity: 0, duration: 0.12, ease: "power2.in" }}, {round(e0 - 0.12, 3)});')
    cj.append(f'    tl.set("#{gid}", {{ opacity: 0, visibility: "hidden" }}, {e0});')
(P / "compositions/captions.html").write_text(f"""<template>
  <style>
@font-face {{ font-family: 'Public Sans'; font-weight: 600; src: url('assets/fonts/PublicSans-SemiBold.woff2'); }}
#root {{ position: absolute; inset: 0; }}
.cap {{ position: absolute; left: 0; right: 0; bottom: 96px; text-align: center; font-family: 'Public Sans', sans-serif;
        font-weight: 600; font-size: 46px; line-height: 1.2; color: {INK}; opacity: 0; visibility: hidden; overflow: visible; }}
.cap-t {{ display: inline-block; padding: 8px 22px 10px; border-radius: 6px; background: {PAPER}; }}
.cw {{ display: inline-block; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
{chr(10).join(cb)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cj)}
    window.__timelines["captions"] = tl;
  </script>
</template>
""")

# ================= index.html =================
DURS = {"impact-bass-1": 2.12, "impact-bass-2": 2.59, "whoosh-short": 0.57, "click-soft": 0.37, "key-press": 0.4}
hosts = "\n".join(
    f'      <div id="{h}" class="clip" data-composition-id="{h}" data-composition-src="compositions/{h}.html" '
    f'data-start="{HSTART[h]}" data-duration="{HDUR[h]}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>'
    for h, _ in HOSTS)
lanes, rows_ = [], []   # first free lane per sound, so no two sounds overlap on one track
for k, (t, f, v) in enumerate(sorted(SFX)):
    t = max(t, 0); d = min(DURS[f], TOTAL - t)
    lane = next((i for i, end in enumerate(lanes) if end <= t), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = t + d
    rows_.append(f'      <audio id="sfx{k}" src="assets/sfx/{f}.mp3" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="{4 + lane}" data-volume="{v}"></audio>')
sfx = "\n".join(rows_)
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
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080" data-motion-blur="on">
{hosts}
      <div id="captions" class="clip" data-composition-id="captions" data-composition-src="compositions/captions.html"
        data-start="0" data-duration="{TOTAL}" data-track-index="2" data-track-kind="captions" data-width="1920" data-height="1080"></div>
      <audio id="vo" src="assets/vo/voiceover.wav" data-start="0" data-duration="{TOTAL}" data-track-index="3" data-volume="1"></audio>
{sfx}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
print("film", TOTAL, "s | hosts", len(HOSTS), "| caption groups", len(groups), "| sfx", len(SFX))
