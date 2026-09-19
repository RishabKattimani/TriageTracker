# Product Specification

## Objective
Build a hackathon prototype for continuous physiological reassessment of emergency-department waiting-room patients using ordinary video.

The prototype does NOT diagnose, assign a clinical triage level, or claim to detect a specific disease. It detects sustained physiological change from a patient-specific baseline and recommends clinician reassessment.

The first-round submission is judged without the team presenting it. Therefore self-guided usability is P0: a stranger must be able to clone the repository, launch it with one command, understand the use case from the opened page, run a reliable guided demo without a camera, and optionally test the live camera.

## Required judge experience
1. `./run.sh` is the only required launch command on a supported Mac.
2. The script creates/reuses a virtual environment, installs pinned dependencies, verifies required assets, starts the server, waits for health, and opens the browser.
3. The first page explains the problem, solution, processing flow, limitations, and real-versus-simulated elements.
4. The first page offers two obvious actions: `RUN GUIDED DEMO` and `TRY LIVE CAMERA`.
5. Guided Demo works when camera access is unavailable or denied.
6. Guided Demo uses the same real processing interfaces as live video; it may not directly set measurements, scores, or patient state.
7. Common failures produce friendly recovery instructions, never an unexplained traceback.

## Required demo
1. Six-patient waiting-room dashboard.
2. At least one real live webcam feed.
3. Camera detects face and tracks facial regions.
4. Real rPPG produces heart-rate estimates.
5. Real respiratory-rate estimate is attempted from video.
6. Eulerian Video Magnification (EVM) is available as a required visual demo.
7. Deliberate head motion lowers confidence and forces abstention.
8. Returning still causes signal reacquisition.
9. A controlled prerecorded physiological-change video enters the SAME processing pipeline.
10. The system detects a sustained change and moves that patient to the top of the reassessment queue.
11. Dashboard explains WHY the patient was flagged.

## Required measurements/features
- Heart rate
- Heart-rate trend
- Respiratory rate
- Respiratory-rate trend
- Facial motion score
- Signal-quality score
- ROI agreement
- Baseline HR
- Baseline RR
- Deviation from baseline
- Persistence duration
- Change score
- Patient state
- Abstention reason

## Patient states
- INITIALIZING
- BASELINING
- STABLE
- CHANGE_DETECTED
- REASSESS
- SIGNAL_UNRELIABLE

SIGNAL_UNRELIABLE is not an alert state.

## Non-goals
Do not implement:
- diagnosis
- sepsis detection
- heart-attack detection
- blood pressure from camera
- SpO2 from RGB camera
- temperature from RGB camera
- medical decision making
- EHR integration
- authentication
- production deployment
- cloud infrastructure
- multi-camera hospital deployment
- requiring Docker, Node, or multiple terminals to launch
- production-grade installer or cross-platform support beyond the tested Mac setup

## Required wording
Use:
"Physiological change detected."
"Reassessment recommended."
"Signal unreliable — no inference made."

Do not use:
"Patient is deteriorating."
"Patient has sepsis."
"Patient is having a heart attack."
