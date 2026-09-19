# Progress

## Split
- This laptop: Product (dashboard / demo / launch). No Supabase. No ML.
- Ranveer: Core (vision / rPPG / confidence / baseline / change). See `HANDOFF_RANVEER.md`.

## Built on this laptop
- FastAPI + `./run.sh` + `/health` + homepage
- Webcam and MP4 share `FramePacket`
- Face/ROI/rPPG/HR/quality/baseline/scorer/state machine (Core, handed to Ranveer)
- Six-patient dashboard, why-flagged, popup, Guided Demo / Live pages
- Synthetic fixtures via `python scripts/generate_fixtures.py`

## Tests
Most M0–M5 and safety tests passed. Remaining Core gap: sustained valid pulse change should become `REASSESS`.

## Do not
- Hardcode REASSESS
- Fabricate physiology
- Add Supabase or a trained medical model
