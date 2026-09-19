# Eulerian Video Magnification Specification

EVM is REQUIRED for the final demo.

## Purpose
EVM is a visualization layer that makes subtle color/motion variation easier for judges to see.

It is NOT the primary numerical HR estimator.

## Required mode
At minimum implement a color-magnification mode on the facial region.

Pipeline:
1. crop/stabilize face region
2. spatial decomposition / downsample pyramid
3. temporal filtering around selected physiological band
4. amplify filtered variation
5. reconstruct visualization
6. blend/display

## Performance
The EVM display does not need to run at full camera resolution.
Prioritize:
- visible effect
- acceptable latency
- no application crash

## UI
Patient detail screen:
[RAW] [EVM] toggle

When EVM is active:
- display clear "Visualization only" label
- HR is still produced by the rPPG engine

## Fallback
Because EVM is required, if live EVM performance is poor:
- run EVM on a small stabilized crop
- reduce resolution
- reduce frame rate
- use the selected patient only

Do not remove EVM from the demo unless implementation is impossible.
