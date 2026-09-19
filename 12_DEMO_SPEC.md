# Demo Specification

## First-round mode

The default experience is self-guided because judges may run the project without the team present. The homepage explains the product and starts the same flow below through `RUN GUIDED DEMO`. Explanatory overlays replace spoken narration. A finalist live presentation can use the identical flow with a speaker.

## Required flow

1. Open six-patient waiting-room dashboard.
2. Display: triage is a snapshot; patients keep changing.
3. Open live webcam patient.
4. Show face ROIs and live HR/RR.
5. Toggle EVM.
6. Explain that EVM visualizes subtle changes; rPPG/RR engines calculate measurements.
7. Turn head / occlude face.
8. Show:
   SIGNAL UNRELIABLE
   Motion artifact detected
   No inference made
9. Return still.
10. Show:
   SIGNAL REACQUIRED
11. Return to dashboard.
12. Run controlled-change prerecorded patient through real pipeline.
13. Let judges watch status change.
14. Patient moves to top.
15. Popup:
   Reassessment recommended.
16. Open patient.
17. Show baseline vs current, trends, confidence, persistence, reasons.
18. End:
   We are not replacing triage. We are continuously asking whether a waiting patient has changed enough to warrant another look.

## Guided-demo requirements
- works without webcam permission by using the controlled prerecorded input
- clearly distinguishes the reliable guided path from optional live camera proof
- displays stage/progress and provides pause, restart, and skip-explanation controls
- takes approximately 60-90 seconds
- can be replayed without restarting the server
- ends with `Try Live Camera` and `How It Works` actions
- never labels the controlled recording as an actual medical emergency

## Required Loom submission video

The event requires a 2-5 minute Loom screen recording with presenter camera enabled. Target approximately 3-3.5 minutes. This is separate from the 60-90 second in-product Guided Demo.

Use the MacBook webcam as the live physiological input and show the dashboard on the same laptop. Do not make iPhone streaming part of the required recording. Do not rely on stock hospital footage; the working product should remain the visual focus.

Recommended flow:

1. Team introductions — 20-30 seconds total
   - each member: name, role, and what they built
2. Elevator pitch — 20-30 seconds
   - what was built, who it serves, and why waiting-room reassessment matters
3. Live webcam proof — 40-50 seconds
   - face/ROI tracking, HR/RR attempt, EVM, motion abstention, recovery
4. Core product loop — 40-50 seconds
   - controlled-change fixture, baseline, sustained change, patient prioritization, `Why flagged?`
5. Engineering explanation — 30-40 seconds
   - briefly show console logs and explain OpenCV, MediaPipe, rPPG, confidence, shared video pipeline, and backend state machine
6. So what / next step — 20-30 seconds
   - decision support rather than diagnosis; future validation and hospital workflow integration

Minimize cuts. Console logs must be readable briefly but must not dominate the recording. The controlled-change alert must be caused by backend processing, not a presentation control.

## Demo integrity
Fake/simulated:
- patient IDs
- ER environment
- wait times
- some background patient feeds

Real:
- video ingestion
- facial tracking
- ROIs
- rPPG
- HR
- RR attempt
- signal confidence
- motion rejection
- baseline
- change detection
- controlled-change alert

Never press a button that directly makes a patient REASSESS.
