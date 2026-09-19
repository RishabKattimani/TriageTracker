"""Application configuration.

Every physiological threshold in this file is a PROTOTYPE engineering value
for the hackathon demo. None are clinically validated.
"""

from __future__ import annotations

from pathlib import Path

APP_NAME = "TriageTracker"
APP_VERSION = "0.4.0-p0"
HOST = "127.0.0.1"
PREFERRED_PORTS: tuple[int, ...] = (8765, 8766, 8767)
DEFAULT_PORT = 8765

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
FIXTURES_DIR = ROOT_DIR / "fixtures"
TEMPLATES_DIR = Path(__file__).resolve().parent / "web" / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "web" / "static"

FACE_LANDMARKER_MODEL = MODELS_DIR / "face_landmarker.task"
POSE_LANDMARKER_MODEL = MODELS_DIR / "pose_landmarker_lite.task"
GUIDED_DEMO_FIXTURE = FIXTURES_DIR / "controlled_change.mp4"
STABLE_FIXTURE = FIXTURES_DIR / "stable_seated.mp4"

# Prototype pulse band: 0.7-3.0 Hz (~42-180 BPM). Not a clinical threshold.
PULSE_BAND_HZ: tuple[float, float] = (0.7, 3.0)
# Prototype respiration band: 0.1-0.7 Hz (~6-42 breaths/min). Not clinical.
RESP_BAND_HZ: tuple[float, float] = (0.1, 0.7)

HR_WINDOW_SECONDS = 12.0
RR_WINDOW_SECONDS = 20.0
MIN_VALID_WINDOW_SECONDS = 8.0
RECOVERY_CLEAN_WINDOW_SECONDS = 4.0
BUFFER_MAX_SECONDS = 60.0
TARGET_SAMPLE_HZ = 30.0

# Prototype confidence / abstention thresholds. Not clinically validated.
HR_CONFIDENCE_THRESHOLD = 0.55
RR_CONFIDENCE_THRESHOLD = 0.50
ROI_AGREEMENT_THRESHOLD = 0.45
MOTION_ABSTAIN_THRESHOLD = 0.45
ILLUMINATION_MIN = 25.0
VALID_FRAME_RATIO_MIN = 0.70

# Prototype baseline window for the demo. Not clinically validated.
BASELINE_DURATION_SECONDS = 25.0
BASELINE_MIN_SAMPLES = 8

# Prototype change-scorer weights. Not a trained medical model.
WEIGHT_HR_DELTA = 0.35
WEIGHT_HR_SLOPE = 0.10
WEIGHT_RR_DELTA = 0.25
WEIGHT_RR_SLOPE = 0.08
WEIGHT_PERSISTENCE = 0.22

# Prototype persistence / alert thresholds. Not clinically validated.
CHANGE_DETECTED_SCORE = 0.45
REASSESS_SCORE = 0.70
CHANGE_DETECTED_PERSISTENCE_SECONDS = 8.0
REASSESS_PERSISTENCE_SECONDS = 16.0
SPIKE_RESET_SECONDS = 3.0

# File-repeatability tolerances, defined before implementation output is seen.
# Deterministic file input must match the state-transition sequence exactly.
REPEATABILITY_HR_TOLERANCE_BPM = 8.0
REPEATABILITY_RR_TOLERANCE_BRPM = 4.0
REPEATABILITY_CONFIDENCE_TOLERANCE = 0.15

PATIENT_IDS: tuple[str, ...] = ("P01", "P02", "P03", "P04", "P05", "P06")
LIVE_PATIENT_ID = "P01"
CONTROLLED_CHANGE_PATIENT_ID = "P04"

WEBCAM_INDEX = 0

# EVM is visualization-only. These are prototype display parameters.
EVM_AMPLIFICATION = 30.0
EVM_DOWNSAMPLE = 4
EVM_BAND_HZ: tuple[float, float] = (0.7, 3.0)

GUIDED_DEMO_TARGET_SECONDS = 75

REQUIRED_WORDING_CHANGE = "Physiological change detected."
REQUIRED_WORDING_REASSESS = "Reassessment recommended."
REQUIRED_WORDING_UNRELIABLE = "Signal unreliable — no inference made."
REQUIRED_WORDING_REACQUIRED = "SIGNAL REACQUIRED"

PROHIBITED_WORDING: tuple[str, ...] = (
    "Patient is deteriorating.",
    "Patient has sepsis.",
    "Patient is having a heart attack.",
)

REQUIRED_ASSET_KEYS: tuple[str, ...] = (
    "face_landmarker_model",
    "pose_landmarker_model",
    "guided_demo_fixture",
    "stable_fixture",
)
