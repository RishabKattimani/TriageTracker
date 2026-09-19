"""Timestamped rolling buffers. Physiology consumes FramePacket only."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class TimestampedBuffer:
    max_seconds: float
    timestamps: list[float] = field(default_factory=list)
    values: list[np.ndarray] = field(default_factory=list)

    def append(self, timestamp_s: float, value: np.ndarray) -> None:
        self.timestamps.append(float(timestamp_s))
        self.values.append(np.asarray(value, dtype=np.float64))
        self._trim()

    def _trim(self) -> None:
        if not self.timestamps:
            return
        cutoff = self.timestamps[-1] - self.max_seconds
        while len(self.timestamps) > 2 and self.timestamps[0] < cutoff:
            self.timestamps.pop(0)
            self.values.pop(0)

    def clear(self) -> None:
        self.timestamps.clear()
        self.values.clear()

    def __len__(self) -> int:
        return len(self.timestamps)

    def duration(self) -> float:
        if len(self.timestamps) < 2:
            return 0.0
        return float(self.timestamps[-1] - self.timestamps[0])

    def as_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        if not self.timestamps:
            return np.array([]), np.zeros((0, 3))
        return np.asarray(self.timestamps, dtype=np.float64), np.vstack(self.values)

    def valid_ratio(self, expected_hz: float, window_seconds: float) -> float:
        if expected_hz <= 0 or window_seconds <= 0:
            return 0.0
        expected = window_seconds * expected_hz
        if expected <= 0:
            return 0.0
        return float(np.clip(len(self.timestamps) / expected, 0.0, 1.0))


def resample_regular(
    timestamps: np.ndarray, values: np.ndarray, target_hz: float
) -> tuple[np.ndarray, np.ndarray]:
    if len(timestamps) < 4:
        return timestamps, values
    duration = timestamps[-1] - timestamps[0]
    if duration <= 0:
        return timestamps, values
    n = max(8, int(duration * target_hz) + 1)
    grid = np.linspace(timestamps[0], timestamps[-1], n)
    cols = []
    for col in range(values.shape[1]):
        cols.append(np.interp(grid, timestamps, values[:, col]))
    return grid, np.column_stack(cols)
