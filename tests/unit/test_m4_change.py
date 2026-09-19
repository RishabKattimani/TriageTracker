import pytest

from app.models import FeatureVector, PatientStatus
from app.monitoring.baseline import BaselineManager
from app.monitoring.scorer import WeightedRuleChangeScorer
from app.monitoring.state_machine import PatientStateMachine
from app.monitoring.patient import PatientMonitor
from app.models import FrameObservation, RGBSample


pytestmark = pytest.mark.milestone4


def _features(**overrides) -> FeatureVector:
    data = dict(
        hr_delta_pct=0.35,
        hr_slope=0.4,
        hr_confidence=0.9,
        rr_delta_pct=None,
        rr_slope=None,
        rr_confidence=0.0,
        motion_score=0.08,
        roi_agreement=0.9,
        signal_quality=0.88,
        persistence_seconds=18.0,
    )
    data.update(overrides)
    return FeatureVector(**data)


def test_baseline_ignores_low_confidence_and_uses_median() -> None:
    mgr = BaselineManager(duration_seconds=20, min_samples=3)
    for i, hr in enumerate((70, 72, 200, 74)):
        mgr.update(float(i), hr=hr, hr_conf=0.9 if hr != 200 else 0.1, rr=None, rr_conf=0.0, abstaining=False)
    mgr.update(21.0, hr=73, hr_conf=0.9, rr=None, rr_conf=0.0, abstaining=False)
    assert mgr.ready is True
    assert mgr.heart_rate == pytest.approx(72.5, abs=2.0)
    assert 200 not in mgr._hr


def test_temporary_spike_does_not_reassess() -> None:
    machine = PatientStateMachine()
    t = 0.0
    for _ in range(5):
        t += 1.0
        machine.update(timestamp=t, dt=1.0, baseline_ready=True, change_score=0.85, abstaining=False, recovered=False)
    assert machine.trustworthy != PatientStatus.REASSESS
    for _ in range(5):
        t += 1.0
        machine.update(timestamp=t, dt=1.0, baseline_ready=True, change_score=0.1, abstaining=False, recovered=False)
    assert machine.trustworthy != PatientStatus.REASSESS
    assert machine.persistence == 0.0


def test_sustained_high_confidence_deviation_reassesses() -> None:
    machine = PatientStateMachine()
    t = 0.0
    status = PatientStatus.STABLE
    for _ in range(20):
        t += 1.0
        status = machine.update(
            timestamp=t, dt=1.0, baseline_ready=True, change_score=0.82, abstaining=False, recovered=False
        )
    assert status == PatientStatus.REASSESS
    scorer = WeightedRuleChangeScorer()
    result = scorer.score(_features())
    assert result.contributing is True
    assert result.score is not None and result.score >= 0.7
    assert any("Heart rate" in reason for reason in result.reasons)


def test_low_confidence_never_reassesses() -> None:
    scorer = WeightedRuleChangeScorer()
    result = scorer.score(_features(hr_confidence=0.2, hr_delta_pct=0.8, persistence_seconds=40))
    assert result.contributing is False
    assert result.score is None
    machine = PatientStateMachine()
    status = machine.update(
        timestamp=10.0, dt=1.0, baseline_ready=True, change_score=None, abstaining=True, recovered=False
    )
    assert status == PatientStatus.SIGNAL_UNRELIABLE
    assert machine.trustworthy != PatientStatus.REASSESS


def test_no_face_monitor_never_alerts() -> None:
    monitor = PatientMonitor("P99")
    for i in range(40):
        obs = FrameObservation(
            face_present=False,
            face_landmarks=None,
            forehead_rgb=None,
            left_cheek_rgb=None,
            right_cheek_rgb=None,
            facial_motion=0.0,
            illumination=0.0,
            torso_motion_signal=None,
            debug_overlay_frame=None,
            timestamp_ms=i * 33.3,
            source_id="none",
            frame_index=i,
        )
        measurement = monitor.ingest(obs)
    assert measurement.heart_rate is None
    assert measurement.respiratory_rate is None
    assert measurement.abstaining is True
    assert measurement.status not in {PatientStatus.CHANGE_DETECTED, PatientStatus.REASSESS}
