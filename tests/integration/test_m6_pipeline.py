from pathlib import Path

import numpy as np
import pytest

from app.models import FrameObservation, PatientStatus, RGBSample
from app.monitoring.patient import PatientMonitor
from app.synth import CONTROLLED_META, write_pulse_video, write_sidecar
from app.video.file import FileVideoSource
from app.vision.processor import FrameProcessor


pytestmark = pytest.mark.milestone6


def _pulse_obs(index: int, hz: float, motion: float = 0.04) -> FrameObservation:
    t = index / 30.0
    pulse = 0.5 * np.sin(2 * np.pi * hz * t)
    sample = RGBSample(r=180 + 4 * pulse, g=140 + 28 * pulse, b=110 + 2 * pulse)
    return FrameObservation(
        face_present=True,
        face_landmarks=None,
        forehead_rgb=sample,
        left_cheek_rgb=sample,
        right_cheek_rgb=sample,
        facial_motion=motion,
        illumination=90.0,
        torso_motion_signal=None,
        debug_overlay_frame=None,
        timestamp_ms=t * 1000.0,
        source_id="synth",
        frame_index=index,
        face_bbox=(40, 30, 80, 100),
    )


def test_low_confidence_motion_never_reassesses() -> None:
    monitor = PatientMonitor("P-motion")
    for i in range(900):
        monitor.ingest(_pulse_obs(i, 1.2, motion=0.9))
    assert monitor.latest.abstaining is True
    assert monitor.latest.status != PatientStatus.REASSESS
    assert monitor.latest.heart_rate is None
    assert monitor.baseline.ready is False


def test_sustained_valid_pulse_change_can_reassess() -> None:
    monitor = PatientMonitor("P-change")
    for i in range(30 * 40):
        monitor.ingest(_pulse_obs(i, 1.2))
    for i in range(30 * 40, 30 * 90):
        monitor.ingest(_pulse_obs(i, 1.833))
    assert monitor.latest.status == PatientStatus.REASSESS, (
        f"status={monitor.latest.status} hr={monitor.latest.heart_rate} "
        f"base={monitor.latest.baseline_heart_rate} score={monitor.latest.change_score} "
        f"persist={monitor.latest.persistence_seconds} abstain={monitor.latest.abstaining} "
        f"{monitor.latest.abstention_reason}"
    )
    assert monitor.latest.heart_rate is not None
    assert monitor.latest.change_score is not None
    assert any("Heart rate" in reason for reason in monitor.latest.reasons)


def test_file_and_processor_share_path_and_no_face_is_safe(tmp_path: Path) -> None:
    video = write_pulse_video(tmp_path / "dark.mp4", segments=[(2.0, 1.2)], dark=True)
    write_sidecar(video, {"kind": "no_face"})
    source = FileVideoSource(video, source_id="dark")
    processor = FrameProcessor(fixture_meta={"kind": "no_face"})
    monitor = PatientMonitor("P-dark")
    with source, processor:
        for packet in source.frames():
            monitor.ingest(processor.process(packet))
    assert monitor.latest.heart_rate is None
    assert monitor.latest.abstaining is True
    assert monitor.latest.status not in {PatientStatus.CHANGE_DETECTED, PatientStatus.REASSESS}


def test_synthetic_fixture_extracts_real_rgb(tmp_path: Path) -> None:
    video = write_pulse_video(tmp_path / "pulse.mp4", segments=[(3.0, 1.2)])
    write_sidecar(video, CONTROLLED_META)
    source = FileVideoSource(video, source_id="pulse")
    processor = FrameProcessor(fixture_meta=CONTROLLED_META)
    seen = 0
    with source, processor:
        for packet in source.frames():
            obs = processor.process(packet)
            if obs.face_present and obs.forehead_rgb is not None:
                seen += 1
    assert seen >= 10
