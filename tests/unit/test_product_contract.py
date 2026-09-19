from pathlib import Path

import pytest

from app.models import PatientMeasurement, PatientStatus
from app.web.product_fixtures import REQUIRED_FIELDS, contract_samples, product_fixture_snapshot


pytestmark = pytest.mark.milestone5

JS = Path("app/web/static/app.js").read_text(encoding="utf-8")


def test_contract_samples_match_schema() -> None:
    samples = contract_samples()
    for name, payload in samples.items():
        for field in REQUIRED_FIELDS:
            assert field in payload, f"{name} missing {field}"
        restored = PatientMeasurement.from_dict(
            {k: payload[k] for k in REQUIRED_FIELDS}
        )
        assert restored.status in PatientStatus
        assert 0.0 <= restored.heart_rate_confidence <= 1.0


def test_unreliable_is_not_an_alert_and_hr_is_null() -> None:
    sample = contract_samples()["unreliable"]
    assert sample["status"] == "SIGNAL_UNRELIABLE"
    assert sample["heart_rate"] is None
    assert sample["respiratory_rate"] is None
    assert sample["abstaining"] is True
    assert PatientStatus.SIGNAL_UNRELIABLE.is_alert_state() is False


def test_product_fixture_snapshot_does_not_hardcode_via_ui() -> None:
    snap = product_fixture_snapshot()
    assert snap["waiting"] == 6
    assert len(snap["patients"]) == 6
    simulated = [p for p in snap["patients"] if p["simulated"]]
    assert len(simulated) == 4
    assert all(p["status"] != "REASSESS" for p in simulated)
    assert all(p["heart_rate"] is None for p in simulated)


def test_frontend_cannot_assign_physiology_or_reassess() -> None:
    forbidden = [
        'status = "REASSESS"',
        "status = 'REASSESS'",
        "patient.status = \"",
        "heart_rate = 98",
        "change_score = 0",
    ]
    for item in forbidden:
        assert item not in JS
    assert "must never assign REASSESS" in JS


def test_product_fixture_route(client) -> None:
    response = client.get("/api/product-fixtures")
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "product-fixtures"
    assert "reassess" in payload["samples"]
    assert payload["samples"]["reassess"]["status"] == "REASSESS"
    assert "must not assign REASSESS" in payload["note"]


def test_homepage_and_demo_copy(client) -> None:
    home = client.get("/").text
    assert "Triage is a snapshot. Patients keep changing." in home
    assert "Decision support only" in home
    assert "RUN GUIDED DEMO" in home
    assert "TRY LIVE CAMERA" in home
    demo = client.get("/demo").text
    assert "cannot assign REASSESS" in demo
    assert "RESET DEMO" in demo
    assert "TRY LIVE CAMERA" in demo


def test_dashboard_handles_backend_statuses(client) -> None:
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert "Why flagged" in page.text
    assert "Technical proof" in page.text
    assert "cannot assign REASSESS" in page.text
