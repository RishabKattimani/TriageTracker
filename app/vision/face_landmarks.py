"""MediaPipe Face Landmarker. VIDEO mode for webcam and files (monotonic timestamps)."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app import config


def _mp_image(frame_bgr: np.ndarray):
    import mediapipe as mp

    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))


class FaceLandmarkService:
    def __init__(self, model_path: Path | None = None, *, live: bool = False) -> None:
        self.model_path = Path(model_path or config.FACE_LANDMARKER_MODEL)
        self.live = live
        self._landmarker = None
        self._available = self.model_path.is_file()
        self._last_error: str | None = None
        self._last_ts = -1

    @property
    def available(self) -> bool:
        return self._available

    def open(self) -> None:
        if not self._available:
            self._last_error = f"Face landmarker model missing: {self.model_path}"
            return
        try:
            from mediapipe.tasks.python.core.base_options import BaseOptions
            from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode
        except Exception as exc:
            self._last_error = str(exc)
            self._available = False
            return

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.4,
            min_face_presence_confidence=0.4,
            min_tracking_confidence=0.4,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        try:
            self._landmarker = FaceLandmarker.create_from_options(options)
        except Exception as exc:
            self._last_error = str(exc)
            self._available = False
            self._landmarker = None
            return
        self._last_ts = -1

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def detect(self, frame_bgr: np.ndarray, timestamp_ms: float) -> np.ndarray | None:
        if self._landmarker is None:
            return None
        ts = int(timestamp_ms)
        if ts <= self._last_ts:
            ts = self._last_ts + 1
        self._last_ts = ts
        try:
            result = self._landmarker.detect_for_video(_mp_image(frame_bgr), ts)
        except Exception as exc:
            self._last_error = str(exc)
            return None
        if result is None or not result.face_landmarks:
            return None
        h, w = frame_bgr.shape[:2]
        lms = result.face_landmarks[0]
        return np.array([[lm.x * w, lm.y * h] for lm in lms], dtype=np.float32)

    def __enter__(self) -> "FaceLandmarkService":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
