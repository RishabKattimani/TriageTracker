"""Signal quality, confidence, and abstention. Low confidence never feeds alerts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app import config
from app.models import HeartRateResult


@dataclass
class QualityDecision:
    confidence: float
    signal_quality: float
    abstaining: bool
    reason: str | None
    recovered: bool


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def compute_confidence(
    *,
    face_present: bool,
    snr: float,
    roi_agreement: float,
    motion: float,
    illumination: float,
    valid_ratio: float,
) -> float:
    if not face_present:
        return 0.0
    snr_term = _clip01(snr / 8.0)
    motion_term = _clip01(1.0 - motion / max(config.MOTION_ABSTAIN_THRESHOLD, 1e-6))
    illum_term = _clip01(illumination / 80.0) if illumination >= config.ILLUMINATION_MIN else 0.15
    agree = _clip01(roi_agreement)
    valid = _clip01(valid_ratio)
    raw = 0.30 * snr_term + 0.25 * agree + 0.25 * motion_term + 0.10 * illum_term + 0.10 * valid
    return _clip01(raw)


def decide_quality(
    hr: HeartRateResult,
    *,
    face_present: bool,
    motion: float,
    illumination: float,
    valid_ratio: float,
    consecutive_clean_seconds: float,
    previously_abstaining: bool,
) -> QualityDecision:
    confidence = compute_confidence(
        face_present=face_present,
        snr=hr.snr,
        roi_agreement=hr.roi_agreement,
        motion=motion,
        illumination=illumination,
        valid_ratio=valid_ratio,
    )
    quality = _clip01(0.6 * confidence + 0.4 * _clip01(hr.roi_agreement))
    reason = None
    abstain = False
    if not face_present:
        abstain, reason = True, "no_face"
    elif illumination < config.ILLUMINATION_MIN:
        abstain, reason = True, "poor_illumination"
    elif motion >= config.MOTION_ABSTAIN_THRESHOLD:
        abstain, reason = True, "motion_artifact"
    elif valid_ratio < config.VALID_FRAME_RATIO_MIN:
        abstain, reason = True, "insufficient_valid_frames"
    elif hr.bpm is None:
        abstain, reason = True, "no_spectral_peak"
    elif hr.roi_agreement < config.ROI_AGREEMENT_THRESHOLD and hr.roi_agreement > 0:
        abstain, reason = True, "roi_disagreement"
    elif confidence < config.HR_CONFIDENCE_THRESHOLD:
        abstain, reason = True, "low_confidence"

    recovered = previously_abstaining and not abstain
    if recovered and consecutive_clean_seconds < config.RECOVERY_CLEAN_WINDOW_SECONDS:
        abstain, reason = True, "recovery_warmup"
        recovered = False

    if abstain:
        hr.bpm = None
    hr.confidence = 0.0 if abstain else confidence
    return QualityDecision(
        confidence=hr.confidence,
        signal_quality=0.0 if abstain else quality,
        abstaining=abstain,
        reason=reason,
        recovered=recovered,
    )
