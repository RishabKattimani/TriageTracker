"""Per-patient monitor: buffers -> HR/RR -> quality -> baseline -> score -> state."""

from __future__ import annotations

from app import config
from app.models import (
    FrameObservation,
    HeartRateResult,
    PatientMeasurement,
    PatientStatus,
    RespirationResult,
)
from app.monitoring.baseline import BaselineManager
from app.monitoring.features import FeatureBuilder
from app.monitoring.scorer import WeightedRuleChangeScorer
from app.monitoring.state_machine import PatientStateMachine
from app.signals.buffers import TimestampedBuffer, resample_regular
from app.signals.heart_rate import estimate_roi_hr, fuse_roi_estimates
from app.signals.quality import decide_quality
from app.signals.respiration import estimate_rr


class PatientMonitor:
    def __init__(self, patient_id: str) -> None:
        self.patient_id = patient_id
        self.baseline = BaselineManager()
        self.features = FeatureBuilder()
        self.scorer = WeightedRuleChangeScorer()
        self.machine = PatientStateMachine()
        self.forehead = TimestampedBuffer(config.BUFFER_MAX_SECONDS)
        self.left = TimestampedBuffer(config.BUFFER_MAX_SECONDS)
        self.right = TimestampedBuffer(config.BUFFER_MAX_SECONDS)
        self.bbox_y = TimestampedBuffer(config.BUFFER_MAX_SECONDS)
        self._last_ts: float | None = None
        self._clean_seconds = 0.0
        self._prev_abstaining = False
        self._history: list[PatientMeasurement] = []
        self.latest = PatientMeasurement(patient_id=patient_id, timestamp=0.0)

    def reset(self) -> None:
        self.baseline.reset()
        self.features.reset()
        self.machine.reset()
        self.forehead.clear()
        self.left.clear()
        self.right.clear()
        self.bbox_y.clear()
        self._last_ts = None
        self._clean_seconds = 0.0
        self._prev_abstaining = False
        self._history.clear()
        self.latest = PatientMeasurement(patient_id=self.patient_id, timestamp=0.0)

    def ingest(self, obs: FrameObservation) -> PatientMeasurement:
        ts = obs.timestamp_ms / 1000.0
        dt = 0.0 if self._last_ts is None else max(0.0, ts - self._last_ts)
        self._last_ts = ts

        if obs.face_present:
            if obs.forehead_rgb:
                self.forehead.append(ts, obs.forehead_rgb.as_array())
            if obs.left_cheek_rgb:
                self.left.append(ts, obs.left_cheek_rgb.as_array())
            if obs.right_cheek_rgb:
                self.right.append(ts, obs.right_cheek_rgb.as_array())
            if obs.face_bbox is not None:
                self.bbox_y.append(ts, [float(obs.face_bbox[1])])

        hr = self._estimate_hr()
        if hr.bpm is not None and self.latest.heart_rate is not None:
            hr.bpm = 0.65 * hr.bpm + 0.35 * self.latest.heart_rate
        rr = self._estimate_rr(obs)
        valid_ratio = max(
            self.forehead.valid_ratio(config.TARGET_SAMPLE_HZ, config.HR_WINDOW_SECONDS),
            self.left.valid_ratio(config.TARGET_SAMPLE_HZ, config.HR_WINDOW_SECONDS),
            self.right.valid_ratio(config.TARGET_SAMPLE_HZ, config.HR_WINDOW_SECONDS),
        )
        if obs.facial_motion < config.MOTION_ABSTAIN_THRESHOLD and obs.face_present:
            self._clean_seconds += dt
        else:
            self._clean_seconds = 0.0

        decision = decide_quality(
            hr,
            face_present=obs.face_present,
            motion=obs.facial_motion,
            illumination=obs.illumination,
            valid_ratio=valid_ratio,
            consecutive_clean_seconds=self._clean_seconds,
            previously_abstaining=self._prev_abstaining,
        )
        if decision.abstaining:
            rr = RespirationResult(None, 0.0, 0.0, rr.method)

        self.baseline.update(
            ts,
            hr=hr.bpm,
            hr_conf=hr.confidence,
            rr=rr.breaths_per_minute,
            rr_conf=rr.confidence,
            abstaining=decision.abstaining,
        )
        persistence = self.machine.persistence
        vector = self.features.build(
            timestamp=ts,
            hr=hr.bpm,
            hr_conf=hr.confidence,
            rr=rr.breaths_per_minute,
            rr_conf=rr.confidence,
            baseline_hr=self.baseline.heart_rate,
            baseline_rr=self.baseline.respiratory_rate,
            motion=obs.facial_motion,
            roi_agreement=hr.roi_agreement,
            signal_quality=decision.signal_quality,
            persistence_seconds=persistence,
            abstaining=decision.abstaining,
        )
        scored = self.scorer.score(vector)
        status = self.machine.update(
            timestamp=ts,
            dt=dt,
            baseline_ready=self.baseline.ready,
            change_score=scored.score,
            abstaining=decision.abstaining,
            recovered=decision.recovered,
        )
        vector.persistence_seconds = self.machine.persistence

        hr_delta = vector.hr_delta_pct
        rr_delta = vector.rr_delta_pct
        reasons = list(scored.reasons)
        if decision.abstaining:
            reasons = [config.REQUIRED_WORDING_UNRELIABLE]
            if decision.reason:
                reasons.append(decision.reason)
        elif status == PatientStatus.REASSESS:
            reasons.insert(0, config.REQUIRED_WORDING_REASSESS)
        elif status == PatientStatus.CHANGE_DETECTED:
            reasons.insert(0, config.REQUIRED_WORDING_CHANGE)
        if decision.recovered:
            reasons.insert(0, config.REQUIRED_WORDING_REACQUIRED)

        measurement = PatientMeasurement(
            patient_id=self.patient_id,
            timestamp=ts,
            heart_rate=hr.bpm,
            heart_rate_confidence=hr.confidence,
            heart_rate_snr=hr.snr,
            respiratory_rate=rr.breaths_per_minute,
            respiratory_confidence=rr.confidence,
            motion_score=obs.facial_motion,
            roi_agreement=hr.roi_agreement,
            signal_quality=decision.signal_quality,
            baseline_heart_rate=self.baseline.heart_rate,
            baseline_respiratory_rate=self.baseline.respiratory_rate,
            heart_rate_delta_pct=hr_delta,
            respiratory_rate_delta_pct=rr_delta,
            persistence_seconds=self.machine.persistence,
            change_score=scored.score,
            status=status,
            abstaining=decision.abstaining,
            abstention_reason=decision.reason,
            reasons=reasons,
        )
        self.latest = measurement
        self._history.append(measurement)
        if len(self._history) > 400:
            self._history = self._history[-400:]
        self._prev_abstaining = decision.abstaining
        return measurement

    def history(self) -> list[PatientMeasurement]:
        return list(self._history)

    def _estimate_hr(self) -> HeartRateResult:
        window = config.HR_WINDOW_SECONDS
        if self.forehead.duration() < config.MIN_VALID_WINDOW_SECONDS:
            return HeartRateResult(None, 0.0, 0.0, 0.0, "pos-welch", window)
        candidates = []
        for name, buf in (("forehead", self.forehead), ("left", self.left), ("right", self.right)):
            ts, rgb = buf.as_arrays()
            if len(ts) < 16:
                candidates.append((name, None, 0.0))
                continue
            grid, resampled = resample_regular(ts, rgb, config.TARGET_SAMPLE_HZ)
            if len(grid) < 2:
                candidates.append((name, None, 0.0))
                continue
            fs = (len(grid) - 1) / max(grid[-1] - grid[0], 1e-6)
            bpm, snr = estimate_roi_hr(resampled, fs)
            candidates.append((name, bpm, snr))
        return fuse_roi_estimates(candidates, window)

    def _estimate_rr(self, obs: FrameObservation) -> RespirationResult:
        ts, vals = self.bbox_y.as_arrays()
        if len(ts) < 32:
            return RespirationResult(None, 0.0, 0.0, "unavailable")
        grid, resampled = resample_regular(ts, vals, config.TARGET_SAMPLE_HZ)
        fs = (len(grid) - 1) / max(grid[-1] - grid[0], 1e-6)
        return estimate_rr(
            resampled[:, 0],
            fs,
            face_present=obs.face_present,
            facial_motion=obs.facial_motion,
        )
