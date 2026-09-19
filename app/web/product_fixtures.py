"""Contract-valid measurement samples for product UI tests. Not live physiology."""

from __future__ import annotations

from app.models import PatientMeasurement, PatientStatus


REQUIRED_FIELDS = (
    "patient_id",
    "timestamp",
    "heart_rate",
    "heart_rate_confidence",
    "respiratory_rate",
    "respiratory_confidence",
    "motion_score",
    "roi_agreement",
    "signal_quality",
    "baseline_heart_rate",
    "baseline_respiratory_rate",
    "heart_rate_delta_pct",
    "respiratory_rate_delta_pct",
    "persistence_seconds",
    "change_score",
    "status",
    "abstaining",
    "abstention_reason",
    "reasons",
)


def _base(**overrides) -> dict:
    measurement = PatientMeasurement(
        patient_id=overrides.pop("patient_id", "P04"),
        timestamp=overrides.pop("timestamp", 12.0),
        **overrides,
    )
    payload = measurement.to_dict()
    payload["wait_minutes"] = 33
    payload["simulated"] = False
    payload["processed"] = True
    return payload


def contract_samples() -> dict[str, dict]:
    return {
        "initializing": _base(status=PatientStatus.INITIALIZING, heart_rate=None, respiratory_rate=None),
        "baselining": _base(
            status=PatientStatus.BASELINING,
            heart_rate=72.0,
            heart_rate_confidence=0.8,
            respiratory_rate=None,
        ),
        "stable": _base(
            status=PatientStatus.STABLE,
            heart_rate=74.0,
            heart_rate_confidence=0.86,
            baseline_heart_rate=73.0,
            heart_rate_delta_pct=0.014,
        ),
        "change_detected": _base(
            status=PatientStatus.CHANGE_DETECTED,
            heart_rate=96.0,
            heart_rate_confidence=0.88,
            baseline_heart_rate=74.0,
            heart_rate_delta_pct=0.30,
            persistence_seconds=10.0,
            change_score=0.61,
            reasons=["Physiological change detected.", "Heart rate +30% from baseline"],
        ),
        "reassess": _base(
            status=PatientStatus.REASSESS,
            heart_rate=108.0,
            heart_rate_confidence=0.91,
            baseline_heart_rate=74.0,
            heart_rate_delta_pct=0.46,
            persistence_seconds=18.0,
            change_score=0.84,
            roi_agreement=0.9,
            motion_score=0.08,
            reasons=[
                "Reassessment recommended.",
                "Heart rate +46% from baseline",
                "Change persisted for 18 seconds",
                "Signal confidence high",
            ],
        ),
        "unreliable": _base(
            status=PatientStatus.SIGNAL_UNRELIABLE,
            heart_rate=None,
            respiratory_rate=None,
            abstaining=True,
            abstention_reason="motion_artifact",
            reasons=["Signal unreliable — no inference made.", "motion_artifact"],
        ),
        "null_rr": _base(
            status=PatientStatus.STABLE,
            heart_rate=70.0,
            heart_rate_confidence=0.8,
            respiratory_rate=None,
            baseline_heart_rate=70.0,
        ),
    }


def product_fixture_snapshot() -> dict:
    samples = contract_samples()
    patients = [
        {**samples["baselining"], "patient_id": "P01", "wait_minutes": 6},
        {**_base(patient_id="P02", status=PatientStatus.STABLE), "simulated": True, "processed": False, "wait_minutes": 18, "heart_rate": None, "reasons": ["Simulated waiting-room tile. Not live physiology."]},
        {**_base(patient_id="P03", status=PatientStatus.STABLE), "simulated": True, "processed": False, "wait_minutes": 41, "heart_rate": None, "reasons": ["Simulated waiting-room tile. Not live physiology."]},
        samples["reassess"],
        {**_base(patient_id="P05", status=PatientStatus.STABLE), "simulated": True, "processed": False, "wait_minutes": 27, "heart_rate": None, "reasons": ["Simulated waiting-room tile. Not live physiology."]},
        {**_base(patient_id="P06", status=PatientStatus.STABLE), "simulated": True, "processed": False, "wait_minutes": 9, "heart_rate": None, "reasons": ["Simulated waiting-room tile. Not live physiology."]},
    ]
    return {
        "type": "snapshot",
        "waiting": 6,
        "reassess_count": 1,
        "patients": patients,
        "note": "Product fixtures only. Backend owns live REASSESS. Frontend must not assign it.",
    }
