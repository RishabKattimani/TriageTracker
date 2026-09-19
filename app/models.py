"""Shared data contracts. Frontend must render these; it must not invent state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class PatientStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    BASELINING = "BASELINING"
    STABLE = "STABLE"
    CHANGE_DETECTED = "CHANGE_DETECTED"
    REASSESS = "REASSESS"
    SIGNAL_UNRELIABLE = "SIGNAL_UNRELIABLE"

    def is_alert_state(self) -> bool:
        return self in (PatientStatus.CHANGE_DETECTED, PatientStatus.REASSESS)


@dataclass(frozen=True)
class FramePacket:
    frame_bgr: Any
    timestamp_ms: float
    source_id: str
    frame_index: int


@dataclass
class RGBSample:
    r: float
    g: float
    b: float

    def as_array(self) -> Any:
        import numpy as np

        return np.array([self.r, self.g, self.b], dtype=np.float64)


@dataclass
class FrameObservation:
    face_present: bool
    face_landmarks: Any
    forehead_rgb: RGBSample | None
    left_cheek_rgb: RGBSample | None
    right_cheek_rgb: RGBSample | None
    facial_motion: float
    illumination: float
    torso_motion_signal: float | None
    debug_overlay_frame: Any
    timestamp_ms: float
    source_id: str
    frame_index: int
    face_bbox: tuple[int, int, int, int] | None = None


@dataclass
class FeatureVector:
    hr_delta_pct: float | None
    hr_slope: float | None
    hr_confidence: float
    rr_delta_pct: float | None
    rr_slope: float | None
    rr_confidence: float
    motion_score: float
    roi_agreement: float
    signal_quality: float
    persistence_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeScoreResult:
    score: float | None
    reasons: list[str]
    contributing: bool


@dataclass
class HeartRateResult:
    bpm: float | None
    confidence: float
    snr: float
    roi_agreement: float
    method: str
    window_seconds: float


@dataclass
class RespirationResult:
    breaths_per_minute: float | None
    confidence: float
    snr: float
    method: str


@dataclass
class PatientMeasurement:
    patient_id: str
    timestamp: float
    heart_rate: float | None = None
    heart_rate_confidence: float = 0.0
    heart_rate_snr: float = 0.0
    respiratory_rate: float | None = None
    respiratory_confidence: float = 0.0
    motion_score: float = 0.0
    roi_agreement: float = 0.0
    signal_quality: float = 0.0
    baseline_heart_rate: float | None = None
    baseline_respiratory_rate: float | None = None
    heart_rate_delta_pct: float | None = None
    respiratory_rate_delta_pct: float | None = None
    persistence_seconds: float = 0.0
    change_score: float | None = None
    status: PatientStatus = PatientStatus.INITIALIZING
    abstaining: bool = False
    abstention_reason: str | None = None
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatientMeasurement":
        payload = dict(data)
        status = payload.get("status", PatientStatus.INITIALIZING)
        if isinstance(status, str):
            payload["status"] = PatientStatus(status)
        return cls(**payload)
