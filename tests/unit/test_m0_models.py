import pytest

from app.models import PatientMeasurement, PatientStatus


pytestmark = pytest.mark.milestone0


def test_status_enum_matches_schema() -> None:
    assert {item.value for item in PatientStatus} == {
        "INITIALIZING",
        "BASELINING",
        "STABLE",
        "CHANGE_DETECTED",
        "REASSESS",
        "SIGNAL_UNRELIABLE",
    }
    assert PatientStatus.SIGNAL_UNRELIABLE.is_alert_state() is False
    assert PatientStatus.REASSESS.is_alert_state() is True


def test_measurement_serializes_null_physiology_when_abstaining() -> None:
    measurement = PatientMeasurement(
        patient_id="P01",
        timestamp=1.0,
        heart_rate=None,
        respiratory_rate=None,
        abstaining=True,
        abstention_reason="no_face",
        status=PatientStatus.SIGNAL_UNRELIABLE,
    )
    payload = measurement.to_dict()
    assert payload["heart_rate"] is None
    assert payload["respiratory_rate"] is None
    assert payload["abstaining"] is True
    assert payload["status"] == "SIGNAL_UNRELIABLE"
    restored = PatientMeasurement.from_dict(payload)
    assert restored.status is PatientStatus.SIGNAL_UNRELIABLE
    assert restored.heart_rate is None


def test_invalid_features_are_none_not_zero() -> None:
    measurement = PatientMeasurement(patient_id="P04", timestamp=0.0)
    payload = measurement.to_dict()
    assert payload["heart_rate"] is None
    assert payload["heart_rate_delta_pct"] is None
    assert payload["change_score"] is None
    assert payload["baseline_heart_rate"] is None
