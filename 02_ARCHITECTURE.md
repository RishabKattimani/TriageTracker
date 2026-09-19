# Architecture

## Stack
- Python 3.11+
- OpenCV
- MediaPipe Tasks Face Landmarker
- MediaPipe Pose Landmarker only if needed for respiration/body motion
- NumPy
- SciPy
- FastAPI
- Uvicorn
- pytest
- HTML/CSS/vanilla JavaScript
- WebSocket for live dashboard telemetry

## Launch and judge-mode architecture

Repository root must contain:
- `run.sh`: executable, idempotent one-command launcher for macOS
- `requirements.txt`: pinned or safely bounded dependencies
- `README.md`: quick start first, then product/technical explanation
- `fixtures/`: permitted demo assets plus metadata

`run.sh` must:
1. find a compatible Python 3.11+ interpreter or explain how to install one;
2. create/reuse `.venv`;
3. install dependencies when needed;
4. verify model and guided-demo fixture availability;
5. start Uvicorn on an available documented localhost port;
6. poll `/health` until ready;
7. open the browser automatically;
8. clean up the server when interrupted;
9. exit nonzero with a concise corrective message on failure.

Do not require Node, Docker, a database, manual model downloads, multiple terminals, or undocumented environment variables.

## High-level pipeline

VideoSource
  -> FaceLandmarkService
  -> ROIExtractor
  -> FrameFeatureExtractor
  -> SignalBuffer
  -> HeartRateEstimator
  -> RespirationEstimator
  -> SignalQualityEstimator
  -> BaselineManager
  -> FeatureBuilder
  -> ChangeScorer
  -> PatientStateMachine
  -> MeasurementStore
  -> FastAPI/WebSocket
  -> Dashboard

EVMRenderer is a parallel visualization path:
VideoSource -> EVMRenderer -> display
It MUST NOT be the numerical source of truth for HR.

## Input abstraction
All inputs MUST implement one shared interface.

VideoSource:
- WebcamVideoSource
- FileVideoSource

Each returns:
FramePacket {
    frame_bgr
    timestamp_ms
    source_id
    frame_index
}

No physiology code may directly depend on cv2.VideoCapture.

## Processing abstraction

FrameProcessor.process(FramePacket) -> FrameObservation

FrameObservation includes:
- face_present
- face_landmarks
- forehead_rgb
- left_cheek_rgb
- right_cheek_rgb
- facial_motion
- illumination
- optional torso_motion_signal
- debug_overlay_frame

## Signal engine
PulseEngine accepts timestamped RGB samples.
RespirationEngine accepts timestamped motion/appearance samples.
Both support rolling windows.

## Dashboard communication
Backend owns current patient state.
Frontend receives snapshots/deltas over WebSocket.

Do not build a SPA framework. Use FastAPI templates/static files + vanilla JS to reduce failure surface.

Required routes/services:
- `/`: explanatory homepage integrated with dashboard entry
- `/demo`: guided prerecorded demonstration
- `/live`: live-camera experience
- `/health`: machine-readable startup health
- startup diagnostics exposed to the UI

The guided demo and live mode must both call the same `VideoSource -> FrameProcessor -> monitoring` chain. Guided UI sequencing may control playback and explanatory overlays only; it may not set backend patient state.

## Multi-patient optimization
Dashboard may show six patient tiles simultaneously.
Only selected/priority feeds need full real-time physiology processing during the demo.
Other tiles may be backed by prerecorded fixture state.

No hardcoded REASSESS status is allowed for the controlled-change feed. Its video must drive the detector.
