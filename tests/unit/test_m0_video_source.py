from pathlib import Path

import numpy as np
import pytest

from app.models import FramePacket
from app.video.base import CameraUnavailable, VideoSource
from app.video.file import FileVideoSource
from app.video.webcam import WebcamVideoSource


pytestmark = pytest.mark.milestone0


def test_video_source_is_abstract() -> None:
    with pytest.raises(TypeError):
        VideoSource()  # type: ignore[abstract]


def test_fake_source_emits_frame_packets(fake_source) -> None:
    packets = []
    with fake_source as source:
        packets = list(source.frames())
    assert len(packets) == 5
    first = packets[0]
    assert isinstance(first, FramePacket)
    assert first.source_id == "unit-fake"
    assert first.frame_index == 0
    assert first.frame_bgr.shape == (24, 32, 3)
    assert packets[-1].timestamp_ms > first.timestamp_ms
    timestamps = [item.timestamp_ms for item in packets]
    assert timestamps == sorted(timestamps)


def test_file_source_missing_path_is_explicit(tmp_path: Path) -> None:
    source = FileVideoSource(tmp_path / "missing.mp4", source_id="missing")
    with pytest.raises(FileNotFoundError, match="missing.mp4"):
        source.open()


def test_webcam_invalid_index_is_friendly(monkeypatch: pytest.MonkeyPatch) -> None:
    class ClosedCapture:
        def isOpened(self) -> bool:
            return False

        def release(self) -> None:
            return None

    monkeypatch.setattr("app.video.webcam.cv2.VideoCapture", lambda _index: ClosedCapture())
    source = WebcamVideoSource(camera_index=97, source_id="no-cam")
    with pytest.raises(CameraUnavailable, match="Guided Demo"):
        source.open()
    assert source.is_open() is False


def test_webcam_and_file_share_the_same_contract() -> None:
    assert issubclass(WebcamVideoSource, VideoSource)
    assert issubclass(FileVideoSource, VideoSource)


def test_physiology_packages_do_not_open_video_capture() -> None:
    """Guardrail: later physiology modules must consume FramePacket only."""
    roots = [
        Path("app/signals"),
        Path("app/monitoring"),
    ]
    offenders = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "VideoCapture" in text:
                offenders.append(str(path))
    assert offenders == []
