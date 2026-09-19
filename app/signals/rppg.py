"""POS / CHROM rPPG transforms. Not a clinical algorithm."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, detrend, filtfilt


def _safe_mean_normalize(rgb: np.ndarray) -> np.ndarray:
    mu = np.mean(rgb, axis=0)
    mu = np.where(np.abs(mu) < 1e-6, 1.0, mu)
    return rgb / mu


def pos_transform(rgb: np.ndarray) -> np.ndarray:
    """Wang et al. POS. rgb is (N, 3) in R,G,B."""
    cn = _safe_mean_normalize(rgb)
    xs = 3.0 * cn[:, 0] - 2.0 * cn[:, 1]
    ys = 1.5 * cn[:, 0] + cn[:, 1] - 1.5 * cn[:, 2]
    std_x = float(np.std(xs))
    std_y = float(np.std(ys))
    alpha = std_x / (std_y + 1e-8)
    return xs + alpha * ys


def chrom_transform(rgb: np.ndarray) -> np.ndarray:
    cn = _safe_mean_normalize(rgb)
    xs = 3.0 * cn[:, 0] - 2.0 * cn[:, 1]
    ys = 1.5 * cn[:, 0] + cn[:, 1] - 1.5 * cn[:, 2]
    std_x = float(np.std(xs))
    std_y = float(np.std(ys))
    return xs - (std_x / (std_y + 1e-8)) * ys


def bandpass(signal: np.ndarray, fs: float, band: tuple[float, float], order: int = 2) -> np.ndarray:
    if len(signal) < 12 or fs <= 0:
        return signal
    low, high = band
    nyq = 0.5 * fs
    if high >= nyq:
        high = nyq * 0.95
    if low <= 0 or low >= high:
        return detrend(signal, type="linear")
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    detrended = detrend(np.asarray(signal, dtype=np.float64), type="linear")
    padlen = min(3 * max(len(a), len(b)), len(detrended) - 1)
    if padlen < 1:
        return detrended
    return filtfilt(b, a, detrended, padlen=padlen)
