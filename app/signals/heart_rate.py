"""Spectral heart-rate estimation from rPPG. Never fabricates BPM."""

from __future__ import annotations

import numpy as np
from scipy.signal import welch

from app import config
from app.models import HeartRateResult
from app.signals.rppg import bandpass, chrom_transform, pos_transform


def hz_to_bpm(hz: float) -> float:
    return float(hz * 60.0)


def estimate_from_pulse(
    pulse: np.ndarray,
    fs: float,
    band: tuple[float, float] | None = None,
) -> tuple[float | None, float]:
    """Return (bpm, snr). bpm is None if the spectrum is unusable."""
    band = band or config.PULSE_BAND_HZ
    if len(pulse) < 16 or fs <= 0:
        return None, 0.0
    filtered = bandpass(pulse, fs, band)
    nperseg = min(len(filtered), max(32, int(fs * 4)))
    freqs, power = welch(filtered, fs=fs, nperseg=nperseg)
    mask = (freqs >= band[0]) & (freqs <= band[1])
    if not np.any(mask):
        return None, 0.0
    band_f = freqs[mask]
    band_p = power[mask]
    if float(np.max(band_p)) <= 1e-20:
        return None, 0.0
    peak_idx = int(np.argmax(band_p))
    peak_hz = float(band_f[peak_idx])
    peak_p = float(band_p[peak_idx])
    others = np.delete(band_p, peak_idx)
    noise = float(np.mean(others)) if len(others) else 1e-12
    snr = peak_p / (noise + 1e-12)
    return hz_to_bpm(peak_hz), float(snr)


def estimate_roi_hr(rgb: np.ndarray, fs: float) -> tuple[float | None, float]:
    if rgb.shape[0] < 16:
        return None, 0.0
    candidates = [
        estimate_from_pulse(pos_transform(rgb), fs),
        estimate_from_pulse(chrom_transform(rgb), fs),
        estimate_from_pulse(rgb[:, 1] - np.mean(rgb[:, 1]), fs),
    ]
    valid = [(bpm, snr) for bpm, snr in candidates if bpm is not None]
    if not valid:
        return None, 0.0
    return max(valid, key=lambda item: item[1])


def fuse_roi_estimates(
    candidates: list[tuple[str, float | None, float]],
    window_seconds: float,
) -> HeartRateResult:
    valid = [(name, bpm, snr) for name, bpm, snr in candidates if bpm is not None and np.isfinite(bpm)]
    if not valid:
        return HeartRateResult(
            bpm=None,
            confidence=0.0,
            snr=0.0,
            roi_agreement=0.0,
            method="pos-welch",
            window_seconds=window_seconds,
        )
    bpms = np.array([v[1] for v in valid], dtype=np.float64)
    snrs = np.array([max(v[2], 1e-6) for v in valid], dtype=np.float64)
    if len(bpms) == 1:
        agreement = 1.0
        bpm = float(bpms[0])
    else:
        spread = float(np.std(bpms))
        mean_bpm = float(np.mean(bpms))
        agreement = float(np.clip(1.0 - spread / max(mean_bpm, 1.0) * 4.0, 0.0, 1.0))
        if spread > 18.0:
            # Disagreement: do not average blindly.
            best = int(np.argmax(snrs))
            bpm = float(bpms[best])
            agreement = min(agreement, 0.35)
        else:
            bpm = float(np.average(bpms, weights=snrs))
    snr = float(np.mean(snrs))
    return HeartRateResult(
        bpm=bpm,
        confidence=0.0,  # filled by quality module
        snr=snr,
        roi_agreement=agreement,
        method="pos-welch-fused",
        window_seconds=window_seconds,
    )
