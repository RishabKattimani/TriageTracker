# Data Schema

## PatientMeasurement

{
  "patient_id": "P04",
  "timestamp": 0.0,

  "heart_rate": 98.0,
  "heart_rate_confidence": 0.94,
  "heart_rate_snr": 8.1,

  "respiratory_rate": 20.0,
  "respiratory_confidence": 0.82,

  "motion_score": 0.08,
  "roi_agreement": 0.91,
  "signal_quality": 0.92,

  "baseline_heart_rate": 74.0,
  "baseline_respiratory_rate": 15.0,

  "heart_rate_delta_pct": 0.324,
  "respiratory_rate_delta_pct": 0.333,

  "persistence_seconds": 24.0,
  "change_score": 0.87,

  "status": "REASSESS",

  "abstaining": false,
  "abstention_reason": null,

  "reasons": [
    "Heart rate +32% from baseline",
    "Respiratory rate +33% from baseline",
    "Change persisted for 24 seconds",
    "Signal confidence high"
  ]
}

## Status enum
INITIALIZING
BASELINING
STABLE
CHANGE_DETECTED
REASSESS
SIGNAL_UNRELIABLE

## Frontend rule
Frontend renders backend state.
Frontend MUST NOT independently calculate reassessment status.
