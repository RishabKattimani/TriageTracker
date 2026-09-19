# Baseline / Fusion / Change Engine

## Baseline
Each patient maintains a personal baseline.

Prototype:
- collect high-confidence measurements during baseline period
- use robust statistics (median preferred)
- do not incorporate low-confidence values

Configurable baseline duration:
20-30 seconds for hackathon demo.

## Feature vector
FeatureVector {
    hr_delta_pct
    hr_slope
    hr_confidence
    rr_delta_pct
    rr_slope
    rr_confidence
    motion_score
    roi_agreement
    signal_quality
    persistence_seconds
}

Invalid features must be marked unavailable, not set to zero.

## Change scoring
Do NOT train an unsupported medical model on a few hackathon videos.

Implement a transparent ChangeScorer interface:

ChangeScorer.score(features) -> ChangeScoreResult

Initial implementation:
WeightedRuleChangeScorer

Possible future implementation:
MLChangeScorer

## Suggested prototype logic
The exact constants must live in config.py, not inline.

Example behavior:
- small deviations -> stable
- temporary spike -> no alert
- sustained high-confidence deviation -> change detected
- sustained stronger deviation -> reassess
- low-confidence apparent deviation -> abstain, never alert

No threshold is clinically validated.
UI and documentation must describe them as prototype thresholds.

## State machine
INITIALIZING
 -> BASELINING
 -> STABLE
 -> CHANGE_DETECTED
 -> REASSESS

SIGNAL_UNRELIABLE can temporarily override display state but must preserve the last trustworthy clinical-monitoring state internally.

## Explainability
Every alert returns reasons:
- HR deviation
- RR deviation
- persistence
- confidence
- ROI agreement
- motion quality

Never return a black-box label with no evidence.
