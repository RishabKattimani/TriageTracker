# Heart Rate / rPPG Specification

## Facial ROIs
Use stable skin areas:
- forehead
- left cheek
- right cheek

Derive polygons from MediaPipe facial landmarks.
Exclude:
- eyes
- eyebrows
- mouth
- hairline where possible

Each ROI outputs mean R/G/B per frame.

## Preprocessing
For each ROI:
1. timestamp samples
2. remove invalid frames
3. resample/interpolate to a regular grid if frame timing is uneven
4. detrend
5. normalize channels
6. apply POS and/or CHROM rPPG transform
7. bandpass within a plausible pulse frequency range
8. estimate dominant pulse frequency
9. convert Hz to BPM

Prototype pulse band:
0.7-3.0 Hz (~42-180 BPM)

The band is a prototype engineering range, not a clinical threshold.

## HR estimation
Preferred:
- Welch PSD / FFT peak
- rolling window
- smoothing across consecutive estimates

Return:
HeartRateResult {
    bpm: float | null
    confidence: float
    snr: float
    roi_agreement: float
    method: string
    window_seconds: float
}

## Multi-ROI fusion
Compute HR candidate independently for each valid ROI.
Use:
- spectral quality
- motion quality
- illumination quality
- agreement with other ROIs

Prefer weighted fusion.
If ROIs disagree materially, reduce confidence rather than averaging blindly.

## Prohibition
If confidence is below threshold:
- bpm MUST be null to downstream alert logic
- baseline MUST NOT update
- trends MUST NOT update
- alert MUST NOT trigger

The UI may show "Signal unreliable" but must not show a fake confident BPM.
