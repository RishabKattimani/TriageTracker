#!/usr/bin/env python3
"""Manual webcam smoke check for M0. Never fabricates a frame."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.video.webcam import WebcamVideoSource, probe_webcam


def main() -> int:
    report = probe_webcam()
    print(report)
    if not report["available"]:
        print("WEBCAM SMOKE: unavailable (honest). Guided Demo remains the no-camera path.")
        return 2
    source = WebcamVideoSource()
    with source:
        packet = source.read()
        if packet is None:
            print("WEBCAM SMOKE: opened but no frame.")
            return 2
        print(
            f"WEBCAM SMOKE: ok source={packet.source_id} "
            f"shape={packet.frame_bgr.shape} ts={packet.timestamp_ms:.1f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
