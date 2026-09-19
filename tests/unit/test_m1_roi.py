import numpy as np
import pytest

from app.models import RGBSample
from app.vision.roi import extract_named_rois, mean_rgb_from_polygon, polygon_from_landmarks


pytestmark = pytest.mark.milestone1


def _grid_landmarks(width: int = 200, height: int = 200) -> np.ndarray:
    pts = np.zeros((478, 2), dtype=np.float32)
    rng = np.linspace(40, 160, 478)
    pts[:, 0] = rng
    pts[:, 1] = 40 + (rng % 80)
    # Forehead cluster
    for i, idx in enumerate((10, 67, 69, 104, 108, 151, 337, 299, 297, 333, 9, 8)):
        pts[idx] = (70 + i * 4, 50 + (i % 3) * 6)
    for i, idx in enumerate((50, 101, 118, 119, 100, 142, 203, 205, 36, 49)):
        pts[idx] = (55 + i * 3, 110 + (i % 4) * 5)
    for i, idx in enumerate((280, 330, 347, 348, 329, 371, 423, 425, 266, 279)):
        pts[idx] = (120 + i * 3, 110 + (i % 4) * 5)
    return pts


def test_polygon_and_mean_rgb_from_landmarks() -> None:
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    frame[40:80, 60:140] = (10, 80, 200)
    pts = _grid_landmarks()
    poly = polygon_from_landmarks(pts, (10, 67, 69, 104, 108, 151))
    assert poly is not None and len(poly) >= 3
    sample = mean_rgb_from_polygon(frame, poly)
    assert isinstance(sample, RGBSample)
    assert sample.r > 50
    rois = extract_named_rois(frame, pts)
    assert set(rois) == {"forehead", "left_cheek", "right_cheek"}


def test_empty_polygon_returns_no_sample() -> None:
    frame = np.zeros((40, 40, 3), dtype=np.uint8)
    assert mean_rgb_from_polygon(frame, None) is None
    assert mean_rgb_from_polygon(frame, np.zeros((0, 2))) is None
