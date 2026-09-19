import pytest

from app.models import HeartRateResult
from app.signals.quality import compute_confidence, decide_quality


pytestmark = pytest.mark.milestone3


def _hr(bpm=72.0, snr=8.0, agree=0.9) -> HeartRateResult:
    return HeartRateResult(bpm, 0.0, snr, agree, "pos-welch", 12.0)


def test_confidence_bounds_and_no_face() -> None:
    high = compute_confidence(
        face_present=True, snr=10, roi_agreement=0.95, motion=0.05, illumination=90, valid_ratio=0.95
    )
    none = compute_confidence(
        face_present=False, snr=10, roi_agreement=1.0, motion=0.0, illumination=90, valid_ratio=1.0
    )
    assert 0.0 <= high <= 1.0
    assert high > 0.55
    assert none == 0.0


def test_motion_and_no_face_force_abstention() -> None:
    motion = decide_quality(
        _hr(),
        face_present=True,
        motion=0.9,
        illumination=80,
        valid_ratio=0.95,
        consecutive_clean_seconds=10,
        previously_abstaining=False,
    )
    assert motion.abstaining is True
    assert motion.reason == "motion_artifact"
    assert motion.confidence == 0.0

    no_face = decide_quality(
        _hr(),
        face_present=False,
        motion=0.0,
        illumination=80,
        valid_ratio=1.0,
        consecutive_clean_seconds=10,
        previously_abstaining=False,
    )
    assert no_face.abstaining is True
    assert no_face.reason == "no_face"


def test_recovery_requires_clean_window() -> None:
    early = decide_quality(
        _hr(),
        face_present=True,
        motion=0.05,
        illumination=80,
        valid_ratio=0.95,
        consecutive_clean_seconds=1.0,
        previously_abstaining=True,
    )
    assert early.abstaining is True
    assert early.reason == "recovery_warmup"
    ready = decide_quality(
        _hr(),
        face_present=True,
        motion=0.05,
        illumination=80,
        valid_ratio=0.95,
        consecutive_clean_seconds=5.0,
        previously_abstaining=True,
    )
    assert ready.abstaining is False
    assert ready.recovered is True
