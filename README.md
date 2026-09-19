# TriageTracker

Continuous physiological-change monitoring for emergency waiting rooms, using an ordinary camera.

This is decision support. It does not diagnose, assign a clinical triage level, or replace a clinician.

## Quick start

On a Mac with Python 3.11+:

```bash
./run.sh
```

That is the only required launch command. It will:

1. create or reuse `.venv`
2. install pinned dependencies
3. download MediaPipe models if they are missing
4. generate synthetic optical fixtures if they are missing
5. start the local server on `127.0.0.1:8765` (or `8766` / `8767` if busy)
6. wait until `/health` is ready
7. open the browser to the homepage

Optional:

```bash
./run.sh --no-browser
./run.sh --check
```

Then use **RUN GUIDED DEMO** (works without a camera) or **TRY LIVE CAMERA**.

Most reliable demo path:

1. `./run.sh`
2. Click **RUN GUIDED DEMO**
3. Watch P04 (controlled-change fixture) baseline, then a sustained HR change
4. Confirm the backend moves P04 to the top and fills **Why flagged**
5. Optional: **TRY LIVE CAMERA** for face/ROI, real HR attempt, motion abstention, and recovery

## Supported setup

- macOS
- Python 3.11 or newer
- Chrome or Safari
- optional MacBook webcam

No Docker, Node, or second terminal is required.

## If something fails

| Symptom | What to do |
| --- | --- |
| `Python 3.11+ is required` | `brew install python@3.11`, then rerun `./run.sh` |
| Camera denied / missing | Guided Demo still works. macOS: System Settings → Privacy & Security → Camera |
| Missing fixture or model | `/health` names the exact path. Models download automatically. Fixtures belong in `fixtures/` |
| Port in use | The launcher tries `8765`, `8766`, then `8767` |
| Page says backend disconnected | The server stopped. Rerun `./run.sh` |

## What is real vs simulated

Real: video ingestion, face tracking, ROIs, rPPG heart rate, respiratory-rate attempt, confidence, motion rejection, baseline, and change detection.

Simulated: patient IDs, wait times, waiting-room chrome, and some background tiles.

The UI never assigns `REASSESS` or invents a heart rate.

## Product

Triage is a snapshot. Patients keep changing.

Pipeline: Camera → HR + RR → Confidence → Personal baseline → Sustained change → Reassessment.

## Two-person split

- **Product (this laptop):** dashboard, Guided Demo, live camera, `./run.sh`. No Supabase. No ML.
- **Core (Ranveer):** face/ROIs, rPPG, HR, confidence, baseline, change engine. See `HANDOFF_RANVEER.md`.

## Tests

```bash
source .venv/bin/activate
python -m pytest
```

## Health

`GET /health` reports process readiness, package imports, camera probe status, and whether required models/fixtures exist.
