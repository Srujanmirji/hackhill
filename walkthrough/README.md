# AuLens walkthrough video (HyperFrames)

About 2 minutes: the deck slides and the live app, narrated, with burned-in captions. Opens with
"Hack in Hills, powered by TinyFish." Real slides and real captures of the app only.

```bash
cd walkthrough
npx hyperframes preview      # watch / edit in the browser
npx hyperframes check        # lint, layout, contrast
npx hyperframes render -o renders/AuLens_walkthrough_HackInHills26.mp4
```

- Copy: `assets/vo/script.json`. After editing it, delete the changed `assets/vo/vNN.wav`, then run
  `python3 scripts/voice.py` (Kokoro, voice af_heart; spoken spellings live in its `SAY` list),
  `npx hyperframes transcribe assets/vo/voiceover.wav --json -l en` and `python3 scripts/build.py`.
- Slides: `pdftoppm -r 192 -png ../CodeWick_AuLens_HackInHills26_v5.pdf assets/deck/slide`.
- App: run `streamlit run app/streamlit_app.py --server.port 8501` at the deployed commit, then
  `python3 scripts/capture_app.py assets/app` (the hosted app sits in an iframe, so capture locally).
- Sound effects: Pixabay Content License, see `assets/sfx/CREDITS.md`.
