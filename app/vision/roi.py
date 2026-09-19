"""Facial ROI polygons and mean RGB extraction."""

from __future__ import annotations

from typing import Iterable

import cv2
import numpy as np

from app.models import RGBSample

# MediaPipe Face Landmarker (478) indices. Eyes, brows, mouth, hairline excluded.
FOREHEAD_IDX = (10, 67, 69, 104, 108, 151, 337, 299, 297, 333, 9, 8)
LEFT_CHEEK_IDX = (50, 101, 118, 119, 100, 142, 203, 205, 36, 49)
RIGHT_CHEEK_IDX = (280, 330, 347, 348, 329, 371, 423, 425, 266, 279)

ROI_NAMES = ("forehead", "left_cheek", "right_cheek")
ROI_INDICES = {
    "forehead": FOREHEAD_IDX,
    "left_cheek": LEFT_CHEEK_IDX,
    "right_cheek": RIGHT_CHEEK_IDX,
}


def landmarks_to_points(landmarks: np.ndarray, indices: Iterable[int]) -> np.ndarray:
    pts = np.array([landmarks[i] for i in indices if 0 <= i < len(landmarks)], dtype=np.float32)
    return pts


def polygon_from_landmarks(landmarks: np.ndarray, indices: Iterable[int]) -> np.ndarray | None:
    pts = landmarks_to_points(landmarks, indices)
    if len(pts) < 3:
        return None
    hull = cv2.convexHull(pts.astype(np.int32))
    return hull.reshape(-1, 2)


def mean_rgb_from_polygon(frame_bgr: np.ndarray, polygon: np.ndarray | None) -> RGBSample | None:
    if polygon is None or len(polygon) < 3:
        return None
    height, width = frame_bgr.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask, polygon.astype(np.int32), 255)
    pixel_count = int(np.count_nonzero(mask))
    if pixel_count < 20:
        return None
    mean_bgr = cv2.mean(frame_bgr, mask=mask)[:3]
    return RGBSample(r=float(mean_bgr[2]), g=float(mean_bgr[1]), b=float(mean_bgr[0]))


def extract_named_rois(
    frame_bgr: np.ndarray, landmarks_xy: np.ndarray
) -> dict[str, tuple[np.ndarray | None, RGBSample | None]]:
    out: dict[str, tuple[np.ndarray | None, RGBSample | None]] = {}
    for name, indices in ROI_INDICES.items():
        poly = polygon_from_landmarks(landmarks_xy, indices)
        out[name] = (poly, mean_rgb_from_polygon(frame_bgr, poly))
    return out


def geometric_face_rois(
    frame_bgr: np.ndarray, bbox: tuple[int, int, int, int]
) -> dict[str, tuple[np.ndarray | None, RGBSample | None]]:
    """Fallback ROIs from a face/skin bounding box. Still measures real pixels."""
    x, y, w, h = bbox
    forehead = np.array(
        [
            [x + int(0.25 * w), y + int(0.08 * h)],
            [x + int(0.75 * w), y + int(0.08 * h)],
            [x + int(0.72 * w), y + int(0.28 * h)],
            [x + int(0.28 * w), y + int(0.28 * h)],
        ],
        dtype=np.int32,
    )
    left = np.array(
        [
            [x + int(0.08 * w), y + int(0.38 * h)],
            [x + int(0.38 * w), y + int(0.36 * h)],
            [x + int(0.36 * w), y + int(0.62 * h)],
            [x + int(0.10 * w), y + int(0.60 * h)],
        ],
        dtype=np.int32,
    )
    right = np.array(
        [
            [x + int(0.62 * w), y + int(0.36 * h)],
            [x + int(0.92 * w), y + int(0.38 * h)],
            [x + int(0.90 * w), y + int(0.60 * h)],
            [x + int(0.64 * w), y + int(0.62 * h)],
        ],
        dtype=np.int32,
    )
    out = {}
    for name, poly in (("forehead", forehead), ("left_cheek", left), ("right_cheek", right)):
        out[name] = (poly, mean_rgb_from_polygon(frame_bgr, poly))
    return out


def illumination_from_samples(samples: list[RGBSample | None]) -> float:
    vals = [0.299 * s.r + 0.587 * s.g + 0.114 * s.b for s in samples if s is not None]
    if not vals:
        return 0.0
    return float(np.mean(vals))
