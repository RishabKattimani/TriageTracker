# Fallback Plan

## Plan A
Live webcam:
- real HR
- real RR
- EVM
- confidence/abstention
Controlled-change MP4:
- real change detection

## Plan B
Live webcam:
- real HR
- RR unavailable or lower confidence
- EVM
- confidence/abstention
Controlled-change MP4:
- real HR-based change detection

## Plan C
Live webcam:
- face tracking
- EVM
- confidence demonstration
Prerecorded fixtures:
- real physiology processing
- real change detection

## Never do
- hardcode a red patient
- show fabricated HR/RR as real measurements
- silently substitute fake values
- let a low-quality signal trigger reassessment

## Required graceful degradation
If RR fails:
- display "RR unavailable"
- keep HR system operating

If live camera fails:
- switch to prerecorded video source through same pipeline
- show a friendly explanation
- keep `RUN GUIDED DEMO` available

If EVM performance is slow:
- reduce ROI/resolution/frame rate, keep feature available

If camera permission is denied:
- do not block the app
- show browser/macOS permission guidance
- allow retry
- keep Guided Demo fully usable

If a fixture or model is missing:
- startup diagnostics identify the exact missing asset
- README explains where it belongs
- do not silently replace real processing with fabricated output

If the preferred port is occupied:
- `run.sh` selects an available documented port or reports the conflict clearly

If the WebSocket disconnects:
- show reconnecting state
- retry with bounded backoff
- do not leave stale measurements appearing live
