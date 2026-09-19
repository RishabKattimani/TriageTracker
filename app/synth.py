"""Optical fixtures. Pulse is injected into pixels; labels are not wearable GT."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


PLATE_NAME = "demo_plate.jpg"
REALISTIC_SIZE = (640, 360)


def draw_face_frame(
    width: int,
    height: int,
    t_seconds: float,
    pulse_hz: float,
    *,
    motion_px: float = 0.0,
    dark: bool = False,
) -> np.ndarray:
    frame = np.full((height, width, 3), 30 if dark else 70, dtype=np.uint8)
    if dark:
        return frame
    cx = int(width * 0.5 + motion_px)
    cy = int(height * 0.48)
    face_w, face_h = int(width * 0.34), int(height * 0.52)
    pulse = 0.5 * np.sin(2 * np.pi * pulse_hz * t_seconds)
    skin_b = int(np.clip(145 + 18 * pulse, 0, 255))
    skin_g = int(np.clip(175 + 28 * pulse, 0, 255))
    skin_r = int(np.clip(210 + 16 * pulse, 0, 255))
    cv2.ellipse(frame, (cx, cy), (face_w, face_h), 0, 0, 360, (skin_b, skin_g, skin_r), -1)
    cv2.ellipse(frame, (cx - face_w // 3, cy - face_h // 5), (18, 10), 0, 0, 360, (20, 20, 20), -1)
    cv2.ellipse(frame, (cx + face_w // 3, cy - face_h // 5), (18, 10), 0, 0, 360, (20, 20, 20), -1)
    cv2.ellipse(frame, (cx, cy + face_h // 4), (40, 16), 0, 0, 180, (40, 40, 80), 3)
    return frame


def _skin_mask(plate: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Mask forehead/cheeks so the injected pulse lands on the same ROIs Core reads."""
    height, width = plate.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    fallback = {"x": 0.22, "y": 0.12, "w": 0.56, "h": 0.70}
    try:
        from app.vision.face_landmarks import FaceLandmarkService
        from app.vision.roi import extract_named_rois
    except Exception:
        cv2.ellipse(mask, (width // 2, int(height * 0.48)), (int(width * 0.16), int(height * 0.28)), 0, 0, 360, 255, -1)
        return mask, fallback

    svc = FaceLandmarkService(live=False)
    svc.open()
    landmarks = svc.detect(plate, 1.0)
    svc.close()
    if landmarks is None or len(landmarks) < 100:
        cv2.ellipse(mask, (width // 2, int(height * 0.48)), (int(width * 0.16), int(height * 0.28)), 0, 0, 360, 255, -1)
        return mask, fallback

    rois = extract_named_rois(plate, landmarks)
    for poly, _sample in rois.values():
        if poly is not None:
            cv2.fillConvexPoly(mask, poly.astype(np.int32), 255)
    xs, ys = landmarks[:, 0], landmarks[:, 1]
    x0, y0, x1, y1 = float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())
    cv2.ellipse(
        mask,
        (int((x0 + x1) / 2), int((y0 + y1) / 2)),
        (max(8, int((x1 - x0) * 0.40)), max(8, int((y1 - y0) * 0.46))),
        0,
        0,
        360,
        255,
        -1,
    )
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    return mask, {
        "x": max(0.0, x0 / width - 0.02),
        "y": max(0.0, y0 / height - 0.02),
        "w": min(1.0, (x1 - x0) / width + 0.04),
        "h": min(1.0, (y1 - y0) / height + 0.04),
    }


def _modulate_plate(plate: np.ndarray, mask: np.ndarray, t_seconds: float, pulse_hz: float) -> np.ndarray:
    pulse = 0.5 * np.sin(2 * np.pi * pulse_hz * t_seconds)
    # Same optical amplitude as the old ellipse fixture so POS/CHROM still sees a peak.
    delta = np.array([18.0, 28.0, 16.0], dtype=np.float32) * pulse
    frame = plate.astype(np.float32)
    selected = mask > 0
    frame[selected] = np.clip(frame[selected] + delta, 0.0, 255.0)
    return frame.astype(np.uint8)


def write_pulse_video(
    path: Path,
    *,
    fps: float = 30.0,
    size: tuple[int, int] = (320, 240),
    segments: list[tuple[float, float]],
    motion: bool = False,
    dark: bool = False,
    plate_path: Path | None = None,
) -> dict[str, float] | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plate = None
    mask = None
    skin_patch = None
    if plate_path is not None and Path(plate_path).is_file() and not dark:
        raw = cv2.imread(str(plate_path))
        if raw is not None:
            plate = cv2.resize(raw, size, interpolation=cv2.INTER_AREA)
            mask, skin_patch = _skin_mask(plate)

    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not writer.isOpened():
        raise RuntimeError(f"Could not create video {path}")
    t = 0.0
    dt = 1.0 / fps
    for duration, hz in segments:
        end = t + duration
        while t < end - 1e-9:
            if plate is not None and mask is not None:
                frame = _modulate_plate(plate, mask, t, hz)
            else:
                shift = 40 * np.sin(2 * np.pi * 1.7 * t) if motion else 0.0
                frame = draw_face_frame(size[0], size[1], t, hz, motion_px=shift, dark=dark)
            writer.write(frame)
            t += dt
    writer.release()
    return skin_patch


def write_sidecar(path: Path, payload: dict) -> Path:
    sidecar = path.with_suffix(".json")
    sidecar.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return sidecar


CONTROLLED_META = {
    "kind": "synthetic_pulse",
    "description": "Photorealistic seated-patient plate with injected optical pulse. Not a clinical recording.",
    "baseline_bpm": 72,
    "changed_bpm": 110,
    "change_at_seconds": 28.0,
    "skin_patch": {"x": 0.22, "y": 0.12, "w": 0.56, "h": 0.70},
}


def generate_repo_fixtures(fixtures_dir: Path) -> dict[str, Path]:
    controlled = fixtures_dir / "controlled_change.mp4"
    stable = fixtures_dir / "stable_seated.mp4"
    no_face = fixtures_dir / "no_face.mp4"
    plate = fixtures_dir / PLATE_NAME
    size = REALISTIC_SIZE if plate.is_file() else (320, 240)

    skin = write_pulse_video(controlled, size=size, plate_path=plate, segments=[(28.0, 1.2), (42.0, 1.833)])
    meta = dict(CONTROLLED_META)
    if skin:
        meta["skin_patch"] = skin
        meta["plate"] = PLATE_NAME
    write_sidecar(controlled, meta)

    skin_stable = write_pulse_video(stable, size=size, plate_path=plate, segments=[(20.0, 1.2)])
    stable_meta = {
        "kind": "synthetic_pulse",
        "description": "Photorealistic plate with a stable injected 72 BPM pulse. Not a wearable recording.",
        "baseline_bpm": 72,
        "skin_patch": skin_stable or {"x": 0.22, "y": 0.12, "w": 0.56, "h": 0.70},
    }
    if plate.is_file():
        stable_meta["plate"] = PLATE_NAME
    write_sidecar(stable, stable_meta)

    write_pulse_video(no_face, segments=[(3.0, 1.2)], dark=True)
    write_sidecar(no_face, {"kind": "no_face", "description": "Dark frames. No face, no pulse."})
    return {"controlled_change": controlled, "stable_seated": stable, "no_face": no_face}
