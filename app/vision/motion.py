"""Facial motion from landmark / bbox displacement."""

from __future__ import annotations

import numpy as np


def landmark_motion(prev: np.ndarray | None, curr: np.ndarray | None, face_scale: float) -> float:
    if prev is None or curr is None or prev.shape != curr.shape:
        return 0.0
    if face_scale <= 1e-6:
        return 1.0
    delta = np.linalg.norm(curr.astype(np.float64) - prev.astype(np.float64), axis=1)
    return float(np.clip(np.median(delta) / face_scale, 0.0, 1.0))


def bbox_motion(
    prev_bbox: tuple[int, int, int, int] | None,
    curr_bbox: tuple[int, int, int, int] | None,
) -> float:
    if prev_bbox is None or curr_bbox is None:
        return 0.0
    px, py, pw, ph = prev_bbox
    cx, cy, cw, ch = curr_bbox
    scale = max(float(max(pw, ph, cw, ch)), 1.0)
    shift = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
    size = abs(cw - pw) + abs(ch - ph)
    return float(np.clip((shift + 0.5 * size) / scale, 0.0, 1.0))


def face_scale_from_landmarks(landmarks: np.ndarray) -> float:
    xs = landmarks[:, 0]
    ys = landmarks[:, 1]
    return float(max(xs.max() - xs.min(), ys.max() - ys.min(), 1.0))
