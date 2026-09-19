"""Respiratory-rate attempt. Independent of HR. Honest unavailable if weak."""

from __future__ import annotations

import numpy as np

from app import config
from app.models import RespirationResult
from app.signals.heart_rate import estimate_from_pulse
from app.signals.rppg import bandpass


def estimate_rr(
    motion_signal: np.ndarray,
    fs: float,
    *,
    face_present: bool,
    facial_motion: float,
) -> RespirationResult:
    unavailable = RespirationResult(
        breaths_per_minute=None,
        confidence=0.0,
        snr=0.0,
        method="unavailable",
    )
    if not face_present or len(motion_signal) < 32 or fs <= 0:
        return unavailable
    if facial_motion >= config.MOTION_ABSTAIN_THRESHOLD:
        return unavailable
    filtered = bandpass(motion_signal, fs, config.RESP_BAND_HZ)
    bpm, snr = estimate_from_pulse(filtered, fs, config.RESP_BAND_HZ)
    if bpm is None:
        return unavailable
    # Respiration estimate is in the same Hz*60 space as HR helper.
    confidence = float(np.clip(snr / 6.0, 0.0, 1.0))
    if confidence < config.RR_CONFIDENCE_THRESHOLD:
        return RespirationResult(
            breaths_per_minute=None,
            confidence=confidence,
            snr=float(snr),
            method="bbox-motion-weak",
        )
    return RespirationResult(
        breaths_per_minute=float(bpm),
        confidence=confidence,
        snr=float(snr),
        method="bbox-motion",
    )
