# Dashboard Specification

## Technology
FastAPI serves:
- HTML
- CSS
- vanilla JavaScript
- WebSocket telemetry

## Main screen
Header:
Product name placeholder
Emergency Waiting Room
N waiting | N requiring reassessment

Above or alongside the dashboard, first-time users must see:
- headline: `Triage is a snapshot. Patients keep changing.`
- one-sentence use case: ordinary-camera physiological change monitoring for emergency waiting rooms
- primary button: `RUN GUIDED DEMO`
- secondary button: `TRY LIVE CAMERA`
- pipeline: `Camera -> HR + RR -> Confidence -> Personal baseline -> Sustained change -> Reassessment`
- safety boundary: `Decision support only. It does not diagnose or replace clinical triage.`
- expandable `What is real vs simulated?` explanation

The use case and next action must be understandable within 15 seconds without reading the README.

Six patient cards.

Each card:
- patient ID
- wait time
- HR
- RR
- signal confidence
- compact trend sparkline if easy
- state badge

REASSESS patients:
- move to top
- visually prominent
- non-intrusive popup/toast

Popup:
"Patient P04 has shown a sustained physiological deviation from baseline. Reassessment recommended."

## Patient detail screen
Required panes:

1. Video
- raw camera/video
- ROI overlays
- RAW/EVM toggle

2. Current physiology
- HR
- RR
- confidence
- signal state

3. Baseline vs current
- baseline HR / current HR / delta
- baseline RR / current RR / delta

4. Trend graph
- HR over time
- RR over time if reliable

5. Why flagged
- HR deviation
- RR deviation
- persistence
- signal confidence
- ROI agreement
- motion

6. Status
- STABLE
- CHANGE DETECTED
- REASSESSMENT RECOMMENDED
- SIGNAL UNRELIABLE

7. Explanation/help
- short tooltip or expandable definition for HR, RR, rPPG, EVM, confidence, ROI agreement, baseline deviation, persistence, and change score
- explain that EVM is visualization-only
- show why a signal is unavailable and what the user can do

## Guided demo controls
- Start/restart
- Pause/resume
- Skip explanation
- Progress/stage indicator
- Switch to live camera

The UI may advance explanatory stages, but must never directly assign physiological measurements or REASSESS state.

## Error states
- camera denied: explain permission and keep Guided Demo available
- no camera: keep Guided Demo available
- missing demo asset/model: identify the missing item and show recovery command/instruction
- backend disconnected: show reconnecting state, not a blank dashboard
- unsupported browser: provide a plain explanation and preserve prerecorded demo where possible

## Design
Clinical, minimal, modern.
No sci-fi aesthetics.
No fake medical certainty.
No unexplained technical jargon on the first screen.
