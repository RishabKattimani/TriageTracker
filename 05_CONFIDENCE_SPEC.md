# Confidence / Abstention Specification

## Confidence inputs
Heart-rate confidence should include:
- rPPG spectral quality / SNR
- cross-ROI agreement
- face tracking stability
- motion score
- illumination quality
- valid-frame ratio

Respiration confidence should include:
- signal periodicity / SNR
- pose/ROI visibility
- motion contamination
- valid-frame ratio

## Required behavior
High confidence:
- accept measurement

Low confidence:
- abstain

Abstention means:
- no baseline update
- no trend update
- no change-score contribution from invalid signal
- no alert from invalid signal

## Recovery
When quality returns:
1. collect a minimum amount of valid data
2. confidence rises
3. measurement resumes
4. UI shows SIGNAL REACQUIRED
5. do not retroactively fill garbage frames

## Required live demo
Still face:
- valid HR expected

Turn head / cover face:
- confidence falls
- "SIGNAL UNRELIABLE"
- "NO INFERENCE"

Return:
- automatic reacquisition
