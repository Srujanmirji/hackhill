"""Kokoro voice per scene -> assets/vo/vNN.wav, then one voiceover.wav with gaps and scenes.json (start, duration)."""
import json, re, subprocess, wave
from pathlib import Path

VO = Path("assets/vo"); GAP = 0.45; SPEED = "1.05"
SAY = [(r"\bAuLens\b", "Aw Lens"), (r"Hack in Hills", "Hack, in Hills"), (r"\bSrujan\b", "Srujun"), (r"\bCodeWick\b", "Code Wick"), (r"\bTinyFish\b", "Tiny Fish"),
       (r"\b999\b", "nine nine nine"), (r"\bMCX\b", "M C X"), (r"Bhavcopy", "Bhav copy"),
       (r"Parquet", "Par-kay"), (r"\bAPI\b", "A P I"), (r"\bSEBI\b", "Sebi"), (r"2026's", "twenty twenty-six's")]
script = json.loads((VO / "script.json").read_text())
scenes, t = [], 0.0
frames_all, params = [], None
for s in script:
    say = s["text"]
    for a, b in SAY:
        say = re.sub(a, b, say)
    out = VO / f"{s['id']}.wav"
    if not out.exists():
        subprocess.run(["npx", "hyperframes@0.8.204", "tts", say, "-v", "af_heart", "-s", SPEED, "-o", str(out)], check=True,
                       stdout=subprocess.DEVNULL)
    with wave.open(str(out)) as w:
        params = params or w.getparams(); n = w.getnframes(); frames_all.append(w.readframes(n))
        dur = n / w.getframerate()
    scenes.append({**s, "start": round(t, 3), "duration": round(dur + GAP, 3)})
    t += dur + GAP
silence = b"\x00" * int(GAP * params.framerate) * params.sampwidth * params.nchannels
with wave.open(str(VO / "voiceover.wav"), "wb") as w:
    w.setparams(params)
    for f in frames_all:
        w.writeframes(f + silence)
(VO / "scenes.json").write_text(json.dumps(scenes, indent=1))
print(f"total {t:.2f}s"); [print(s["id"], s["start"], s["duration"]) for s in scenes]
