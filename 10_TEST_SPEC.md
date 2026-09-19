# Test Specification

Tests are defined BEFORE implementation.

## Unit tests
- ROI polygon extraction
- RGB mean extraction
- timestamp handling
- signal filtering
- BPM conversion
- RR conversion
- confidence bounds
- baseline median
- delta calculation
- persistence timer
- state transitions
- serialization
- WebSocket schema

## Fixture tests

### No face
Expected:
- no physiology output
- abstention
- `heart_rate` and `respiratory_rate` are null
- `abstaining` is true
- status never becomes `CHANGE_DETECTED` or `REASSESS`

### Stable face
Expected:
- HR eventually produced
- confidence reaches valid range
- output appears only after the configured minimum valid window
- returned confidence remains within 0.0-1.0

### Head movement
Expected:
- motion score rises
- confidence falls
- if severe: abstention
- no baseline, trend, persistence, or change-score update while abstaining

### Recovery
Expected:
- valid signal resumes after sufficient clean frames
- UI/backend emits `SIGNAL REACQUIRED`
- recovery occurs only after the configurable clean-data window

### Dark scene
Expected:
- quality falls
- system requests better signal / abstains

### Talking
Expected:
- RR confidence likely falls
- no false high-confidence alert

### Temporary spike
Expected:
- no REASSESS state
- persistence resets or decays according to config

### Sustained high-confidence deviation
Expected:
- CHANGE_DETECTED then REASSESS
- transition occurs only after the configured persistence threshold

### Low-confidence apparent spike
Expected:
- NEVER REASSESS
- baseline and trend remain unchanged for the invalid samples

### File repeatability
Same fixture run twice should produce materially similar outputs.

Define `materially similar` in test configuration before implementation. For deterministic file input, compare state-transition sequence exactly and numeric outputs within explicit configurable tolerances. Never let the test decide its tolerance after seeing implementation output.

## Integration tests
- FastAPI starts
- dashboard route loads
- WebSocket connects
- valid measurement JSON arrives
- dashboard accepts state
- no-face does not crash
- video file source works
- webcam source works
- raw/EVM endpoint or view works
- `/health` reports readiness and required asset status
- guided demo route works with camera disabled
- homepage contains problem, use case, safety boundary, and both primary actions
- guided demo uses file `VideoSource` and real backend state
- frontend cannot directly set REASSESS
- server disconnect shows a recoverable UI state

## Judge-mode acceptance tests

Run on Laptop B from a new clone with no existing virtual environment:
1. `./run.sh` is the only setup/launch command.
2. Browser opens after health becomes ready.
3. A stranger can identify the problem, solution, limitations, and first action within 15 seconds.
4. Guided Demo completes with camera permission denied.
5. The controlled-change fixture produces backend measurements and backend state transitions.
6. Guided Demo can restart and complete three consecutive times.
7. Live mode explains camera permission and recovers after permission is granted.
8. Missing fixture/model causes a friendly diagnostic and nonzero launcher exit where appropriate.
9. Interrupting `run.sh` cleans up the local server.
10. README commands exactly match tested behavior.

Anything requiring verbal help from the team is a failed judge-mode test.

## Milestone test ownership

- M0: startup, health, VideoSource contract, launcher smoke tests
- M1: landmarks, ROI geometry, RGB extraction, no-face behavior
- M2: buffers, filters, frequency/BPM conversion, fixture measurements
- M3: confidence, abstention, recovery, EVM smoke test
- M4: baseline, persistence, scoring, state-machine transitions
- M5: routes, WebSocket schema, dashboard rendering, backend-owned status
- M6: complete guided flow and controlled-change integration
- M7: clean-clone, no-camera, README, launcher, repeatability

Cursor must create or complete the relevant tests before declaring each milestone complete, then run that milestone suite plus the entire prior regression suite.

## Regression rule
After each milestone:
1. milestone tests
2. entire prior suite

Tests must not be deleted/weakened merely to obtain a pass.
