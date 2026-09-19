# Handoff — Ranveer (Core)

This laptop owns **Product**: dashboard, Guided Demo, live camera page, launch/`run.sh`.
You own **Core**: face/ROIs, rPPG, HR, quality/abstention, baseline, change engine.

No Supabase. No machine learning. One local FastAPI app.

## Run

```bash
./run.sh
```

Then `RUN GUIDED DEMO` (no camera) or `TRY LIVE CAMERA`.

```bash
source .venv/bin/activate
python -m pytest
```

## Your files

- `app/video/` — webcam + MP4 share `FramePacket`
- `app/vision/` — MediaPipe face, ROIs, motion
- `app/signals/` — buffers, POS/CHROM, HR, quality, RR, tiny EVM
- `app/monitoring/` — baseline, features, weighted scorer, state machine
- `app/synth.py` + `scripts/generate_fixtures.py` + `fixtures/`
- `tests/unit/test_m1_*.py` … `test_m4_*.py`
- `tests/integration/test_m6_pipeline.py`

Do not rewrite `app/web/`. Product renders `PatientMeasurement` from `app/models.py`. Never hardcode `REASSESS` in the UI.

## Shared contract

`PatientMeasurement.to_dict()` is the object the dashboard displays.
Emit real values or `null`. Do not fabricate HR/RR.

## Known gap

Sustained-change test last failed: synthetic 72→110 BPM ended `STABLE` (HR ~105, baseline ~75, score ~0.60, persist ~7s). Need backend `REASSESS` after a long high-confidence deviation. Temporary spikes and low-confidence/no-face must still never alert.

If RR is weak, keep: `RR unavailable — insufficient signal quality.`
