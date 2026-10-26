# AuLens demo video (HyperFrames)

Source for the ~1:28 hackathon demo. Real MCX data and real captures of the live app only.

```bash
cd video
npx hyperframes preview            # edit / watch in the browser
npx hyperframes check              # lint, layout, contrast
npx hyperframes render             # MP4 into renders/ (git-ignored)
```

- `index.html` mounts the scenes in `compositions/`; captions are one sub-composition; voice is `assets/vo/voiceover.wav`.
- `scripts/build_film.py .` regenerates every composition from `assets/vo/scenes.json` + `assets/vo/transcript.json`
  (cues are word starts from the voice). Edit timings or copy there, then re-run it.
- `scripts/capture_screens.py assets/screens` re-captures the app regions from a local `streamlit run app/streamlit_app.py`
  on port 8502 (crops were then trimmed by hand; see REVIEW.md).
- Voice: Kokoro (`npx hyperframes tts`, voice af_heart), script in `assets/vo/script.json`.
- Sound effects: Pixabay Content License, see `assets/sfx/CREDITS.md`.
