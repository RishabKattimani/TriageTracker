"""FrameProcessor: FramePacket -> FrameObservation. Shared by webcam and MP4."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from app.models import FrameObservation, FramePacket, RGBSample
from app.vision.face_landmarks import FaceLandmarkService
from app.vision.motion import bbox_motion, face_scale_from_landmarks, landmark_motion
from app.vision.roi import extract_named_rois, geometric_face_rois, illumination_from_samples


class FrameProcessor:
    def __init__(
        self,
        *,
        live: bool = False,
        fixture_meta: dict | None = None,
        landmarker: FaceLandmarkService | None = None,
    ) -> None:
        self.live = live
        self.fixture_meta = fixture_meta or {}
        self._landmarker = landmarker or FaceLandmarkService(live=live)
        self._owns_landmarker = landmarker is None
        self._prev_landmarks: np.ndarray | None = None
        self._prev_bbox: tuple[int, int, int, int] | None = None

    def open(self) -> None:
        if self._owns_landmarker:
            self._landmarker.open()

    def close(self) -> None:
        if self._owns_landmarker:
            self._landmarker.close()

    def process(self, packet: FramePacket) -> FrameObservation:
        frame = packet.frame_bgr
        landmarks = self._landmarker.detect(frame, packet.timestamp_ms)
        rois: dict[str, tuple[np.ndarray | None, RGBSample | None]] = {}
        bbox = None
        face_present = landmarks is not None and len(landmarks) >= 100

        if face_present and landmarks is not None:
            xs = landmarks[:, 0]
            ys = landmarks[:, 1]
            x0, y0 = int(xs.min()), int(ys.min())
            x1, y1 = int(xs.max()), int(ys.max())
            bbox = (x0, y0, max(1, x1 - x0), max(1, y1 - y0))
            rois = extract_named_rois(frame, landmarks)
            scale = face_scale_from_landmarks(landmarks)
            motion = landmark_motion(self._prev_landmarks, landmarks, scale)
            self._prev_landmarks = landmarks.copy()
        else:
            landmarks = None
            motion = 0.0
            patch = self._skin_patch_bbox(frame)
            if patch is not None:
                face_present = True
                bbox = patch
                rois = geometric_face_rois(frame, patch)
                motion = bbox_motion(self._prev_bbox, bbox)
                self._prev_bbox = bbox
            else:
                self._prev_landmarks = None
                self._prev_bbox = None

        forehead = rois.get("forehead", (None, None))[1]
        left = rois.get("left_cheek", (None, None))[1]
        right = rois.get("right_cheek", (None, None))[1]
        overlay = draw_overlay(frame, rois, face_present, motion)
        illum = illumination_from_samples([forehead, left, right])
        return FrameObservation(
            face_present=face_present,
            face_landmarks=landmarks,
            forehead_rgb=forehead,
            left_cheek_rgb=left,
            right_cheek_rgb=right,
            facial_motion=float(motion),
            illumination=illum,
            torso_motion_signal=None,
            debug_overlay_frame=overlay,
            timestamp_ms=packet.timestamp_ms,
            source_id=packet.source_id,
            frame_index=packet.frame_index,
            face_bbox=bbox,
        )

    def _skin_patch_bbox(self, frame: np.ndarray) -> tuple[int, int, int, int] | None:
        """Synthetic-fixture fallback only. Never invents RGB; extracts real pixels."""
        meta = self.fixture_meta
        if meta.get("kind") != "synthetic_pulse":
            return None
        patch = meta.get("skin_patch") or {}
        h, w = frame.shape[:2]
        x = int(float(patch.get("x", 0.25)) * w)
        y = int(float(patch.get("y", 0.15)) * h)
        pw = int(float(patch.get("w", 0.5)) * w)
        ph = int(float(patch.get("h", 0.6)) * h)
        if pw < 16 or ph < 16:
            return None
        return (x, y, pw, ph)

    def __enter__(self) -> "FrameProcessor":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def load_fixture_meta(video_path: Path) -> dict:
    sidecar = Path(video_path).with_suffix(".json")
    if not sidecar.is_file():
        return {}
    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def draw_overlay(
    frame_bgr: np.ndarray,
    rois: dict[str, tuple[np.ndarray | None, RGBSample | None]],
    face_present: bool,
    motion: float,
) -> np.ndarray:
    overlay = frame_bgr.copy()
    colors = {
        "forehead": (60, 180, 75),
        "left_cheek": (50, 140, 220),
        "right_cheek": (220, 140, 50),
    }
    for name, (poly, _sample) in rois.items():
        if poly is None:
            continue
        cv2.polylines(overlay, [poly.astype(np.int32)], True, colors.get(name, (255, 255, 255)), 2)
    label = "FACE" if face_present else "NO FACE"
    cv2.putText(
        overlay,
        f"{label}  motion={motion:.2f}",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (40, 40, 40) if face_present else (20, 20, 200),
        2,
        cv2.LINE_AA,
    )
    return overlay
