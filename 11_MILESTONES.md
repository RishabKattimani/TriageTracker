# Milestones — Target: judge-ready build in 3 hours 40 minutes

The two-hour target is not a valid planning assumption. Aim for a functional core by approximately hour three and a clean-clone Judge Mode by hour 3:40. If behind, degrade optional quality honestly rather than skipping confidence, tests, or controlled-change integrity.

## M0 — Foundation (0:00-0:15)
Build:
- repo structure
- virtual environment/dependencies
- test runner
- config
- FastAPI skeleton
- VideoSource abstraction
- webcam smoke test
- executable `run.sh`
- `/health` endpoint and startup diagnostics
- README quick-start skeleton

Gate:
- app starts
- tests run
- webcam opens
- Git remote works
- `./run.sh` launches the skeleton and opens the browser

Commit:
MILESTONE-0: foundation operational

## M1 — Vision / ROIs (0:15-0:45)
Build:
- MediaPipe Face Landmarker
- forehead/cheek ROIs
- RGB extraction
- face motion estimate
- debug overlay

Gate:
- face detected
- 3 ROIs visible
- RGB values emitted
- no-face handled
- 60-second run no crash

Commit:
MILESTONE-1: face tracking and ROI extraction

## M2 — Physiology (0:45-1:30)
Build:
- POS/CHROM
- detrending/bandpass
- HR estimator
- respiration estimator
- rolling buffers
- terminal output

Required first meaningful terminal:
PATIENT P01
HR: <value or unavailable>
RR: <value or unavailable>
SIGNAL QUALITY: <value>
MOTION: <value>

Gate:
- stable webcam produces HR
- file source produces measurements
- RR pipeline operates
- no fabricated output

Commit:
MILESTONE-2: physiological signal engine

## M3 — Reliability + EVM (1:30-1:55)
Build:
- signal confidence
- ROI agreement
- abstention
- reacquisition
- EVM visualizer

Gate:
- movement lowers confidence
- severe movement abstains
- recovery works
- EVM toggle works

Commit:
MILESTONE-3: confidence abstention and EVM

## M4 — Baseline / fusion (1:55-2:20)
Build:
- baseline manager
- feature vector
- weighted change scorer
- persistence
- state machine
- reasons/explainability

Gate:
- short spike no alert
- sustained valid deviation alerts
- invalid spike never alerts

Commit:
MILESTONE-4: baseline and reassessment engine

## M5 — Dashboard + onboarding (2:20-2:50)
Build:
- six-patient dashboard
- patient detail page/panel
- WebSocket live updates
- trends
- alert popup
- reasons panel
- raw/EVM toggle
- explanatory homepage content
- Guided Demo / Live Camera entry buttons
- tooltips and real-vs-simulated panel
- camera-denied and disconnected states

Gate:
- live data renders
- priority patient moves to top
- popup caused by backend state
- first-time user understands use case and safety boundary

Commit:
MILESTONE-5: live waiting-room dashboard

## M6 — End-to-end guided demo (2:50-3:15)
Build/integrate:
- live webcam patient
- stable prerecorded feeds/states
- controlled-change video
- complete demo sequence
- guided narration/overlays and replay controls
- no-camera path

Gate:
- clean launch
- movement -> abstention
- recovery
- controlled change -> reassessment
- dashboard prioritizes patient
- guided demo completes without team narration
- no UI action directly sets REASSESS

Commit:
MILESTONE-6: end-to-end demo ready

## M7 — Judge mode + clean install (3:15-3:40)
Build/finish:
- robust `run.sh`
- complete README
- friendly startup diagnostics
- clean-clone compatibility
- repeatable guided demo

Gate on Laptop B:
- delete/rename existing checkout
- clone remote into a new folder
- use README only
- run `./run.sh`
- complete Guided Demo with camera disabled
- complete Live Camera flow
- rerun Guided Demo three times
- no verbal assistance from Laptop A

Commit:
MILESTONE-7: self-guided judge experience

## Remaining time to 4:15 — Human QA and fixes
No feature expansion unless fixing critical demo failures.

## 4:15-4:30 — Submission assets
Allowed:
- record the required 2-5 minute Loom video
- capture screenshots
- write submission description
- verify repository visibility/access

For this event, the required Loom submission video may be 2-5 minutes. Target 3-3.5 minutes and begin recording no later than hour 4:15.

## 4:30 — HARD FREEZE

## 4:30-5:00
- final fresh clone/run
- full regression
- demo run repeatedly
- fallback run
- upload/submit with buffer before the deadline

Required final clock plan for a 10:00 AM-3:00 PM event:
- 10:00-1:40 build through M7
- 1:40-2:15 adversarial QA and fixes
- 2:15-2:30 record Loom and screenshots
- 2:30 hard feature freeze
- 2:30-2:50 final clone, regression, and submission
- 2:50-3:00 emergency buffer

No iPhone experiment unless M7 passes early and it cannot affect the Mac path.
