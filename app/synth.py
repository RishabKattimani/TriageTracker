"""Synthetic optical fixtures. Pixel oscillation is real; labels are not wearable GT."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


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


def write_pulse_video(
    path: Path,
    *,
    fps: float = 30.0,
    size: tuple[int, int] = (320, 240),
    segments: list[tuple[float, float]],
    motion: bool = False,
    dark: bool = False,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not writer.isOpened():
        raise RuntimeError(f"Could not create video {path}")
    t = 0.0
    dt = 1.0 / fps
    frame_i = 0
    for duration, hz in segments:
        end = t + duration
        while t < end - 1e-9:
            shift = 40 * np.sin(2 * np.pi * 1.7 * t) if motion else 0.0
            frame = draw_face_frame(size[0], size[1], t, hz, motion_px=shift, dark=dark)
            writer.write(frame)
            t += dt
            frame_i += 1
    writer.release()
    return path


def write_sidecar(path: Path, payload: dict) -> Path:
    sidecar = path.with_suffix(".json")
    sidecar.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return sidecar


CONTROLLED_META = {
    "kind": "synthetic_pulse",
    "description": "Synthetic skin-tone patch with optically modulated pulse. Not a clinical recording.",
    "baseline_bpm": 72,
    "changed_bpm": 110,
    "change_at_seconds": 28.0,
    "skin_patch": {"x": 0.22, "y": 0.12, "w": 0.56, "h": 0.70},
}


def generate_repo_fixtures(fixtures_dir: Path) -> dict[str, Path]:
    controlled = fixtures_dir / "controlled_change.mp4"
    stable = fixtures_dir / "stable_seated.mp4"
    no_face = fixtures_dir / "no_face.mp4"
    write_pulse_video(controlled, segments=[(28.0, 1.2), (42.0, 1.833)])
    write_sidecar(controlled, CONTROLLED_META)
    write_pulse_video(stable, segments=[(20.0, 1.2)])
    write_sidecar(
        stable,
        {
            "kind": "synthetic_pulse",
            "description": "Synthetic stable pulse fixture. Not a seated-patient recording.",
            "baseline_bpm": 72,
            "skin_patch": {"x": 0.22, "y": 0.12, "w": 0.56, "h": 0.70},
        },
    )
    write_pulse_video(no_face, segments=[(3.0, 1.2)], dark=True)
    write_sidecar(no_face, {"kind": "no_face", "description": "Dark frames. No face, no pulse."})
    return {"controlled_change": controlled, "stable_seated": stable, "no_face": no_face}
