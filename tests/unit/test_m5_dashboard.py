from pathlib import Path

import pytest

from app.clinic import clinic
from app.models import PatientStatus


pytestmark = pytest.mark.milestone5

JS = Path("app/web/static/app.js").read_text(encoding="utf-8")


def test_frontend_cannot_assign_reassess() -> None:
    forbidden = [
        'status = "REASSESS"',
        "status = 'REASSESS'",
        'status:"REASSESS"',
        ".status = \"REASSESS\"",
        "patient.status =",
    ]
    for item in forbidden:
        assert item not in JS
    assert "Backend owns patient state" in JS or "never assign REASSESS" in JS.lower() or "must never assign REASSESS" in JS


def test_dashboard_and_api_snapshot(client) -> None:
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert "Why flagged" in page.text
    assert "cannot assign REASSESS" in page.text
    snap = client.get("/api/patients")
    assert snap.status_code == 200
    payload = snap.json()
    assert payload["type"] == "snapshot"
    assert payload["waiting"] == 6
    assert len(payload["patients"]) == 6
    ids = {p["patient_id"] for p in payload["patients"]}
    assert ids == {"P01", "P02", "P03", "P04", "P05", "P06"}
    background = [p for p in payload["patients"] if p["simulated"]]
    assert len(background) == 4
    assert all(p["status"] != PatientStatus.REASSESS.value for p in background)


def test_websocket_snapshot_is_backend_owned(client) -> None:
    with client.websocket_connect("/ws/telemetry") as socket:
        hello = socket.receive_json()
        assert hello["type"] == "hello"
        assert "REASSESS" in hello["note"]
        snap = socket.receive_json()
    assert snap["type"] == "snapshot"
    assert "patients" in snap


def test_clinic_priority_sorts_reassess_first() -> None:
    from app.models import PatientMeasurement

    clinic.monitors["P04"].latest = PatientMeasurement(
        patient_id="P04",
        timestamp=1.0,
        status=PatientStatus.REASSESS,
        change_score=0.9,
        reasons=["Heart rate +32% from baseline"],
    )
    snap = clinic.snapshot()
    assert snap["patients"][0]["patient_id"] == "P04"
    assert snap["patients"][0]["status"] == "REASSESS"
    clinic.monitors["P04"].reset()
