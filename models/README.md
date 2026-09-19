# Models

MediaPipe Tasks models are downloaded by `./run.sh` when missing.

Expected files:

- `face_landmarker.task`
- `pose_landmarker_lite.task`

`/health` reports each path as present or missing. The app must not silently invent landmarks.
