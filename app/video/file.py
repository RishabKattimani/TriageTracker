"""File-backed VideoSource. Webcam and MP4 share the FramePacket contract."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.video.base import FramePacket, VideoSource


class FileVideoSource(VideoSource):
    def __init__(
        self,
        path: str | Path,
        source_id: str = "file",
        *,
        loop: bool = False,
    ) -> None:
        self._path = Path(path)
        self._source_id = source_id
        self._loop = loop
        self._cap: cv2.VideoCapture | None = None
        self._frame_index = 0
        self._fps = 30.0

    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def path(self) -> Path:
        return self._path

    def open(self) -> None:
        if not self._path.is_file():
            raise FileNotFoundError(
                f"Video file not found: {self._path}. "
                "Place the fixture in fixtures/ or pass a valid path."
            )
        cap = cv2.VideoCapture(str(self._path))
        if not cap.isOpened():
            raise RuntimeError(
                f"Could not open video file: {self._path}. "
                "The file may be corrupt or an unsupported codec."
            )
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        self._fps = fps if fps > 1e-3 else 30.0
        self._cap = cap
        self._frame_index = 0

    def read(self) -> FramePacket | None:
        if self._cap is None:
            raise RuntimeError("FileVideoSource.read() called before open().")
        ok, frame = self._cap.read()
        if not ok or frame is None:
            if not self._loop:
                return None
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
            if not ok or frame is None:
                return None
        # File timestamps are frame-index based so looping stays monotonic even
        # when CAP_PROP_POS_MSEC does not reset on rewind.
        timestamp_ms = self._frame_index * (1000.0 / self._fps)
        packet = FramePacket(
            frame_bgr=np.ascontiguousarray(frame),
            timestamp_ms=timestamp_ms,
            source_id=self._source_id,
            frame_index=self._frame_index,
        )
        self._frame_index += 1
        return packet

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()
