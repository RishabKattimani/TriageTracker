from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.models import FramePacket
from app.video.base import VideoSource


class FakeVideoSource(VideoSource):
    """Test double that never opens cv2.VideoCapture."""

    def __init__(self, frames: list[np.ndarray], source_id: str = "fake", fps: float = 30.0) -> None:
        self._frames = frames
        self._source_id = source_id
        self._fps = fps
        self._index = 0
        self._open = False

    @property
    def source_id(self) -> str:
        return self._source_id

    def open(self) -> None:
        self._open = True
        self._index = 0

    def read(self) -> FramePacket | None:
        if not self._open:
            raise RuntimeError("FakeVideoSource.read() before open()")
        if self._index >= len(self._frames):
            return None
        frame = self._frames[self._index]
        packet = FramePacket(
            frame_bgr=frame,
            timestamp_ms=self._index * (1000.0 / self._fps),
            source_id=self._source_id,
            frame_index=self._index,
        )
        self._index += 1
        return packet

    def close(self) -> None:
        self._open = False

    def is_open(self) -> bool:
        return self._open


def write_solid_video(path: Path, n_frames: int = 12, fps: float = 10.0, size: tuple[int, int] = (64, 48)) -> Path:
    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not writer.isOpened():
        raise RuntimeError(f"Could not create test video at {path}")
    for index in range(n_frames):
        frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        frame[:, :] = (20 + index * 8, 40, 90)
        writer.write(frame)
    writer.release()
    return path


@pytest.fixture
def fake_source() -> FakeVideoSource:
    frames = [np.full((24, 32, 3), fill_value=i, dtype=np.uint8) for i in range(5)]
    return FakeVideoSource(frames, source_id="unit-fake")


@pytest.fixture
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


@pytest.fixture
def synthetic_video(tmp_path: Path) -> Path:
    return write_solid_video(tmp_path / "synthetic.mp4")
