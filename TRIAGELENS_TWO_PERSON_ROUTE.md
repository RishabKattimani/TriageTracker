# TriageTracker — Two-Person Split

One GitHub repo. One local FastAPI app. No Supabase. No machine learning.

## Ranveer — Core
Real physiology. Do not polish the dashboard.

1. webcam / MP4 -> face -> ROIs
2. RGB -> rPPG -> HR
3. signal quality
4. motion -> abstain -> reacquire
5. EVM (small face crop is enough)
6. baseline + weighted change engine
7. emit `PatientMeasurement` JSON

Primary gap: sustained high-confidence change must become `REASSESS` without hardcoding it.

## Partner — Product
Complete judge-facing product. Do not tune signal algorithms.

1. six-patient waiting-room UI
2. WebSocket updates from backend state
3. attention queue / why-flagged
4. patient detail
5. Guided Demo + reset
6. live camera page
7. `./run.sh` / README

The UI must never assign `REASSESS` or invent HR.

## Contract
`app/models.py` `PatientMeasurement.to_dict()`.

## Integration
Core emits real measurements. Product only renders them.
Checkpoint: no-face / motion abstains; sustained valid change flags; reset replays the fixture.
