# MASTER CURSOR PROMPT

You are the primary autonomous implementation engineer.

This repository contains the complete product and engineering specification for a five-hour hackathon build. The team wants the functional build complete in the first three hours and will use the remaining two hours for independent QA, refinement, and demo rehearsal.

FIRST ACTION:
Read every specification file completely, in numeric order, before writing code.

Files:
01_PRODUCT_SPEC.md
02_ARCHITECTURE.md
03_SIGNAL_PROCESSING_SPEC.md
04_RESPIRATION_SPEC.md
05_CONFIDENCE_SPEC.md
06_CHANGE_ENGINE_SPEC.md
07_EVM_SPEC.md
08_DATA_SCHEMA.md
09_DASHBOARD_SPEC.md
10_TEST_SPEC.md
11_MILESTONES.md
12_DEMO_SPEC.md
13_FALLBACK_PLAN.md
14_GIT_QA_PROTOCOL.md
15_QA_AGENT_PROMPT.md
17_PRE_HACKATHON_CHECKLIST.md

Then create PROGRESS.md and begin M0.

Also create `QA_RESULTS.md` with an empty structured template. The primary agent owns automated milestone QA. Independent adversarial QA is performed on Laptop B using `15_QA_AGENT_PROMPT.md`; do not claim that self-testing replaces that independent check.

## GLOBAL RULES

1. Implement milestones strictly in order.
2. Do not redesign the product unless a specification is technically impossible.
3. Do not ask the user routine implementation questions. Make the smallest technically sound decision consistent with the specs.
4. Do not implement future milestones before the current milestone gate passes.
5. Keep modules small and testable.
6. Separate webcam/file input from physiology processing.
7. Webcam and MP4 MUST enter the same FramePacket/processing path.
8. Never hardcode a patient into REASSESS.
9. Never fabricate HR or RR.
10. Low-confidence physiology must never affect baseline, trend, change score, or alerts.
11. A failed measurement is preferable to a confident wrong measurement.
12. EVM is required but is a visualization layer, not the numerical HR source.
13. RR is required in V1, but if RR is temporarily invalid, HR and the application must continue.
14. Do not train a pseudo-medical ML model on tiny hackathon data. Implement the ChangeScorer abstraction and a transparent weighted scorer.
15. All thresholds must be configurable and marked as prototype thresholds.
16. Prefer a robust simple implementation over an elaborate fragile one.
17. Do not add authentication, cloud infrastructure, EHR integrations, databases, or other non-goals.
18. Optimize for a repeatable 60-90 second self-guided demo.
19. Treat one-command launch, onboarding, README accuracy, diagnostics, and Judge Mode as P0 requirements, not polish.
20. A camera-denied user must still be able to complete Guided Demo.
21. Guided Demo may control playback and explanations but may never assign measurements, scores, or patient state.
22. Stop all feature work early enough to complete submission before the hard deadline.

## REQUIRED PROJECT STRUCTURE

Create a sensible structure similar to:

app/
  main.py
  config.py
  models.py

  video/
    base.py
    webcam.py
    file.py

  vision/
    face_landmarks.py
    roi.py
    motion.py
    pose.py

  signals/
    buffers.py
    rppg.py
    heart_rate.py
    respiration.py
    quality.py
    evm.py

  monitoring/
    baseline.py
    features.py
    scorer.py
    state_machine.py
    patient.py

  web/
    routes.py
    websocket.py
    templates/
    static/

tests/
  unit/
  fixture/
  integration/

fixtures/

scripts/

PROGRESS.md
QA_RESULTS.md
README.md
run.sh

You may adjust names if needed, but preserve separation of concerns.

## DEPENDENCIES

Prefer:
- Python 3.11+
- opencv-python
- mediapipe
- numpy
- scipy
- fastapi
- uvicorn
- jinja2
- pytest
- httpx / FastAPI TestClient as needed

Avoid unnecessary dependencies.

## IMPLEMENTATION LOOP

For EACH milestone:

A. Read the milestone requirements and gate.
B. Write/complete tests needed for that milestone BEFORE declaring success.
C. Implement the smallest complete version.
D. Run formatting/static checks if configured.
E. Run milestone tests.
F. Run all regression tests from prior milestones.
G. If anything fails:
   1. reproduce
   2. identify root cause
   3. implement smallest correct fix
   4. rerun failed test
   5. rerun milestone suite
   6. rerun regression suite
H. Manually execute a smoke test where automated testing cannot validate hardware behavior.
I. Update PROGRESS.md:
   - current milestone
   - completed requirements
   - passing tests
   - failing tests
   - known limitations
   - next step
J. Only after gate passes:
   git add relevant files
   git commit -m "MILESTONE-X: <description>"
   git push
K. Proceed immediately to the next milestone.

Before committing each milestone, record in PROGRESS.md the exact test commands, pass/fail counts, manual checks performed, and any requirement that degraded to an honest unavailable state. A milestone does not pass merely because the application starts.

Never weaken or delete an acceptance test simply to pass.

## M0
Target: first 15 minutes.
Create environment, architecture, FastAPI shell, tests, VideoSource abstraction, webcam smoke test, executable `run.sh`, `/health`, startup diagnostics, and README quick-start skeleton.
Gate exactly as specified.
Commit/push.

## M1
Target: 30 minutes.
Implement MediaPipe Face Landmarker, three facial ROIs, RGB extraction, motion, overlays.
Use live/video MediaPipe running modes appropriately.
No-face must be safe.
Commit/push only after gate passes.

## M2
Target: 45 minutes.
Implement:
- rolling timestamped buffers
- POS and/or CHROM rPPG
- detrending/filtering
- spectral HR estimation
- multi-ROI fusion
- respiratory-rate estimator
- terminal output

Do not chase perfect accuracy before obtaining a stable end-to-end signal.
Validate against any available fixtures/reference metadata.
Commit/push.

## M3
Target: 25 minutes.
Implement:
- confidence model
- signal quality
- ROI agreement
- abstention
- recovery
- EVM

Required manual behavior:
still -> measurement
move/occlude -> low confidence / no inference
return -> signal reacquired
RAW/EVM visualization works

Commit/push.

## M4
Target: 25 minutes.
Implement:
- baseline
- feature vector
- weighted change scoring
- persistence
- state machine
- explanation reasons

Required tests:
temporary spike -> no reassess
sustained valid deviation -> reassess
low-confidence apparent deviation -> never reassess

Commit/push.

## M5
Target: 30 minutes.
Implement FastAPI dashboard:
- six patient tiles
- WebSocket updates
- patient detail
- video/ROI display
- RAW/EVM toggle
- trend charts
- baseline/current
- why-flagged section
- reassessment popup
- priority sorting
- first-time-user explanation and safety boundary
- Guided Demo and Live Camera entry paths
- metric tooltips and real-vs-simulated panel
- friendly camera/backend error states

Use vanilla JS/CSS; do not introduce Node unless absolutely necessary.

Frontend must display backend state; frontend cannot calculate alert state.

Commit/push.

## M6
Target: 25 minutes.
Integrate complete self-guided demo.

Required end-to-end:
clean start
dashboard
live patient
real HR
real RR attempt
EVM
movement -> abstention
recovery
controlled-change input
backend-detected sustained change
patient moves to top
popup
detail/reasons
guided explanatory stages
pause/restart/skip controls
camera-denied guided path

Run twice from clean launch.
Commit/push:
MILESTONE-6: end-to-end demo ready

## M7
Target: 25 minutes.
Complete Judge Mode:
- harden `./run.sh` for a fresh macOS clone
- finish README quick start and troubleshooting
- expose useful startup diagnostics
- verify Guided Demo without camera access
- verify missing-asset and server-disconnect errors
- make the product understandable without team narration

Laptop B must clone into a new directory, use only README + `./run.sh`, and run the complete experience without coaching. Fix all BLOCKER/HIGH judge-mode failures.

Commit/push:
MILESTONE-7: self-guided judge experience

## AFTER M6
Run complete suite.
Fix BLOCKER/HIGH failures.
Do not add speculative features.

If core is stable and time remains:
- improve UI
- improve smoothing/latency
- attempt iPhone camera input as OPTIONAL enhancement

iPhone support must never destabilize MacBook webcam operation.

Do not attempt iPhone input until M7 passes on both Macs. For the required Loom recording, use the MacBook webcam plus the controlled prerecorded fixture.

## FAILURE PRIORITY

P0:
app launch
one-command clean-clone launch
homepage/onboarding
camera-independent Guided Demo
webcam
face/ROI
HR
confidence/abstention
baseline/change detection
dashboard
controlled-change alert

P1:
RR quality
EVM quality
trend polish
iPhone camera

EVM itself is REQUIRED to exist, but visual perfection is P1.

## DEFINITION OF DONE

The project is done only when:
- app launches cleanly
- automated test suite passes
- webcam path works
- file-video path works
- real HR is demonstrated
- RR pipeline operates and degrades honestly if unreliable
- motion can force abstention
- recovery works
- EVM toggle works
- baseline works
- controlled sustained change can trigger reassessment
- bad signal cannot trigger reassessment
- dashboard shows six patients
- priority patient moves to top
- alert includes reasons
- full demo can be repeated from clean launch
- `./run.sh` is the sole required launch command on the tested Mac
- homepage explains problem, use case, workflow, safety boundary, and real-vs-simulated elements
- Guided Demo works without camera permission
- README exactly matches the tested setup
- Laptop B passes the no-coaching clean-clone test
- milestone QA records exact automated and manual evidence
- the 2-5 minute Loom recording path can be performed using the MacBook webcam and dashboard without iPhone or stock footage

When done:
1. update PROGRESS.md
2. run regression suite
3. run guided demo three times, including once with camera denied
4. complete Laptop B clean-clone test
5. git commit -m "RELEASE: judge-ready-v1"
6. git push

Do not merely tell the user what remains. Continue executing until the definition of done is satisfied or a genuine external blocker makes a requirement impossible.
