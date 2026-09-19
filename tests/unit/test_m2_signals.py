import numpy as np
import pytest

from app.signals.heart_rate import estimate_from_pulse, estimate_roi_hr, hz_to_bpm
from app.signals.rppg import bandpass, pos_transform
from app.signals.buffers import TimestampedBuffer, resample_regular


pytestmark = pytest.mark.milestone2


def test_hz_to_bpm() -> None:
    assert hz_to_bpm(1.2) == 72.0
    assert hz_to_bpm(1.833) == pytest.approx(110.0, abs=0.2)


def test_pos_recovers_known_pulse() -> None:
    fs = 30.0
    t = np.arange(0, 12.0, 1.0 / fs)
    pulse = np.sin(2 * np.pi * 1.2 * t)
    rgb = np.column_stack(
        [
            180 + 3 * pulse,
            140 + 22 * pulse,
            110 + 1.5 * pulse,
        ]
    )
    bpm, snr = estimate_roi_hr(rgb, fs)
    assert bpm is not None
    assert abs(bpm - 72.0) <= 8.0
    assert snr > 1.0
    transformed = pos_transform(rgb)
    filtered = bandpass(transformed, fs, (0.7, 3.0))
    assert filtered.std() > 0


def test_empty_signal_does_not_fabricate_bpm() -> None:
    bpm, snr = estimate_from_pulse(np.zeros(4), 30.0)
    assert bpm is None
    assert snr == 0.0


def test_buffer_trim_and_resample() -> None:
    buf = TimestampedBuffer(max_seconds=2.0)
    for i in range(40):
        buf.append(i * 0.1, np.array([1.0, 2.0, 3.0]))
    assert buf.duration() <= 2.05
    ts, vals = buf.as_arrays()
    grid, resampled = resample_regular(ts, vals, 20.0)
    assert len(grid) >= 8
    assert resampled.shape[1] == 3
