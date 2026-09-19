from pathlib import Path

import pytest

from app.video.file import FileVideoSource
from tests.conftest import write_solid_video


pytestmark = pytest.mark.milestone0


def test_file_source_reads_synthetic_video(synthetic_video: Path) -> None:
    source = FileVideoSource(synthetic_video, source_id="fixture-P04")
    packets = []
    with source:
        assert source.is_open()
        packets = list(source.frames())
    assert source.is_open() is False
    assert len(packets) >= 8
    assert packets[0].source_id == "fixture-P04"
    assert packets[0].frame_bgr.ndim == 3
    assert packets[0].frame_index == 0
    assert packets[-1].frame_index == len(packets) - 1
    timestamps = [item.timestamp_ms for item in packets]
    assert timestamps == sorted(timestamps)
    assert timestamps[-1] > timestamps[0]


def test_file_source_loop_keeps_monotonic_timestamps(tmp_path: Path) -> None:
    path = write_solid_video(tmp_path / "loop.mp4", n_frames=6, fps=10.0)
    source = FileVideoSource(path, source_id="loop", loop=True)
    timestamps = []
    with source:
        for _ in range(10):
            packet = source.read()
            assert packet is not None
            timestamps.append(packet.timestamp_ms)
    assert timestamps == sorted(timestamps)
    assert timestamps[-1] > timestamps[0]
