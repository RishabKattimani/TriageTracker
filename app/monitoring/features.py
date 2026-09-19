"""Feature builder. Invalid features stay None, never 0."""

from __future__ import annotations

from collections import deque

from app.models import FeatureVector


class FeatureBuilder:
    def __init__(self) -> None:
        self._hr_hist: deque[tuple[float, float]] = deque(maxlen=40)

    def reset(self) -> None:
        self._hr_hist.clear()

    def build(
        self,
        *,
        timestamp: float,
        hr: float | None,
        hr_conf: float,
        rr: float | None,
        rr_conf: float,
        baseline_hr: float | None,
        baseline_rr: float | None,
        motion: float,
        roi_agreement: float,
        signal_quality: float,
        persistence_seconds: float,
        abstaining: bool,
    ) -> FeatureVector:
        hr_delta = None
        hr_slope = None
        rr_delta = None
        rr_slope = None
        if not abstaining and hr is not None and baseline_hr not in (None, 0):
            hr_delta = (hr - baseline_hr) / baseline_hr
            self._hr_hist.append((timestamp, hr))
            hr_slope = _slope(self._hr_hist)
        if not abstaining and rr is not None and baseline_rr not in (None, 0):
            rr_delta = (rr - baseline_rr) / baseline_rr
        return FeatureVector(
            hr_delta_pct=hr_delta,
            hr_slope=hr_slope,
            hr_confidence=hr_conf,
            rr_delta_pct=rr_delta,
            rr_slope=rr_slope,
            rr_confidence=rr_conf,
            motion_score=motion,
            roi_agreement=roi_agreement,
            signal_quality=signal_quality,
            persistence_seconds=persistence_seconds,
        )


def _slope(history: deque[tuple[float, float]]) -> float | None:
    if len(history) < 4:
        return None
    t0, v0 = history[0]
    t1, v1 = history[-1]
    dt = t1 - t0
    if dt < 1.0:
        return None
    return (v1 - v0) / dt
