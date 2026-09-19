# Product QA

Owner: Rishab / `rishab-product`. Core algorithms are not changed here.

## Commands

```bash
./run.sh
source .venv/bin/activate && python -m pytest tests/unit/test_product_contract.py tests/unit/test_m5_dashboard.py tests/integration/test_m0_startup.py tests/integration/test_m0_health.py
```

## Automated

`python -m pytest tests/unit/test_product_contract.py tests/unit/test_m5_dashboard.py tests/integration/test_m0_startup.py tests/integration/test_m0_health.py tests/unit/test_m0_launcher.py` — 19 passed.

HTTP smoke on `127.0.0.1:8765`: `/`, `/demo`, `/dashboard`, `/live`, `/health`, `/api/product-fixtures` all 200.

## Evidence

- Homepage states problem, ordinary-camera solution, reassessment action, and safety boundary.
- Six tiles: P01 live slot, P04 controlled-change, P02/P03/P05/P06 simulated (not live physiology).
- Frontend reads `PatientMeasurement` / snapshot only. No JS assignment of `REASSESS` or HR.
- `/api/product-fixtures` serves contract-valid samples for UI QA without writing clinic state.
- Guided Demo: start/pause/skip/reset. Reset calls `/api/session/reset` → Core restart of the file pipeline.
- Abstention copy: `Signal unreliable — no inference made.`
- Alert copy: `Reassessment recommended.` Patient moves to top only when backend status is `REASSESS`.
- RR null: `RR unavailable — insufficient signal quality.`
- Disconnect: reconnecting notice; measurements marked not live.
- Camera denied: Guided Demo remains available.

## Known limitations

- Sustained `REASSESS` still depends on Ranveer's Core (last Core test was `STABLE` with score ~0.60).
- Product fixtures are for contract/UI tests, not a fake live alert.
- No Supabase, no ML, no iPhone path.

## Core integration required

- Core must emit real `SIGNAL_UNRELIABLE` on motion/no-face.
- Core must emit real `REASSESS` after sustained high-confidence change on `fixtures/controlled_change.mp4`.
- Same JSON shape as `PatientMeasurement.to_dict()`.
