"""Personal baseline. Low-confidence samples are ignored."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app import config


@dataclass
class BaselineManager:
    duration_seconds: float = config.BASELINE_DURATION_SECONDS
    min_samples: int = config.BASELINE_MIN_SAMPLES
    _hr: list[float] = field(default_factory=list)
    _rr: list[float] = field(default_factory=list)
    _started_at: float | None = None
    ready: bool = False
    heart_rate: float | None = None
    respiratory_rate: float | None = None

    def reset(self) -> None:
        self._hr.clear()
        self._rr.clear()
        self._started_at = None
        self.ready = False
        self.heart_rate = None
        self.respiratory_rate = None

    def update(
        self,
        timestamp: float,
        *,
        hr: float | None,
        hr_conf: float,
        rr: float | None,
        rr_conf: float,
        abstaining: bool,
    ) -> None:
        if abstaining:
            return
        if self._started_at is None:
            self._started_at = timestamp
        if hr is not None and hr_conf >= config.HR_CONFIDENCE_THRESHOLD:
            self._hr.append(float(hr))
        if rr is not None and rr_conf >= config.RR_CONFIDENCE_THRESHOLD:
            self._rr.append(float(rr))
        elapsed = timestamp - self._started_at
        if elapsed >= self.duration_seconds and len(self._hr) >= self.min_samples:
            self.heart_rate = float(np.median(self._hr))
            self.respiratory_rate = float(np.median(self._rr)) if self._rr else None
            self.ready = True

    def elapsed(self, timestamp: float) -> float:
        if self._started_at is None:
            return 0.0
        return max(0.0, timestamp - self._started_at)
