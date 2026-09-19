"""Webcam VideoSource. Uses the same FramePacket path as file input."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.config import WEBCAM_INDEX
from app.video.base import CameraUnavailable, FramePacket, VideoSource


class WebcamVideoSource(VideoSource):
    def __init__(self, camera_index: int = WEBCAM_INDEX, source_id: str = "webcam") -> None:
        self._camera_index = camera_index
        self._source_id = source_id
        self._cap: cv2.VideoCapture | None = None
        self._frame_index = 0

    @property
    def source_id(self) -> str:
        return self._source_id

    @property
    def camera_index(self) -> int:
        return self._camera_index

    def open(self) -> None:
        cap = cv2.VideoCapture(self._camera_index)
        if not cap.isOpened():
            cap.release()
            raise CameraUnavailable(
                "Camera unavailable. On macOS: System Settings → Privacy & "
                "Security → Camera, enable access for this terminal or browser, "
                "then retry. Guided Demo still works without a camera."
            )
        self._cap = cap
        self._frame_index = 0

    def read(self) -> FramePacket | None:
        if self._cap is None:
            raise RuntimeError("WebcamVideoSource.read() called before open().")
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return None
        packet = FramePacket(
            frame_bgr=np.ascontiguousarray(frame),
            timestamp_ms=time.time() * 1000.0,
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


def probe_webcam(camera_index: int = WEBCAM_INDEX, timeout_frames: int = 3) -> dict:
    """Best-effort camera probe for startup diagnostics. Never raises."""
    source = WebcamVideoSource(camera_index=camera_index, source_id="probe")
    try:
        source.open()
        grabbed = 0
        width = height = 0
        for _ in range(timeout_frames):
            packet = source.read()
            if packet is None:
                break
            grabbed += 1
            height, width = packet.frame_bgr.shape[:2]
        return {
            "available": grabbed > 0,
            "camera_index": camera_index,
            "frames_grabbed": grabbed,
            "width": width,
            "height": height,
            "message": "Camera opened and delivered frames."
            if grabbed
            else "Camera opened but delivered no frames.",
        }
    except CameraUnavailable as exc:
        return {
            "available": False,
            "camera_index": camera_index,
            "frames_grabbed": 0,
            "width": 0,
            "height": 0,
            "message": str(exc),
        }
    finally:
        source.close()
