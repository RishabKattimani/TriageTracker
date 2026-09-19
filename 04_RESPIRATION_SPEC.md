# Respiratory Rate Specification

Respiratory rate is required in V1, but its failure must NOT break heart-rate measurement or the full application.

## Candidate methods in priority order

### Method A: upper-body optical motion
Use MediaPipe pose landmarks if reliable.
Track a chest/shoulder region.
Derive vertical/scale motion over time.
Bandpass in a plausible respiration range.
Estimate dominant frequency.

### Method B: facial/head micro-motion
If pose tracking is unavailable, derive a respiration-related motion signal from stabilized face landmarks / bounding-box displacement.

### Method C: rPPG amplitude/baseline modulation
Only use if straightforward and demonstrably stable.

## Prototype respiration band
~0.1-0.7 Hz (~6-42 breaths/minute)

This is a prototype engineering range, not a clinical threshold.

## Output
RespirationResult {
    breaths_per_minute: float | null
    confidence: float
    snr: float
    method: string
}

## Independence
The HR engine and RR engine must fail independently.

Examples:
- valid HR + invalid RR is allowed
- invalid HR + valid RR is allowed
- both invalid -> SIGNAL_UNRELIABLE

The reassessment scorer may use whichever signals are valid, but must weight by confidence.

## Testing
At minimum:
- stable seated subject
- deliberate talking
- deliberate head movement
- no face
- torso not visible

Talking/movement should lower RR confidence rather than output an implausibly precise value.
