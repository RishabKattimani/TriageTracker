"""Minimal face-crop color EVM. Visualization only. Never a numerical HR source."""

from __future__ import annotations

from collections import deque

import cv2
import numpy as np

from app import config


class SimpleFaceEVM:
    def __init__(self, amplification: float | None = None, max_width: int = 96) -> None:
        self.amplification = amplification if amplification is not None else config.EVM_AMPLIFICATION
        self.max_width = max_width
        self._history: deque[np.ndarray] = deque(maxlen=int(config.TARGET_SAMPLE_HZ * 3))

    def render(self, frame_bgr: np.ndarray, bbox: tuple[int, int, int, int] | None) -> np.ndarray:
        if bbox is None:
            small = cv2.resize(frame_bgr, (self.max_width, self.max_width))
            return small
        x, y, w, h = bbox
        x, y = max(0, x), max(0, y)
        crop = frame_bgr[y : y + h, x : x + w]
        if crop.size == 0:
            crop = frame_bgr
        if crop.shape[1] > self.max_width:
            scale = self.max_width / crop.shape[1]
            crop = cv2.resize(crop, (self.max_width, max(16, int(crop.shape[0] * scale))))
        self._history.append(crop.astype(np.float32))
        if len(self._history) < 8:
            return crop
        stack = np.stack(list(self._history), axis=0)
        mean = np.mean(stack, axis=0)
        latest = stack[-1]
        residual = latest - mean
        amplified = np.clip(latest + residual * (self.amplification / 10.0), 0, 255)
        return amplified.astype(np.uint8)
